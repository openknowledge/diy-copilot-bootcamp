"""Builds evaluation_dataset.csv from the knowledge base.

The line ranges of the ground truth are resolved from anchor texts, so the
dataset stays correct when the documents change. Run from the repository root:

    python data/evaluation/build_evaluation_dataset.py data/knowledge_base data/evaluation/evaluation_dataset.csv
"""
import csv
import sys
from pathlib import Path

KB = Path(sys.argv[1]); OUT = Path(sys.argv[2])

def lines_of(file, start, end=None):
    lines = (KB / file).read_text(encoding="utf-8").splitlines()
    def find(anchor, after=0):
        for i in range(after, len(lines)):
            if anchor in lines[i]: return i + 1
        raise ValueError(f"{anchor!r} not found in {file}")
    s = find(start); e = find(end, s - 1) if end else s
    return f"{file}:{s}-{e}"

P = "domain/room-booking-policy.md"; R = "domain/meeting-rooms-berlin.md"; D = "domain/desk-sharing-policy.md"
G = "domain/glossary.md"; EV = "domain/event-spaces-policy.md"; ACC = "security/access-and-password-policy.md"; IR = "security/security-incident-response.md"; PY = "engineering/python-coding-guidelines.md"; API = "engineering/api-design-guidelines.md"
T = "engineering/testing-guidelines.md"; GIT = "engineering/git-and-code-review.md"
S = "security/secrets-and-logging.md"; DP = "security/data-protection.md"; AI = "security/ai-assistant-usage-policy.md"

