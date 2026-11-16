// Roomie web UI – plain JavaScript, no build step.
// Talks to the Roomie API (/api/v2) with the demo API keys from roomie/config.py.

const API = "/api/v2";
const TIMEZONE = "Europe/Berlin";
const DAY_START = 7 * 60; // business hours 07:00-20:00 (see roomie/config.py)
const DAY_END = 20 * 60;

const USERS = [
  { name: "Alice (employee)", key: "rk_live_alice_8f3a" },
  { name: "Bob (employee)", key: "rk_live_bob_2c91" },
  { name: "Fiona (facility admin)", key: "rk_live_fiona_77de", admin: true },
];

const $ = (selector) => document.querySelector(selector);
let rooms = [];

// --- API --------------------------------------------------------------------

function currentUser() {
  return USERS[Number($("#user").value)];
}

async function api(path, options = {}) {
  const response = await fetch(API + path, {
    ...options,
    headers: { "Content-Type": "application/json", "X-Roomie-Key": currentUser().key, ...(options.headers || {}) },
  });
  const text = await response.text();
  let body = null;
  try { body = text ? JSON.parse(text) : null; } catch { /* not JSON, e.g. a 500 */ }
  if (!response.ok) {
    const error = body?.error;
    if (error) throw new Error(`<code>${error.code}</code> ${escapeHtml(error.message)}`);
    const detail = Array.isArray(body?.detail) ? body.detail.map((d) => d.msg).join("; ") : text;
    throw new Error(`<code>HTTP ${response.status}</code> ${escapeHtml(detail || response.statusText)}`);
  }
  return body;
}

// --- Time helpers -------------------------------------------------------------

function escapeHtml(text) {
  return String(text).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
}

function todayInBerlin() {
  return new Intl.DateTimeFormat("en-CA", { timeZone: TIMEZONE }).format(new Date());
}

function addDays(day, days) {
  const date = new Date(day + "T12:00:00Z");
  date.setUTCDate(date.getUTCDate() + days);
  return date.toISOString().slice(0, 10);
}

function weekdayName(day) {
  return new Date(day + "T12:00:00Z").toLocaleDateString("en-GB", { weekday: "long", timeZone: "UTC" });
}

// UTC offset of the office timezone on a given day and time, e.g. "+01:00".
// The API expects timezone-aware timestamps (see docs/api.md).
function berlinOffset(day, time) {
  const date = new Date(`${day}T${time}:00Z`);
  const name = new Intl.DateTimeFormat("en-US", { timeZone: TIMEZONE, timeZoneName: "longOffset" })
    .formatToParts(date).find((part) => part.type === "timeZoneName").value; // "GMT+01:00"
  return name === "GMT" ? "+00:00" : name.slice(3);
}

function toApiTimestamp(day, time) {
  return `${day}T${time}:00${berlinOffset(day, time)}`;
}

// "2026-03-03T07:15:00+01:00" -> minutes since midnight (office time)
function minutesOfDay(timestamp) {
  return Number(timestamp.slice(11, 13)) * 60 + Number(timestamp.slice(14, 16));
}

function formatMinutes(minutes) {
  return `${String(Math.floor(minutes / 60)).padStart(2, "0")}:${String(minutes % 60).padStart(2, "0")}`;
}

function formatRange(start, end) {
  const options = { timeZone: TIMEZONE };
  const date = new Date(start).toLocaleDateString("en-GB", { ...options, weekday: "short", day: "2-digit", month: "short" });
  const time = (value) => new Date(value).toLocaleTimeString("en-GB", { ...options, hour: "2-digit", minute: "2-digit" });
  return `${date}, ${time(start)}–${time(end)}`;
}

// --- Messages -------------------------------------------------------------------

function showMessage(html, type = "success") {
  const box = $("#message");
  box.innerHTML = html;
  box.className = `message ${type}`;
  clearTimeout(showMessage.timer);
  showMessage.timer = setTimeout(() => box.classList.add("hidden"), type === "error" ? 9000 : 4000);
}

async function run(action) {
  try {
    await action();
  } catch (error) {
    showMessage(error.message, "error");
  }
}

// --- Availability timeline --------------------------------------------------

async function loadTimeline() {
  const day = $("#day").value;
  $("#weekday").textContent = weekdayName(day);
  const timeline = $("#timeline");
  const slotsPerRoom = await Promise.all(rooms.map((room) => api(`/rooms/${room.room_id}/availability?day=${day}`)));

  const span = DAY_END - DAY_START;
  const percent = (minutes) => ((minutes - DAY_START) / span) * 100;
  const ticks = [];
  for (let minutes = DAY_START; minutes <= DAY_END; minutes += 60) {
    ticks.push(`<span style="left:${percent(minutes)}%">${formatMinutes(minutes).slice(0, 2)}</span>`);
  }

  timeline.innerHTML = rooms.map((room, index) => {
    const features = [`${room.capacity} seats`, room.has_video && "video", room.has_catering && "catering"].filter(Boolean).join(" · ");
    const free = slotsPerRoom[index].map((slot) => {
      const start = minutesOfDay(slot.start);
      const end = minutesOfDay(slot.end) || DAY_END;
      return `<div class="tl-free" style="left:${percent(start)}%;width:${percent(end) - percent(start)}%"
                   title="${room.name}: free ${formatMinutes(start)}–${formatMinutes(end)}"
                   data-room="${room.room_id}" data-start="${start}" data-end="${end}"></div>`;
    }).join("");
    return `<div class="tl-row">
              <div class="tl-room"><b>${room.room_id} ${escapeHtml(room.name)}</b><span class="muted">${features}</span></div>
              <div class="tl-bar">${free}</div>
            </div>`;
  }).join("") + `<div class="tl-axis"><div></div><div class="tl-ticks">${ticks.join("")}</div></div>`;

  timeline.querySelectorAll(".tl-free").forEach((element) => {
    element.addEventListener("click", () => {
      const start = Number(element.dataset.start);
      const end = Math.min(Number(element.dataset.end), start + 60);
      prefillBooking(element.dataset.room, day, formatMinutes(start), formatMinutes(end));
    });
  });
}

