# Keep a useful picture of the work

`me.md` is the user's corrected description, preferences, and approved context locations. `state/context.md` is a short working summary for the agent, refreshed before each brief. Neither belongs in the distributed skill or a shared feed.

Use the conversation, the user's brain dump, and approved context to identify one to three active projects, their current stage, constraints and decisions. List names and dates inside the approved scope where possible. Prefer a current overview or decision note. Read at most five files or records per project across all locations. Skip secrets, dependencies, and links outside the selected scope.

## Read for context

Store one entry per approved place in `me.md`, with the actual path or stable link, what it's for, and any limits the user gave. For example:

> - Local: `/Users/name/projects/kiosk` · Current project notes.
> - Local: `/Users/name/notes/kiosk.md` · Just this file.
> - Google Drive: [Kiosk decisions](<folder link>) · This folder only, for recent decision notes.

Existing entries with just local paths still work. An empty section means use the profile only. A provider name, a connected plugin, a source in the public reading list, or a link from an approved document is not permission to read a new place. Never save credentials or access tokens.

For connected apps, use tools that can read within the approved file, folder, page, or other named resource. Never substitute a broad provider search, move up to a parent folder, follow external shortcuts, or change access, files, or account settings. If the session lacks the connector, permission, or a way to restrict the read, skip that location and note the gap in the brief's coverage. Keep its saved scope for later runs; ask for a narrower location only in an interactive session. If the scope is removed from `me.md`, stop reading it and drop its derived context from subsequent summaries.

Write at most 500 words in `state/context.md`, dated, with:

- Each project's name, intended outcome and current stage.
- Its next unresolved decision or bottleneck, and what new evidence would change the approach.
- Approaches already tried or understood; avoid rediscovering them.
- Supporting file paths or approved resource links and dates, or the dated user statement. Distinguish confirmed facts from inferences and stale information.
- Two or three research questions derived from those decisions, plus one adjacent mechanism worth exploring.

At each brief, read `me.md` and the previous context summary first, then check permitted files for changes. Update the derived summary with supported changes. The user's explicit corrections override inference. Never silently rewrite `me.md` or turn a speculative interpretation into a new goal. If work appears to have changed, label it tentative, propose a correction after the brief, and use the confirmed goals until corrected. In unattended mode record the uncertainty without asking a question.

## How they work (only if `me.md` allows reading conversations)

When the "How I work" schedule says it's due (monthly: if `state/threads/` has no digest from the last 28 days; every brief: always; when asked: only on request), run `<skill>/scripts/threads.py digest <workspace> --days 30` and read the newest `state/threads/<date>.md`. If they limited it to their project folders, use only the sections for folders listed in `me.md`.

Add a "How they work" part to `state/context.md`, at most 150 words: what they've been spending time on, recurring kinds of task, what they keep coming back to, and where things seemed to take several tries. Write observations, not verdicts: "spent time in eight conversations on deploy setup", never "struggles with" or "wastes time on". Each line names how many conversations it comes from. Say plainly that this is a partial view: other computers, apps, meetings and thinking don't show up, so something that looks repetitive may be the right call for reasons you can't see.

Never quote their messages in a brief, never put names, clients or file paths from conversations into a search, and never keep more than the summary. The digest file is theirs to delete.

## Filter

Filter each candidate by asking: which named decision could this affect, what is new relative to what they already know, and why now? If the answer is only “they work in AI,” it is too generic. A surprising connection needs a plausible mechanism and a small way to check it, not a motivational analogy. Relevant contrary evidence matters too.

Search with generalized technical questions. Do not send private customer names, confidential plans or raw project notes to search engines or optional external APIs. Read the summary locally with the user's existing model provider. Link it after the first brief as “My working picture” so they can correct it.