items = [
 ("What is the maximum duration of a single meeting room booking in Berlin?", "4 hours (240 minutes); longer workshops are booked by the facility team as several bookings.",
  [(P, "### 2.2 Duration", "please send a request")]),
 ("Can I book a meeting room in Berlin from 10:10 to 10:50?", "No, bookings must start and end on a full quarter hour, e.g. 10:00 to 11:00.",
  [(P, "### 2.1 Time grid", "11:00 instead")]),
 ("Can meeting rooms in the Berlin office be booked on Saturdays?", "No, only Monday to Friday 07:00-20:00; for weekend events contact the facility team.",
  [(P, "### 2.3 Business hours", "weekends; for weekend events")]),
 ("How far in advance can I book a meeting room in Berlin?", "At most 60 days.",
  [(P, "### 2.4 Booking in advance", "future are not possible")]),
 ("Why am I not allowed to book the Tempelhof room for a 1:1 customer call?", "Big room policy: rooms with 12+ seats need at least 4 attendees; use A1-01 or A1-02 which have the same video system.",
  [(P, "### 3.2 Big room policy", "small rooms A1-01"), (G, "**Big room**")]),
 ("How long after a meeting with catering can the next booking start?", "15 minutes later at the earliest because of the cleaning buffer.",
  [(P, "### 3.3 Rooms with catering", "at the earliest"), (G, "**Cleaning buffer**")]),
 ("How do I order catering for a meeting in a Berlin meeting room?", "Via the catering form in the intranet, at least 2 working days in advance; the booking system does not order catering.",
  [(R, "## Catering", "intranet. The booking system")]),
 ("When do I have to check in to my meeting room booking in Berlin?", "From 5 minutes before until 10 minutes after the start, at the door display or with /room checkin.",
  [(P, "### 4.1 Check-in", "`/room checkin`"), (G, "**Check-in**")]),
 ("What happens in Berlin if nobody checks in to a meeting room booking?", "The booking is released automatically 10 minutes after the start; the owner gets an email and the facility team is informed.",
  [(P, "### 4.2 Automatic release", "book the room again if it is still")]),
 ("Until when can I cancel my desk booking?", "Until 10:00 on the same day.",
  [(D, "## Cancellation", "cancellations are counted")]),
 ("I need to cancel a Berlin meeting room booking that starts in one hour. What can I do?", "Own cancellations are only possible until 2 hours before; contact the facility team via #facility-roomie.",
  [(P, "## 5. Cancellation", "via `#facility-roomie` in Slack")]),
 ("What does the room id B2-14 mean?", "Room number 14 on floor 2 of building B.",
  [(R, "## Room names and ids", "floor 2 of building B")]),
 ("Which meeting room has an induction loop for hearing aids?", "A2-10 (Tempelhof).",
  [(R, "## Accessibility", "induction loop")]),
 ("Where should business rules like durations and limits be defined in our Python services?", "Once in a central configuration module (config.py) and imported from there (PY-03).",
  [(PY, "**PY-03", "the configuration instead")]),
 ("How should I get the current time in business logic?", "Inject a clock instead of calling datetime.now(); all datetimes must be timezone-aware (PY-05).",
  [(PY, "**PY-05", "naive datetimes are a bug"), (T, "## TEST-03", "is a bug in the test")]),
 ("May I raise HTTPException in a service class?", "No, business logic raises domain exceptions; conversion to HTTP happens in a central handler (PY-06).",
  [(PY, "**PY-06", "central exception handler")]),
 ("Which HTTP header do our internal services use for API keys and why not the Authorization header?", "X-<Service>-Key (e.g. X-Roomie-Key); the corporate reverse proxy strips the Authorization header.",
  [(API, "## API-04", "support our SSO")]),
 ("What does an error response of our APIs look like?", "{\"error\": {\"code\": \"<SERVICE>-<status>-<REASON>\", \"message\": ...}}",
  [(API, "## API-05", "Add a new code instead")]),
 ("Should a booking that was cancelled be deleted with a DELETE endpoint?", "No, resources kept for statistics are soft-deleted; use POST /{id}/cancel instead of DELETE.",
  [(API, "## API-03", "action endpoint instead")]),
 ("Which status code should an API return if a request violates a business rule?", "422 (never 500).",
  [(API, "## API-06", "A 500 is always a bug")]),
 ("How must timestamps be formatted in our APIs?", "ISO 8601 with timezone offset; timestamps without offset are rejected with 422; stored and returned in UTC.",
  [(API, "## API-07", "Responses return UTC")]),
 ("What do tests for API error cases have to check?", "The error code in the response body, not only the HTTP status (TEST-04).",
  [(T, "## TEST-04", "the right rule was")]),
 ("What test coverage is required for new code?", "At least 80% line coverage (TEST-06).",
  [(T, "## TEST-06", "maximum duration")]),
 ("How do I name a branch for a bug fix?", "fix/<ticket>-short-name, e.g. fix/WORK-412-naive-datetimes.",
  [(GIT, "## GIT-01", "Team Workplace")]),
 ("Who has to approve a merge request that changes the maximum booking duration in config.py?", "One team member plus the product owner of the business department (facility management).",
  [(GIT, "## GIT-04", "security champion")]),
 ("Is it okay to commit an API key in a test file?", "No, secrets must never be committed; only clearly marked local demo keys are allowed (SEC-01).",
  [(S, "## SEC-01", "deployed environment")]),
 ("I accidentally pushed a password to the repository. What do I have to do?", "Treat it as compromised: rotate it immediately and inform #security; removing the commit is not enough.",
  [(S, "## SEC-02", "inform `#security`")]),
 ("May I log the meeting title when a booking is created?", "No, personal data like meeting titles must not be logged; log the user id and a request id.",
  [(S, "## SEC-04", "request id"), (DP, "## DP-01", "check-ins")]),
 ("How long may booking data including the owner be stored?", "12 months, then it has to be anonymised.",
  [(DP, "## DP-03", "if they are anonymised")]),
 ("Can we build a report showing which employees cause the most no-shows?", "No, evaluations of individual persons need the approval of the works council; team-level evaluations are allowed.",
  [(DP, "## DP-04", "rate is allowed")]),
 ("Can I paste production logs into an AI assistant to debug a problem?", "No, logs with user ids or other personal data and secrets must not be shared with AI assistants.",
  [(AI, "## AI-02", "approved tools"), (DP, "## DP-06", "AI assistant usage policy")]),
 ("Are AI agents allowed to push code or deploy on their own?", "No, agents only work in a sandbox or feature branch without production credentials, and a human approves every change.",
  [(AI, "## AI-05", "production APIs on their own")]),
]

