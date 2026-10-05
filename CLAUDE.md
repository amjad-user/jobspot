# JobSpot — project guide for Claude

## Vision
JobSpot is a simple, friendly job search app for **non-technical people**.
You type a job ("Barista", "part-time job in a café"), pick a place ("Berlin"),
and see real job listings. "View & apply" opens the original job posting in a
new tab — the person applies there themselves. JobSpot never applies for them.

- Feels like a real app: clean, modern, friendly. **No technical words on screen**
  (no "API", "endpoint", "JSON", error codes).
- Search bar "What job are you looking for?" + "Where?" field.
- Filters in a row under the search bar: distance (10/25/50/100 km),
  job type (part-time / full-time), date posted.
- Job cards: title, company, location, type, date posted, "View & apply", "Save".
- Saved jobs page: track progress — Saved → Applied → Got a reply / Interview / Rejected.
- Simple stats (saved, applied, replies, interviews).
- Friendly empty and loading messages.
- Works on laptop and phone-sized windows. Dark mode.
- Name: **JobSpot**. Style: **bold & modern** (near-black + lime accent).
- UI language: English now, German switch later.

## Approved design (rebuild this in task 7)
The clickable prototype was approved. Rebuild it in plain HTML/CSS/JS with these details:
- **Colors (light):** background `#F4F4EE`, cards `#FFFFFF`, input fields `#F4F4EE`,
  text `#141412`, muted text `#5A5A52`, borders `#DEDED5`. **Accent (lime):** `#C8F53B`
  with dark text `#141412` on it.
- **Colors (dark):** background `#0F100D`, cards `#1A1B17`, fields `#24251F`,
  text `#F3F3ED`, muted `#A9A99F`, borders `#30312A`. Dark mode follows the computer
  setting, with a moon/sun button in the header to switch.
- **Fonts (Google Fonts):** headings "Bricolage Grotesque" (700–800, tight letter spacing),
  body "Figtree" (400–800).
- **Look:** bold & modern. Big rounded corners (cards 18px, search box 22px),
  2px dark outlines on main buttons, the search box has a hard offset shadow (6px 6px 0, text color).
- **Header:** logo (lime square with pin icon + "JobSpot"), nav pills "Find jobs" and
  "Saved jobs" (with a lime count badge), dark mode button.
- **Home:** small pill "Real jobs near you. You apply directly.", huge headline
  "Find your next job, close to home.", search box (two fields: "What job are you looking for?"
  and "Where?" + lime "Search jobs" button), filter row (Distance 10/25/50/100 km, default 25;
  Job type Any/Part-time/Full-time; Posted Any time/24h/7 days/30 days; "Clear filters" link),
  "Popular" suggestion chips, and 3 "how it works" cards (Search, Save, Apply & track).
- **Results:** title "N jobs near Berlin", subtitle "Within 25 km · newest first", grid of cards
  (initials logo square, title, company, location · km, type, posted "Today/Yesterday/N days ago",
  lime "View & apply" button opening a new tab, "Save"/"Saved" toggle button).
- **Loading:** "Loading jobs…" with pulsing skeleton cards.
- **No results:** "No jobs found" + tip "Try a wider radius, fewer filters…" + "Widen my search" button.
- **Saved jobs page:** title, 4 stat boxes (Saved, Applied, Replies, Interviews), each saved job
  as a card with a status badge, status buttons (Saved, Applied, Got a reply, Interview, Rejected),
  "View & apply" and "Remove". Empty state "No saved jobs yet" + "Find jobs" button.
- **Footer:** "Your saved jobs stay on this computer only." / "You always apply on the employer's own page."
- Works at phone width (everything stacks), buttons at least 44px tall.

## Job source details (Bundesagentur Jobsuche) — tested by hand 2026-10-05
- Base: `https://rest.arbeitsagentur.de/jobboerse/jobsuche-service`
- Search: **`GET /pc/v6/jobs`**, header `X-API-Key: jobboerse-jobsuche`.
  (`/pc/v4/jobs` now returns **403 Forbidden** — do not use it.)
