# Schedule

Goal: the user says "weekly" and it is running, with at most one approval click. Work out where you are, pick the option that fits, do the setup yourself, and prove it with one run while they watch.

The scheduled prompt is always the same (weekly shown; adjust the wording for monthly):

> Run the farfield skill in brief mode, unattended. Workspace: `<absolute path>`. End with the SUMMARY line.

In Claude that is `/farfield:brief unattended. Workspace: <path>. End with the SUMMARY line.`; in Codex, `$farfield brief, unattended, workspace <path>`. Always include the word "unattended".

## 1. Which host is this?

Check what you actually have; don't ask the user to explain their setup.

| You have | You are in | Use |
|---|---|---|
| A tool to create scheduled tasks (Claude desktop app, Code or Cowork tab) | Claude desktop | **A. Desktop task** |
| The `/schedule` skill, a terminal, no desktop task tool | Claude Code CLI | Ask: **B. This computer** or **C. Cloud** |
| Codex app | Codex desktop | **D. Codex scheduled task** |
| Codex CLI, or anything else with a shell | terminal | **B. This computer** |
| No shell, no scheduler | chat only | Tell them it can't be scheduled here; `brief` on request works |

When there is a real choice (B or C), ask one question:

- **This computer** (Recommended): reads your local folders; runs when the machine is awake.
- **Cloud**: runs with the laptop closed; only sees a private GitHub repo, so your workspace moves there and local context folders are not read.

Then ask day and time in one question. Recommend off-peak times: weekday working hours are peak, and the Claude app warns that runs then use plan limits faster. Defaults: weekly on Sunday at 6pm, so it's ready Monday morning; monthly on the 1st at 5am. Offer one other off-peak option and "Other".

## A. Claude desktop app

Create the task yourself with the scheduled-task tool: name `farfield`, the prompt above, working folder = the workspace, the chosen schedule. Then tell the user, in two lines:

- It runs while the Claude app is open and the computer is awake. After sleep it runs once to catch up.
- Open **Scheduled → farfield → Run now** once and choose "always allow" on each prompt. After that it runs without asking. If a later run stalls, it's waiting in that same place.

It needs (and nothing else; in particular it never reads the keys file itself, the helper does): read the workspace and any context folders in `me.md`, write inside the workspace, fetch web pages, start subagents, and run the skill's six scripts (`radar.py`, `library.py`, `threads.py`, `audio.py`, `social.py`, `feed.py`).

## B. This computer (terminal)

Claude Code's own `/loop` and cron tools end with the session and expire after seven days, so they are not a schedule. Use the operating system.

1. Write `<workspace>/state/run.sh`:

   ```sh
   #!/bin/sh
   cd "<workspace>" || exit 1
   "<absolute path from: command -v claude>" -p "/farfield:brief unattended. Workspace: <workspace>. End with the SUMMARY line." \
     --model sonnet \
     --permission-mode acceptEdits \
     --allowedTools "Read" "Write" "Edit" "Glob" "Grep" "WebFetch" "WebSearch" "Agent" \
       "Bash(*/farfield/scripts/radar.py *)" "Bash(*/farfield/scripts/library.py *)" \
       "Bash(*/farfield/scripts/audio.py *)" "Bash(*/farfield/scripts/social.py *)" \
       "Bash(*/farfield/scripts/threads.py *)" \
       "Bash(*/farfield/scripts/feed.py *)" \
     --add-dir "<each context folder from me.md>" \
     </dev/null >> state/run.log 2>&1
   ```

   Codex CLI equivalent: `codex exec -C "<workspace>" -s workspace-write -m <newest Sol model> "\$farfield brief, unattended" </dev/null >> state/run.log 2>&1`. Find the Sol model's exact name in the Codex model picker (`/model`), not from memory.

   A scheduled brief runs on the everyday tier (Sonnet in Claude Code, Sol in Codex), not the top one, so it doesn't eat into the user's plan. Readers still go to the fast tier as SKILL.md says. Write `sonnet` as is (Claude Code resolves it to the current version); a Codex model name includes a version, so check it again when updating the schedule.

   The prompt must say "unattended", or the run will stop to ask for feedback and never print its SUMMARY line. Never use a skip-all-permissions flag. Edits are limited to the workspace because that is the working directory.

2. Show the user the script and the schedule entry, and get a yes before installing. This is the one approval.
   - macOS: a LaunchAgent at `~/Library/LaunchAgents/com.farfield.brief.plist` with `StartCalendarInterval`, then `launchctl bootstrap gui/$(id -u) <plist>`. launchd runs a missed job when the Mac next wakes.
   - Linux: a `crontab` line. Windows: Task Scheduler via `schtasks`.
3. Run `state/run.sh` once now (it takes 10 to 30 minutes) and show the last line of `state/run.log`. It must be a `SUMMARY:` line; if the log shows a permission refusal, fix the allowed tools rather than widening permissions.

To stop: `launchctl bootout gui/$(id -u)/com.farfield.brief` and delete the plist (or remove the crontab line). Tell them this.

## C. Claude Code cloud (`/schedule`)

A cloud run starts from a fresh clone of a GitHub repository. It cannot see this computer.

1. Explain the trade in one sentence and confirm: the workspace becomes a **private** GitHub repo; briefs arrive as commits; local context folders are not read (copy the few files that matter into `context/`).
2. In the workspace: remove the `*` line from `.gitignore`, copy this skill's folder to `.claude/skills/farfield/` (cloud sessions load skills committed to the repo; they do not have the user's installed plugins), `git init`, and create the private repo with `gh repo create --private` after the user confirms the name. Don't push anything they haven't seen listed.
3. Run `/schedule` with: the repo, the schedule, and the prompt above plus "Commit the brief, evidence and state to the default branch" (without that sentence, changes land on a `claude/` branch).
4. The cloud environment's default network access is a limited allowlist. Source sites are mostly outside it: tell the user to open the task at https://claude.ai/code/routines → Edit → environment and widen network access, or briefs will report unreachable sources.
5. Runs and their output are at https://claude.ai/code/routines. Minimum interval is one hour; runs count against their plan's usage.

## D. Codex app

Ask Codex to create the scheduled task from this conversation: prompt `$farfield brief, unattended, workspace <path>`, the newest Sol model if the task lets you set one, running in the local project (not a worktree: the workspace isn't a repo). Tell the user:

- It runs with the app open and the computer on, with their default sandbox settings. Workspace-write is enough.
- Results show up in the app's **Scheduled** view. Codex CLI has no schedule manager; use B there.

## After any of them

Write what you set up to `<workspace>/state/schedule.md`: host, method, schedule, how to pause it, how to remove it. Then say where the next brief will appear and when. If they later ask "is it running", read that file and check the newest file in `briefs/` and the last `SUMMARY` line.
