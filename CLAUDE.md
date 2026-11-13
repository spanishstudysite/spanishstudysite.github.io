# CLAUDE.md

Notes for Claude (and any developer) working in this repo. Read this before changing anything.

## What this is
**Loro** is a Spanish practice site for high school students and their teachers. Students practice vocabulary and verb conjugations by typing. Teachers make classes, send assignments with goals, and see results and weak spots. See `PRD.md` for the full product picture and `README.md` for the overview.

- Live site: https://spanishstudysite.github.io/
- Repo: https://github.com/spanishstudysite/spanishstudysite.github.io

## Standing rules
1. **Every new feature or fix ships with a new test** in `tests/tests.html`. Prove the test can fail (break the feature in a throwaway copy, see it go red), then confirm the full suite is green.
2. **No student personal info, ever.** Students sign up with an animal username (animal + class tag, e.g. `koalaab3`) and a 4-digit PIN. Never add fields that collect real names, emails, birthdays, or photos for students. Never put example student names on screens.
3. **No secrets in the repo.** The repo is public. Never commit the teacher code, database passwords, the Supabase service key, or the checks passcode. Only the public Supabase anon key and the checks passcode's SHA-256 hash belong in `site/index.html`.
4. **Don't change the name, logo, or look without asking the owner first.**
5. Keep copy plain and friendly. Students are teenagers, and teachers are busy.

## How it's built
- **One file:** `site/index.html` holds all the HTML, CSS, and JavaScript, plus the built-in vocab sets and verb data (about 1.9 MB). There's no framework, no bundler, and no npm dependencies for the site.
- **Code style:** ES5-style JavaScript (`var`, `function`, no arrow functions or classes in site code), with short helper names: `$(id)` gets an element, and `rp(fn, args)` calls a Supabase RPC. Match the surrounding style and keep it compact.
- **Hosting:** GitHub Pages publishes only `site/` via `.github/workflows/pages.yml`. Every push to `main` goes live in about a minute. Check deploys with `gh run list -R spanishstudysite/spanishstudysite.github.io`.
- **Keep-awake ping:** `.github/workflows/keep-awake.yml` pings the database every Monday and Thursday so the free Supabase project never pauses. It reads the address and public key from `site/index.html` (`var SBU="…",KEY="…"`), so keep that line in that shape. If a ping fails, GitHub emails the owner. `database/check-size.sql` shows how full the database is (free plan: 500 MB).
- **Owner tools:** `pages.yml` runs all checks before publishing (a failure blocks the deploy). `backup.yml` makes a weekly encrypted `pg_dump` (secrets `DATABASE_URL`, `BACKUP_PASSPHRASE`). `error-check.yml` reads the private error log daily with secret `OWNER_TOKEN` via `owner_errors`, and fails on purpose when there are errors so GitHub emails the owner. The site sends errors with `reportErr` → `log_error`, scrubbing the username and PIN, at most 5 per page. Setup steps are in `BACKUPS.md`.
- **Old host:** the old Netlify copy has been deleted. GitHub Pages is the only host.
- **Database:** Supabase (PostgreSQL). The browser never reads tables directly. It only calls `security definer` SQL functions that check a student's username and PIN, or a teacher's login, first. PINs are bcrypt hashed (`crypt`/`gen_salt('bf')`).

## Folders
| Path | What it is |
| --- | --- |
| `site/index.html` | The whole app |
| `site/manifest.webmanifest`, `site/*.png` | App name and icons (tab, phone home screen) |
| `tests/tests.html` | Test source (never published directly) |
| `tests/build-checks.py` | Embeds the tests into `index.html` as the private `#checks` page |
| `tests/run-tests.js` | Runs the tests headlessly with Playwright |
| `database/*.sql` | Database setup and update scripts |
| `TESTING.md` | Testing details |
| `docs/` | One-pager PDF for teachers and the school |

## Making a change
```bash
# 1. edit site/index.html and add a test in tests/tests.html
python3 tests/build-checks.py   # embed the tests into the site's #checks page
node tests/run-tests.js         # must end with "0 failed"
git push origin main            # goes live via GitHub Pages
```
- Always rerun `build-checks.py` after editing **either** `site/index.html` or `tests/tests.html`, then commit both files.
- Tests run against a sealed copy of the site with no internet and blank storage, so they never touch real data.
- If a test needs a function that lives inside a closure, expose it as `window.SH_name` (for example `window.SH_dn = dn`) and call `w.SH_name` from the test.
- Inside `tests/tests.html`, write `suite("Plain-English name")`, then `check(name, ok, detail)` or `eq(name, got, want)`. `w` is the site's window.

## Database changes
- Nobody can reach the live database from the repo or a dev container. Write a new file in `database/` whose header says what it does and whether it's safe to run again. The owner then pastes it into the Supabase SQL Editor and runs it.
- Use `create or replace function`, `add column if not exists`, and similar statements, so scripts can be run twice safely.
- Grant new functions to `anon`, and revoke helper functions (names starting with `_`) from `public, anon, authenticated`.
- When the site calls a new function, show a friendly toast if the function is missing, like "needs a quick database update", instead of crashing.
- Teacher functions take `pw` (JSON `{n, p, l}`) and call `_tctx(pw)` to check the teacher.