# Hard questions: phrased like real developer questions - informal, as a scenario,
# without the vocabulary of the documents, or easy to confuse with a similar document
# (meeting rooms vs. desks). They are needed to see the effect of retrieval optimizations.
hard_items = [
 ("My team lead wants a dashboard that ranks colleagues by how often they skip meetings they booked. Can I build that?",
  "Not without the approval of the works council; evaluations of individual persons are not allowed, team-level evaluations are.",
  [(DP, "## DP-04", "rate is allowed")]),
 ("I reserved a spot in the open space for tomorrow but now I'll work from home. Until when can I drop it without it counting against me?",
  "Desk bookings can be cancelled until 10:00 on the same day; later cancellations count as a no-show.",
  [(D, "## Cancellation", "cancellations are counted")]),
 ("I came to the office at 10:45 and someone else was sitting at the desk I had reserved. Is that allowed?",
  "Yes, desks not checked in by 10:30 are released and can be booked by others.",
  [(D, "## Check-in", "booked by others")]),
 ("Where do I put my laptop and jacket overnight if I don't have a fixed desk?",
  "Into the permanently assigned lockers on each floor; desks must be left empty.",
  [(D, "## Clean desk", "cannot be booked")]),
 ("A reviewer complained that my endpoint crashes with a 500 when the end date is before the start date. What should it return instead?",
  "422 - a business rule violation must never be answered with 500.",
  [(API, "## API-06", "A 500 is always a bug")]),
 ("The firmware of our door displays can't get a bearer token through to the service. How are these devices supposed to authenticate?",
  "With an API key in the custom header X-<Service>-Key (e.g. X-Roomie-Key).",
  [(API, "## API-04", "support our SSO")]),
 ("Is it okay to just write 15 directly into the overlap check for the cleaning time?",
  "No, business rules like the cleaning buffer must be defined once in config.py and imported (PY-03).",
  [(PY, "**PY-03", "the configuration instead")]),
 ("My unit test passes in the morning but fails every evening after 8 pm. What did I do wrong?",
  "The test depends on the real current time; inject a fake clock and advance it explicitly (TEST-03, PY-05).",
  [(T, "## TEST-03", "is a bug in the test"), (PY, "**PY-05", "naive datetimes are a bug")]),
 ("Someone pasted our staging token into a public Slack channel. Is it enough to delete the message?",
  "No, the secret is compromised: rotate it immediately and inform #security; secrets must never be shared via Slack.",
  [(S, "## SEC-02", "inform `#security`"), (S, "## SEC-06", "one-time link")]),
 ("Can I use Copilot with my private GitHub account for work on our services?",
  "No, only tools approved by Information Security may be used; private accounts are not allowed for company work.",
  [(AI, "## AI-01", "Using private accounts of AI tools")]),
 ("An agent opened a pull request and wants to merge it itself once CI is green. Is that fine?",
  "No, a human must approve every change; agents must not push, merge or deploy on their own.",
  [(AI, "## AI-05", "production APIs on their own")]),
 ("How long can I look up application logs when I investigate an incident?",
  "30 days.",
  [(S, "## SEC-05", "central log platform"), (DP, "## DP-03", "if they are anonymised")]),
 ("We're planning a full-day hackathon in the big room. How do we get it for the whole day?",
  "Bookings are limited to 4 hours; the facility team books full days as several consecutive bookings - request at least one week in advance.",
  [(P, "### 2.2 Duration", "please send a request")]),
 ("A partner from another company wants to reserve a room for our joint meeting. How does that work?",
  "Guests cannot book rooms themselves; their host books the room for them.",
  [(P, "## 1. Who can book", "book rooms themselves")]),
 ("About a third of our team's room bookings never take place. Will anyone notice?",
  "Yes, teams with a no-show rate above 25% are contacted by facility management.",
  [(P, "## 6. Misuse", "contacted by facility management")]),
 ("Is test_cancel_2 a good name for my new test?",
  "No, test names describe the expected behaviour, e.g. test_late_cancellation_only_for_admins.",
  [(T, "## TEST-02", "like `test_cancel_2`")]),
 ("I want to fix the 500 error for timestamps without timezone. What should be the first thing in my merge request?",
  "A test that reproduces the bug and references the ticket (TEST-07).",
  [(T, "## TEST-07", "docstring")]),
 ("Do we have to delete booking records after a year?",
  "No, they have to be anonymised after 12 months; deleting is not required if they are anonymised.",
  [(DP, "## DP-03", "if they are anonymised")]),
 ("I want to store the names of everyone invited to a meeting together with the booking. Any concerns?",
  "Yes, data minimisation: a booking system needs the owner and the number of attendees, not their names.",
  [(DP, "## DP-02", "names of the attendees")]),
 ("Should I write 'Wannsee' or something else when I mention the room in a Jira ticket?",
  "Use the room id (B2-14), names can change.",
  [(R, "## Room names and ids", "names can change")]),
 ("I booked a Berlin meeting room for 14:00. Until when do I have to confirm that the meeting actually takes place?",
  "Check in until 14:10 (10 minutes after the start), earliest from 13:55.",
  [(P, "### 4.1 Check-in", "`/room checkin`")]),
 ("Is a 3.5-hour workshop booking in one of our Berlin meeting rooms still allowed?",
  "Yes, bookings in Berlin can last up to 4 hours.",
  [(P, "### 2.2 Duration", "please send a request")]),
 ("Can I still cancel my Berlin room booking myself 90 minutes before the meeting?",
  "No, own cancellations are only possible until 2 hours before the start; contact the facility team.",
  [(P, "## 5. Cancellation", "via `#facility-roomie` in Slack")]),
 ("Our new API should use Authorization: Bearer tokens like the API guidelines say, right?",
  "No, the current guidelines (API-04) require an API key in X-<Service>-Key; Bearer was only allowed in the superseded version 3.",
  [(API, "## API-04", "support our SSO")]),
 ("Should my endpoint answer with 400 Bad Request when a booking violates a business rule?",
  "No, business rule violations return 422 (API-06).",
  [(API, "## API-06", "A 500 is always a bug")]),
 ("If a client sends a timestamp without an offset, can the server just assume Berlin time?",
  "No, timestamps without offset are rejected with 422 (API-07).",
  [(API, "## API-07", "Responses return UTC")]),
 ("We want to celebrate our release with 40 people and pizza in the office. Which room do we book in Roomie?",
  "None - this is an event: event spaces are requested via the event request form at least 4 weeks in advance, not in Roomie.",
  [(EV, "## 1. What counts as an event", "3 working days")]),
 ("How often do I have to change the password of my company account?",
  "Not periodically - only if there is a suspicion that someone else knows it.",
  [(ACC, "## ACC-02", "private services")]),
 ("I need access to the production database to debug WORK-412. How do I get it?",
  "Request temporary production access (max. 8 hours) via the access portal, justified with a ticket.",
  [(ACC, "## ACC-04", "ticket.")]),
 ("My laptop was stolen on the train, and it had a local .env file with API keys. What do I do?",
  "Call the security hotline immediately (remote lock and wipe), report it to the police, and treat the keys as compromised: rotate them.",
  [(IR, "## IR-02", "from another device"), (S, "## SEC-02", "inform `#security`")]),
]


with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f, quoting=csv.QUOTE_ALL)
    w.writerow(["question", "ground_truth_origin", "ground_truth_answer", "difficulty"])
    for difficulty, group in (("easy", items), ("hard", hard_items)):
        for q, a, refs in group:
            w.writerow([q, ";".join(lines_of(*r) for r in refs), a, difficulty])
print(len(items), "easy and", len(hard_items), "hard items written")
