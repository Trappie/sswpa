---
name: gen-program-md
description: Generate the ticket program.md from a concert program screenshot. User provides a screenshot of the printed program; this skill transcribes it into program.json and runs the existing ticket_tool formatter to produce program.md. Use when the user asks to convert a program screenshot into the website ticket markdown.
---

Generate `ticket_tool/program.md` from a concert program screenshot the user has provided in this conversation.

## Inputs

The user will paste or attach a screenshot of a printed concert program. It typically lists pieces with composer names, lifespan years, and (sometimes) movements, plus an INTERMISSION marker.

If the user passed a path or arg in $ARGUMENTS, treat it as the screenshot path; otherwise use the most recently shared image in the conversation.

## Steps

0. **Check that a screenshot is actually present.** Before doing anything else, confirm there is an image attached to the current message or earlier in the conversation (or a path in $ARGUMENTS pointing to one). If there is no screenshot, STOP and reply with something like:

   > 你还没发截图哦 — 把音乐会节目单的截图粘贴/拖进来再跑一次 `/gen-program-md` 就行。

   Do not invent or guess program contents. Do not proceed to step 1 without an image.

1. **Transcribe the screenshot** into the JSON schema expected by [ticket_tool/format_ticket.py](../../../ticket_tool/format_ticket.py). Schema:
   ```json
   {
     "items": [
       { "type": "piece", "title": "...", "composer": "...", "years": "YYYY-YYYY", "movements": ["I. ...", "II. ..."] },
       { "type": "intermission" }
     ]
   }
   ```
   - `movements` is optional; omit if the piece has none.
   - Preserve the title's original casing and punctuation (e.g. `"EL PELELE", from Goyescas`). The formatter uppercases the composer automatically, so write composer in lowercase.
   - Order items top-to-bottom as printed.

2. **Sanity-check composer years and name spellings** against general knowledge. If a year or spelling in the screenshot looks wrong (e.g. Granados as 1896-1916 instead of 1867-1916, or "ALBÉNITZ" instead of "ALBÉNIZ"), flag it to the user *before* writing the file and ask whether to correct it. Don't silently change values.

3. **Write** the result to `/Users/diwu/src/marina/sswpa/ticket_tool/program.json` (overwrite).

4. **Run the formatter** from the sswpa directory using its venv:
   ```bash
   cd /Users/diwu/src/marina/sswpa && source venv/bin/activate && python ticket_tool/format_ticket.py
   ```
   Note: the system `python` command is not available; must use venv. Do not try `python3` directly — use the venv.

5. **Show the generated `/Users/diwu/src/marina/sswpa/ticket_tool/program.md`** content to the user so they can copy it to the website.

## Notes

- The formatter wraps each piece as `### **TITLE**` + `#### *COMPOSER* (years)` with movements as plain lines and `---` separators. Don't reimplement this — always run the script.
- If the user previously rejected a typo correction, respect that choice and don't re-flag the same issue.