## Key concepts
- **Animal usernames:** each class has a `tag` (the teacher's initials plus the period, e.g. `ab3`). A student picks an animal from a grid after entering the class code, so the username is `animal + tag`. An animal is "taken" only by members of that same class. Everyone must log in: there is no guest mode. A student who forgets their username or PIN asks the teacher, who sees usernames in the class list and can reset a PIN (PINs are stored one-way, so nobody can look one up). Deleting a class deletes its animal-only student accounts.
- **Idle log out:** students (not teachers) who touch nothing for 30 minutes see a "Still there?" box. If nobody taps "I'm still here" within 1 minute, or the Chromebook was closed longer than that, Loro saves any assignment time and logs them out (`idleCheck`). Logging out also clears that student's weak spots from the browser.
- **PIN guessing wait:** `database/save-space-and-slow-pin-guessing.sql` renamed the original login check to `_sid_core` and wraps it in a new `_sid`. After 5 wrong PINs for a username, each try waits 1 minute (error `too many tries`). Counts live in 1,024 sequences `_lt0`…`_lt1023`, because sequence changes survive the failed login's rollback. The same script makes `student_log` add assignment minutes to one row per session instead of a row per minute.
- **No name labels:** teachers see only animal usernames. The old private name labels were removed completely. Teachers match usernames to real names outside Loro (school gradebook or a paper roster). `dn(n)` just returns the username.
- **Teacher passwords:** teachers log in with a password (8 to 72 characters, letters and numbers), checked by `goodPw()` on the site and `_goodpw()` in `database/teacher-passwords.sql`. A teacher who logs in with an old 4-digit PIN is asked to pick a password (`tNewPw`). Students keep 4-digit PINs.
- **Picture links:** every `<img src>` goes through `isrc()`, which only allows `data:image/…;base64` or `https://` links and escapes them. Never put a picture link into HTML without it.
- **Terms editor:** `editor()` shows rows (term | definition). Enter jumps to the next box and adds a row at the end. Pasting several lines into any box fills rows. "Paste a list" switches to the old textarea (`#sd`). `parse2()` reads tabs, `|`, ` - `, `=`, `;`, `: `, or term and definition on alternating lines.
- **Assignments:** each assignment has a goal type: minutes practiced, terms completed at a minimum %, or a timed goal (N words in M minutes at X%). Students turn work in, and teachers see it in the gradebook.
- **Weak spots:** terms a student keeps missing. They're saved per student, and teachers can view them per student and per class.
- **Libraries:** each teacher has their own library of units and sets, and can share sets with another teacher by share code.
- **Fixing built-in sets:** with editing unlocked, a built-in set's ⋮ menu has "Fix answers" (`fxPics` for pictures, `fxVerb` for Pretérito irregular) and "Reset to original". Fixes live in `FX`, saved as the library key `pfix` (listed in `SK`, so students get them when their library syncs). `fixP()` and `fixV()` rebuild `PIC` and `D` from the untouched originals `PA`/`PW0` and `D0`. Fixes are keyed by the original word or verb, so the built-in data itself never changes. Verb sets (type `verbs`, items `[verb, meaning, [6 forms], sentence ending]`) get "Fix forms & sentences" (`vFix`, added to the ⋮ menu by wrapping `pop`). It edits the set's own items, so fixes sync with the library like any edit.
- **Loro the parrot:** the parrot logo talks to students. On the home screen it counts open assignments (`loroAsg`). During any practice it slides in from the top right (big, for about 5 seconds) after every 5 in a row, and now and then with a random cheer or a "try again" (`loroAns`, hooked into `WK` and verb practice). Lines live in `LORO` and mix English and Spanish.
- **Top bar and home (Pro look):** a slim top bar holds the links (students: Home · My work · Answer key; teachers: Home · Dashboard), drawn by `navR()` and re-run on every `view()` and `#key` change. The student home (`drawAsg`) shows a `¡Hola!` heading, an Assignments card with progress bars (`gpct`), and a "Practice by unit" label. The teacher home has Loro beside the greeting and New unit · New set · Answer key. The styles are the "Pro look" block at the end of the main `<style>` and use `var(--acc)`, so they follow the theme. Unit cards keep their original style.
- **Themes:** students can pick a color theme. Default is Ocean Slate blue (`#3f78b5` → `#2f5d8f`).

## Gotchas
- `index.html` is huge. Search with `grep -n` and edit with exact, small replacements. Don't rewrite whole sections.
- The `<!--CHECKS-->…<!--/CHECKS-->` block at the end of `index.html` is generated. Never hand-edit it. Rerun `build-checks.py` instead.
- The `#gate` (login screen) must scroll on short screens. Keep content able to scroll instead of using a centered flex box that cuts off the top.
- `database/close-name-signup.sql` has been run, so the old "type your name" sign-up is off in the database. Never bring back `student_signup` with names.
