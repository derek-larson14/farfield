# Start: four questions, then a brief

The user types one paragraph and clicks four answers; you do the rest. Questions take a couple of minutes. The first brief then takes about 10 to 30 minutes of reading, so say that before you start it and post a one-line update per phase. Do the work yourself; don't hand them steps. If `HELPER where` already finds a workspace, say where it is and ask whether they want a brief now or to change the setup.

## 1. One open question (free text)

Say, in your own words: "Tell me what you're working on (one to three projects) and one question you're stuck on. A few sentences is plenty." Wait for the answer. If the conversation or the current folder already makes this obvious, propose it instead and ask them to correct it.

## 2. Four choices (structured questions)

Use the question UI described in SKILL.md. Group these within the host's limits, recommend a default, and explain the consequence in the option description. Keep setup conversational; the person should not need to read a guide. If they already supplied an answer, use it instead of asking again.

1. **Context**: "Can I read a folder to understand the work better?"
   Explain: "Only the folder you choose; or I can work from your description. Text I read is processed by your current model provider under your account."
   - No, just use what I told you (Recommended) *(unless the current folder is clearly their project; then recommend that instead)*
   - This folder (`<current directory>`) *(offer only if it looks like their project or notes, not a home directory)*
   - Another folder (they paste a path)
   - A Google Drive folder *(offer only if a Drive connector is available in this session; it replaces one of the others, since the tool allows four options)*
2. **Where briefs go**: "Where should I keep your briefs?"
   Explain: "These are ordinary Markdown files you can keep, edit, or open in Obsidian."
   - `~/farfield` (Recommended)
   - `./farfield` inside this folder *(good for an Obsidian vault or notes repo)*
   - Somewhere else *(then ask for the path)*

All four fit one `AskUserQuestion` call in Claude Code.
3. **Sources**: "What should I read?"
   Explain: "You can add or mute sources later by asking me."
   - The curated list (Recommended) *(say how many sources and name three)*
   - The curated list plus my own *(then ask for names or URLs in a follow-up)*
   - Only my own
4. **How often**: "How often do you want a brief?"
   Explain: "I'll write the first one now. Weekly or monthly is a preference for now; I'll offer to set it up after you've seen the result."
   - Weekly (Recommended)
   - Monthly
   - Only when I ask

Then one more call with two questions, about how they work. Explain first, in one or two sentences: "Besides reading the news for you, I can look for work that rhymes with how you work: people tackling similar problems, new methods that might fit. To do that I'd read what you typed in your recent Claude Code and Codex conversations on this computer. Not tool output or file contents; keys and emails are blanked out. It stays on this computer."

5. **How you work**: "Can I look at your recent agent conversations?"
   - Yes, the last 30 days (Recommended)
   - Yes, but only conversations in the project folders I named
   - No
6. **How often**: "How often should I look for work that rhymes with yours?"
   - Monthly (Recommended) *(patterns need a few weeks to show)*
   - Every brief
   - Only when I ask

If they said yes, ask once in plain text: "Is there anywhere else that shows how you work, like a notes folder or a Drive folder? Optional." Add any answer under "Read for context". Don't go looking in other systems on your own, even if a connector exists.

Record the answers under "How I work" in `me.md`. If they said no, skip 6.

After these choices, offer the optional Twitter/X question in [social.md](social.md) once. It is a separate opt-in, not required setup.

## 3. Show the working picture

Run `HELPER init <workspace>`. If they offered a folder: list file names and dates first, then read at most five files per project (an overview, the most recent notes, anything that states an open problem). Skip credentials, `.env`, binaries, dependency folders. Stay inside the folder they named.

Then show five lines and ask for corrections, once:

> **Working on:** …
> **Stuck on:** …
> **Already knows:** …
> **Will read for context:** `<paths>` (or "nothing")
> **Skip:** …

Write the corrected version to `me.md` using its headings. Tell them: the text I read goes to the model provider you're already using, under your account; nothing goes to the shared source list or this skill's repository.

For "Only my own", first run `HELPER source-mode <workspace> only-mine`. This keeps future catalog additions off too. Then follow [sources.md](sources.md) to resolve each named source: add a new URL, or unmute its existing ID if already in the catalog. Only explicitly selected sources should be enabled. A catalog match is still their choice, shown as "Picked from the curated list". For the curated choices, use `HELPER source-mode <workspace> curated`; existing individual mutes stay respected. If a source they name is already in the curated list, `add` says so: tell them it's already included rather than adding it twice.

If any enabled source is a podcast and the user chose or added it themselves, ask the one audio question in [audio.md](audio.md). Otherwise leave audio on skip and don't mention it.

If they said yes to conversations, run `<skill>/scripts/threads.py digest <workspace>` (add `--days 30`) and use it for the working summary as [context.md](context.md) describes. Create the bounded working summary in `state/context.md` following [context.md](context.md). Link it alongside `me.md`; this is the agent's correctable picture of the work, not another setup questionnaire.

## 4. Write the first brief now

Run the Brief section of SKILL.md. Don't wait for anything else.

## 5. Hand over

After the brief, show these links using the host's supported local-file format:

- Your brief: `briefs/<date>.md`
- What I think you're working on (edit any time): `me.md`
- What I read (add or mute any time): `sources.md`
- Commands: `brief`, `sources`, `schedule`

Ask which findings were useful, already known, or not relevant, and record the answers in `feedback.md`.

## 6. Schedule

If they chose weekly or monthly, say "Want me to set that up now?" and on yes follow [schedule.md](schedule.md). If the first brief wasn't useful, fix the profile or sources first and offer scheduling after a second brief.