- Params (all confirmed working): `was` (what), `wo` (where), `umkreis` (km),
  `arbeitszeit` (`vz` full-time, `tz` part-time), `veroeffentlichtseit` (days, 0–100),
  `page` (starts at 1), `size`.
- Answer (v6): `maxErgebnisse` (total), `page`, `size`, `woOutput.bereinigterOrt` (cleaned place
  name), `facetten` (filter counts, not needed), and **`ergebnisliste`** (the job list).
  - **When there are 0 results, `ergebnisliste` is missing completely** → treat missing as empty list.
- Each job in `ergebnisliste` (v6 names — different from v4!):
  - `stellenangebotsTitel` (title), `firma` (company — may be missing), `referenznummer` (id),
  - `stellenlokationen[0].adresse` → `ort`, `plz`, `region` (location; is a list),
  - `entfernung` (distance in km from the searched place),
  - `datumErsteVeroeffentlichung` / `veroeffentlichungszeitraum.von` (date posted, `YYYY-MM-DD`),
  - `arbeitszeitVollzeit` (true/false), `arbeitszeitTeilzeit*` (several true/false fields),
  - sometimes `externeURL` (note the capital **URL**).
- Job page link: `https://www.arbeitsagentur.de/jobsuche/jobdetail/{referenznummer}`
  (confirmed working), or `externeURL` if present.
- Notes: answers contain German letters (ä, ö, ü, ß) — read as UTF-8. PowerShell 5.1 shows them
  wrong and its JSON reader can fail on `facetten` (duplicate company names); Python is fine.

## Install & privacy rules
- Download from GitHub → double-click **one start file** → app opens in the browser.
- A Claude Code user can say "set this up and run it for me" and it works.
- Windows first (PowerShell), Mac later. Maybe a desktop app with an icon later.
- Runs **locally only**. Saved jobs never leave the user's computer.
- No personal data in the repo. Keys go in `.env` (never committed).

## Job sources
- Only use sources that allow access. **No scraping** of LinkedIn, Indeed etc.
- First candidate: Bundesagentur für Arbeit Jobsuche (community docs:
  github.com/bundesAPI/jobsuche-api). Research properly before deciding.
- Other sources can be added later.

## How to work with Amjad
- Amjad: first-year CS student. Knows Python, HTML, CSS. **No JavaScript/React yet.**
  Windows, PowerShell, VS Code. Not a native English speaker.
- Portfolio project for SWE internships → he must be able to explain it in interviews.
- Plain English. Avoid jargon, or explain it when used.
- Professional but simple: clean folders, tests, `.gitignore`, `.env`, error handling,
  good README with screenshots, one-click start file.
- Beginner-friendly code: plain if/else, no clever one-liners, clear names, short comments.

### BUILD MODE (since 2026-10-05)
- Build all of Step 3 (tasks 1–9) in order until JobSpot fully works.
- **No check questions and no explanations while building.**
- Only ask Amjad when a real decision is needed or something is blocked
  (job service down, something missing on the laptop). Small decisions: pick the
  sensible option, write it under "Decisions made while building", keep going.
- Run the tests after each task; fix failures before moving on. Tick the checklist.
- **Git (updated 2026-10-05):** Claude makes **one commit per task** at the end of each
  task, with a Conventional Commits message and the `Co-Authored-By: Claude` line.
  After each commit, show Amjad the exact git commands that were run, so he learns them.
  Then continue with the next task without waiting.
- **Never run `git push`.** Amjad pushes to GitHub himself after checking the work.
- When everything is built:
  1. Run the app and check search, filters, save, status changes and stats.
  2. Teach Amjad the code **in the order it runs**: double-click `start.bat` → one search
     (browser → `app.js` → FastAPI route → JobSource → Bundesagentur → back to screen) →
     saving a job into SQLite. Explain JavaScript slowly. When code calls a function in
     another file, jump into it, explain it, then come back.
  3. Then ask 5 interview-style questions about the project.