// --- Booking --------------------------------------------------------------------

function prefillBooking(roomId, day, start, end) {
  const form = $("#booking-form");
  form.room_id.value = roomId;
  form.day.value = day;
  form.start.value = start;
  form.end.value = end;
  form.title.focus();
}

async function createBooking(event) {
  event.preventDefault();
  const form = event.target;
  const booking = await api("/bookings", {
    method: "POST",
    body: JSON.stringify({
      room_id: form.room_id.value,
      title: form.title.value,
      start: toApiTimestamp(form.day.value, form.start.value),
      end: toApiTimestamp(form.day.value, form.end.value),
      attendees: Number(form.attendees.value),
    }),
  });
  showMessage(`Booked <b>${escapeHtml(booking.room_id)}</b>: ${escapeHtml(booking.title)} (${formatRange(booking.start, booking.end)})`);
  form.title.value = "";
  await Promise.all([loadTimeline(), loadBookings()]);
}

async function searchRooms(event) {
  event.preventDefault();
  const form = event.target;
  const params = new URLSearchParams({
    start: toApiTimestamp(form.day.value, form.start.value),
    end: toApiTimestamp(form.day.value, form.end.value),
    attendees: form.attendees.value,
    needs_video: form.needs_video.checked,
  });
  const found = await api(`/rooms/search?${params}`);
  const list = $("#search-results");
  if (found.length === 0) {
    list.innerHTML = `<li class="muted">No free room found.</li>`;
    return;
  }
  list.innerHTML = found.map((room) => `
    <li>
      <span><b>${room.room_id} ${escapeHtml(room.name)}</b> <span class="muted">${room.capacity} seats${room.has_video ? " · video" : ""}</span></span>
      <button class="small" data-room="${room.room_id}">Select</button>
    </li>`).join("");
  list.querySelectorAll("button").forEach((button) => {
    button.addEventListener("click", () => {
      prefillBooking(button.dataset.room, form.day.value, form.start.value, form.end.value);
      $("#booking-form").attendees.value = form.attendees.value;
    });
  });
}

// --- My bookings ----------------------------------------------------------------

async function loadBookings() {
  const bookings = await api("/bookings/mine");
  const body = $("#bookings");
  if (bookings.length === 0) {
    body.innerHTML = `<tr><td colspan="6" class="muted">No bookings yet.</td></tr>`;
    return;
  }
  body.innerHTML = bookings.map((booking) => {
    const active = booking.status === "confirmed" || booking.status === "checked_in";
    const actions = [
      booking.status === "confirmed" && `<button class="small" data-action="check-in" data-id="${booking.booking_id}">Check in</button>`,
      active && `<button class="small" data-action="cancel" data-id="${booking.booking_id}">Cancel</button>`,
    ].filter(Boolean).join("");
    return `<tr>
              <td>${booking.room_id}</td>
              <td>${escapeHtml(booking.title)}</td>
              <td>${formatRange(booking.start, booking.end)}</td>
              <td>${booking.attendees}</td>
              <td><span class="status ${booking.status}">${booking.status.replace("_", " ")}</span></td>
              <td class="actions">${actions}</td>
            </tr>`;
  }).join("");
  body.querySelectorAll("button").forEach((button) => {
    button.addEventListener("click", () => run(async () => {
      const booking = await api(`/bookings/${button.dataset.id}/${button.dataset.action}`, { method: "POST" });
      showMessage(`Booking ${escapeHtml(booking.title)}: ${booking.status.replace("_", " ")}`);
      await Promise.all([loadTimeline(), loadBookings()]);
    }));
  });
}

async function releaseNoShows() {
  const released = await api("/bookings/release-no-shows", { method: "POST" });
  showMessage(`Released ${released.length} booking(s) without check-in.`);
  await Promise.all([loadTimeline(), loadBookings()]);
}

// --- Start ----------------------------------------------------------------------

function onUserChanged() {
  document.querySelectorAll(".admin-only").forEach((element) => element.classList.toggle("hidden", !currentUser().admin));
  run(loadBookings);
}

function changeDay(days) {
  $("#day").value = addDays($("#day").value, days);
  run(loadTimeline);
}

async function init() {
  $("#user").innerHTML = USERS.map((user, index) => `<option value="${index}">${user.name}</option>`).join("");
  const today = todayInBerlin();
  $("#day").value = today;
  $("#booking-form").day.value = today;
  $("#search-form").day.value = today;

  $("#user").addEventListener("change", onUserChanged);
  $("#day").addEventListener("change", () => run(loadTimeline));
  $("#prev-day").addEventListener("click", () => changeDay(-1));
  $("#next-day").addEventListener("click", () => changeDay(1));
  $("#booking-form").addEventListener("submit", (event) => run(() => createBooking(event)));
  $("#search-form").addEventListener("submit", (event) => run(() => searchRooms(event)));
  $("#release").addEventListener("click", () => run(releaseNoShows));

  const health = await fetch("/health").then((response) => response.json());
  $("#version").textContent = `v${health.version}`;

  rooms = await api("/rooms");
  $("#room-select").innerHTML = rooms.map((room) => `<option value="${room.room_id}">${room.room_id} ${escapeHtml(room.name)} (${room.capacity} seats)</option>`).join("");
  onUserChanged();
  await loadTimeline();
}

run(init);
