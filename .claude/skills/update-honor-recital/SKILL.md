---
name: update-honor-recital
description: Update the website's Young Artists Honor Recital info (season year, the 4 recital dates, venue, program-submission rule) each year. User pastes the email/notice from Marina with the new dates and venue. Use when the user asks to update honor recital dates, venue, or season on the website.
---

Update the annual **Honor Recital** info on the SSWPA website. Edit only the places listed below; do not touch the other events.

## Background: the site has 4 separate event types

| Event | What it is | Pages |
|---|---|---|
| Artist Recital (ticketed) | Professional pianists, sold tickets | `tickets.html`, `index.html`, `app/database.py`, `ticket_tool/` |
| Heinz Hall | Young students perform outside Pittsburgh Symphony concerts | `young-artists-heinz-hall.html` |
| **Honor Recital** | **Young students; venue changes by year; audience is mostly parents** | **this skill** |
| Audition | Decides the Heinz Hall lineup | `young-artists-audition.html` |

**Never edit** the Heinz Hall, Audition, or Artist Recital pages/files when running this skill, even though their text may mention recitals or contain a year. Pages that only mention "Honors Recitals" generically (`programs.html`, `membership.html`, `support.html`, `footer.html`, `nav.html`) have no dates or venue and need no change.

## Inputs

The user pastes an email/notice from the Artistic Director. Extract:
- Season (e.g. 2026-2027)
- The 4 recital dates (normally all Sundays, same start time)
- Venue name and full street address
- Program-submission deadline (e.g. "10 days before each recital")

If any of these is missing or ambiguous, ask before editing. Verify each date's weekday against a calendar (`python3 -c "import datetime; print(datetime.date(Y,M,D).strftime('%A'))"`) and flag mismatches with the email.

**Email-only details stay off the website.** Logistics meant for performers only (piano model, "first come, first served", how to reply with a preferred date) are communicated by email. Do not add them to the site unless the user asks.

## Places to change

### 1. `templates/young-artists-honors.html` (main page)

- **Heading** `<h2>YYYY-YYYY Honors Recital Dates</h2>`: update the season.
- **Dates**: four `<div class="recital-date"><strong>Sunday, Month D, YYYY</strong></div>` blocks inside `.recital-dates`. Replace the date text; keep exactly one block per recital (add/remove blocks if the count changes).
- **Time and venue** in `.recital-info-card`:
  ```html
  <p><strong>All of these recitals begin at 3:00 PM.</strong></p>
  <p><strong>Venue Name</strong><br>
  Street address, City, STATE ZIP</p>
  ```
  Update the time if it changed. Venue name goes in the bold line, address on the next line. If the venue was renamed, mention the old name in parentheses, e.g. `Beit Kulanu (previously named Rodef Shalom)`.
- **Guidelines list** `.guidelines-card`: the bullet "You should send your program information via Email N days prior to the recital date to: ..." must match the deadline in the email (e.g. "10 days"). The rest of the bullets (10 minute limit, memorized, program-note format, dress code) change only if the email says so. The contact email is `marinaschmidt@comcast.net`.

### 2. `templates/young-artists-about.html` ("Young Artists Honors Recitals" section)

One paragraph: `Open to all SSWPA Young Artists, the YYYY-YY Honors Recitals will take place at <venue>. ...`. Update the season (short form, e.g. `2026-27`) and the venue (name only; the full address lives on the honors page). Leave the rest of the paragraph alone unless the email changes it.

## Steps

1. Confirm the extracted info with the user (season, 4 dates with weekdays, venue + address, deadline). Wait for a yes before editing.
2. Edit the two files above.
3. `grep -rn -E "<old season>|<old venue>" templates/` to confirm no stale honor-recital references remain. Hits on Heinz Hall / Audition / Artist Recital pages are expected and must be left alone.
4. Tell the user how to preview locally and let them run it themselves; do not start it unprompted. The script that works (verified Oct 2026) is `./run-local.sh` (builds the Docker image and starts container `sswpa-local` on http://localhost:8000; stop it with `./stop-local.sh`). Pages to check: `/young-artists/honors` and `/young-artists/about`.5. Summarize the diff for the user. Do **not** commit; the user commits themselves.
