---
name: update-heinz-hall
description: Update the website's Heinz Hall Performances page (the season's schedule of Young Artists playing in the Heinz Hall lobby before Pittsburgh Symphony concerts). Used for the yearly full replacement and for mid-season edits such as filling in TBD slots or schedule changes. Input can be a pasted list, email, table, or screenshot. Use when the user asks to update the Heinz Hall roster or schedule.
---

Update the **Heinz Hall Performances** page on the SSWPA website. Edit only the file below; do not touch the other events.

## Background: the site has 4 separate event types

| Event | What it is | Pages |
|---|---|---|
| Artist Recital (ticketed) | Professional pianists | Managed in the admin page `/admin/wm`; not this skill |
| **Heinz Hall** | **Young students play in the Heinz Hall lobby before Pittsburgh Symphony (PSO) concerts; this skill** | `young-artists-heinz-hall.html` |
| Honor Recital | Young students; venue changes by year | skill `update-honor-recital` |
| Audition | Held each spring; decides the Heinz Hall lineup | skill `update-audition` |

**Never edit** the Honor Recital, Audition, or Artist Recital pages when running this skill. `young-artists-about.html`, `programs.html`, `nav.html`, and `footer.html` only mention or link to Heinz Hall (no dates or names) and need no change.

## The one file: `templates/young-artists-heinz-hall.html`

| Part | What it is |
|---|---|
| `<h2>` heading | `Honoring the Best of the Best of our YYYY-YYYY SSWPA Young Artists`. The year is the **season of the performances** (students chosen at the spring 2025 audition perform in 2025-2026). |
| Intro paragraph | Describes how the students were chosen. It does not change from year to year; leave it alone unless the user says otherwise. |
| `.performance-schedule` | A list of `performance-date` blocks, one per PSO concert slot. |

One block:
```html
<div class="performance-date">
    <div class="date-header">October 10, 2025, 6:30pm</div>
    <div class="performers">SOPHIE MA, KARINA COLL, ALEX SHEN</div>
</div>
```

Formatting rules (copy the existing blocks, including indentation and the blank line between blocks):
- Date line: `Month D, YYYY, h:mmpm` (no space before `pm`, no leading zero on the hour).
- Performers: ALL CAPS, separated by commas. Unfilled slots are written `TBD`.
- Siblings or duos: use the exact wording the user gives (the page currently has `EVAN & ETHAN KUANG`, `NANA and LILIA KOLL`, etc.). Do not normalize `&` vs `and` or "fix" name spellings; if something looks inconsistent or like a typo, ask the user.
- Blocks are in chronological order, oldest first.

## Typical schedule (use as a sanity check, not a rule)

Dates come from the PSO concert calendar. The usual pattern is a weekend of three slots: Friday 6:30pm, Saturday 6:30pm, Sunday 1:30pm; sometimes 6:15pm / 1:15pm. Check each date's weekday with `python3 -c "import datetime; print(datetime.date(Y,M,D).strftime('%A'))"` and ask the user about any date that falls outside the usual pattern.

## Two modes

### A. New season (yearly): replace everything
The previous season's blocks are deleted entirely (no archive on the page); the new schedule replaces them.
1. Update the `<h2>` season.
2. Replace all `performance-date` blocks with the new schedule. Some slots may be `TBD`.

### B. Mid-season edit
Only touch the affected blocks (fill in a `TBD`, add or remove a slot, move a date, change a performer). Leave everything else untouched. Past examples: filling `TBD` rosters in September, PSO schedule changes in February.

## Inputs

The user may paste a list, an email, a table, or a screenshot (images can be read directly). Extract, for each slot: date, time, performers. Ask about anything missing or ambiguous (unclear year, unreadable name, a time with no date) before editing.

## Steps

1. Work out the mode (new season or mid-season) and extract the slots. For a new season, also confirm the season for the heading.
2. Show the user the extracted schedule as a plain list (date with weekday, time, performers) and any questions. Wait for a yes before editing.
3. Edit `templates/young-artists-heinz-hall.html`.
4. Verify: the block count matches the source, dates are in chronological order, the heading season is right, and (new season) no old-season dates remain: `grep -n -E "<old year>" templates/young-artists-heinz-hall.html`.
5. Tell the user how to preview: `./run-local.sh` (see CLAUDE.md), then open `/young-artists/heinz-hall`. Do not start the app unprompted.
6. Summarize the diff. Do **not** commit; the user commits themselves.