### Decisions made while building
- Job source uses `/pc/v6/jobs` (v4 returns 403).
- Folders: `backend/` (Python server; `sources/` = job sources), `frontend/` (HTML/CSS/JS),
  `tests/` (`fake_answers/` = saved fake job-service answers), `data/` (SQLite file, ignored by git).
- Two requirement files: `requirements.txt` (app only, used by `start.bat`) and
  `requirements-dev.txt` (adds pytest). Versions are pinned.
- Settings come from `.env` via python-dotenv in `backend/config.py`; every setting has a
  default, so the app works without `.env`. Server runs on `127.0.0.1` only (local-only).
- pytest hides a Starlette warning about its own test client (not our code).
- `Job` shape (backend/models.py): `id` = "jobsuche:{referenznummer}", `source`, `title`,
  `company` ("" if missing), `location` (town of first work place), `distance_km`,
  `job_type` (full_time / part_time / full_or_part_time / not_stated), `posted_date`, `url`.
- Posted date = `veroeffentlichungszeitraum.von` (latest publication), fallback
  `datumErsteVeroeffentlichung`.
- Link: `externeURL` if it starts with http(s) (safety), else the arbeitsagentur.de job page.
- 24 jobs per page. The service has no "sort by date" option, so each page is sorted
  newest first by us. Listings without id or title are skipped.
- Errors: `JobSourceUnavailable` (no internet, timeout, non-200) and `PlaceNotFound`
  (service says `suchmodus: UNGUELTIG`). Tests use `httpx.MockTransport` (tests/fakes.py).
- Fake answers in tests use made-up company names (no real company data in the repo).

## Progress checklist
### Step 1 — Design first
- [x] Ask design questions (style, name, language, filter placement)
- [x] Build clickable prototype with fake jobs (search, filters, results, saved jobs, dark mode)
- [x] Design approved (2026-10-05). Amjad: the backend is the most important part.

### Step 2 — Plan
- [x] Research job sources (Bundesagentur Jobsuche = main source; Adzuna / Arbeitnow = later)
- [x] Propose tech stack, architecture, folder structure
- [x] Amjad approves the plan (2026-10-05)

### Approved plan
- Backend: Python + FastAPI, httpx (calls job source), Pydantic (data shapes),
  SQLite (saved jobs, local file), pytest (tests, with fake job-source answers).
- Frontend: the approved design as plain HTML + CSS + small plain JavaScript, served by FastAPI.
- Flow: browser → our local server (localhost) → Bundesagentur Jobsuche → our server
  turns the answer into our own simple `Job` shape → browser.
- Job sources sit behind one `JobSource` interface, so new sources plug in later.
- Start file: `start.bat` (makes venv, installs, starts server, opens browser).

### Step 3 — Build
- [x] 1. Test the Jobsuche service by hand on Amjad's laptop (one request) — done 2026-10-05:
      v4 blocked (403), **v6 works**; field names updated in "Job source details" above.
- [x] 2. Project setup: folders, venv, `requirements.txt`, `.gitignore`, `.env.example`, README skeleton
- [x] 3. `Job` model + Jobsuche client that turns the answer into `Job` objects (+ tests)
- [ ] 4. `GET /api/jobs` search route with filters + friendly errors (+ tests)
- [ ] 5. SQLite saved-jobs storage (+ tests)
- [ ] 6. Saved jobs routes: list, save, change status, remove, stats (+ tests)
- [ ] 7. Frontend: turn the design into HTML/CSS, then connect it with JavaScript
- [ ] 8. `start.bat` one-click start + first-run checks
- [ ] 9. README with screenshots, final clean-up
- [ ] Later: German language switch, more job sources, Mac start file, desktop app
