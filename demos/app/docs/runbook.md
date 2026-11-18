# Runbook

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `ROOMIE_RUN_SCHEDULER` | `0` | Set to `1` on exactly one replica to run the no-show job |
| `ROOMIE_DATABASE_URL` | – | PostgreSQL connection string (production only) |
| `ROOMIE_SMTP_HOST` | – | SMTP relay for emails (production only) |
| `ROOMIE_LOG_LEVEL` | `INFO` | Log level of all `roomie.*` loggers |

## Common incidents

### Rooms are released although people are in the meeting

Users must check in on the door display or via `/room checkin` in Slack
within 10 minutes after the start. If the door display of a room is offline,
nobody can check in and the booking gets released.

1. Check the display status in the facility dashboard.
2. If a display is broken, ask the facility team (`#facility-roomie`) to
   replace it.
3. As a workaround a facility admin can create a new booking for the room.

### No-show job runs twice / users get two release emails

The scheduler is enabled on more than one replica. Check the deployment for
`ROOMIE_RUN_SCHEDULER=1` – it must be set on exactly one replica.

### Many `ROOM-401-AUTH` errors

Usually an expired API key of the Slack bot. Rotate the key in the secret
store (`roomie/slack-bot-key`) and restart the bot. Never paste keys into
Slack or tickets.

## Manual operations

Trigger the no-show job manually (facility admin key required):

```bash
curl -X POST -H "X-Roomie-Key: $ADMIN_KEY" https://roomie.internal/api/v2/bookings/release-no-shows
```
