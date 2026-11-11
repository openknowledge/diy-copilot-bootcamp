# Data Protection Requirements for Internal Applications

- Owner: Data Protection Officer (DPO)
- Applies to: all internal applications that process personal data of employees
- Version: 2.2

## DP-01 – What is personal data

Personal data is any information relating to an identifiable person. In
internal tools this includes user ids, names, email addresses, calendar
entries, **meeting titles** (they often contain names or topics like
"Performance review with Anna") and usage data such as bookings or check-ins.

## DP-02 – Data minimisation

Only collect data that is needed for the purpose of the application. For
example, a room booking system needs the owner and the number of attendees,
but not the names of the attendees.

## DP-03 – Retention periods

| Data | Retention |
|---|---|
| Bookings, cancellations, check-ins (incl. title and owner) | 12 months, then anonymised |
| Aggregated statistics (no personal reference) | unlimited |
| Application logs | 30 days |
| Backups | 35 days |

Anonymisation means: remove the owner and replace the title with a generic
text. The record itself can be kept for statistics. Deleting records is not
required if they are anonymised.

## DP-04 – Statistics and evaluations

Usage data may be evaluated for capacity planning at the level of rooms,
floors and teams. Evaluations of **individual persons** (e.g. "who causes
the most no-shows") are not allowed without the approval of the works
council. Contacting teams with a high no-show rate is allowed.

## DP-05 – Access

Only the owner and administrators with a business need (e.g. facility admins)
may see the details of a booking. Other users must not even learn that a
booking with a given id exists – APIs answer with 404 in this case.

## DP-06 – External services and AI

Personal data of employees must not be sent to external services without a
data processing agreement. This includes AI services: do not paste booking
data, logs with user ids or meeting titles into public AI tools. See the
[AI assistant usage policy](ai-assistant-usage-policy.md).

## DP-07 – Records of processing

Every application that processes personal data must be registered in the
records of processing activities before it goes live. Contact the DPO at
privacy@example.com.
