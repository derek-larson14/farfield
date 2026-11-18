# Start with the user's project

Use the structured question tool described in SKILL.md for every setup question. Use its custom answer for paths, a brain dump, and corrections. If the current session lacks the tool, explain how to continue on their host. In Claude desktop, use a local session in the **Code** tab and run `/farfield:start`. In Codex, use an interactive session with the picker available and run `$farfield start`. If only a planning session offers the picker, gather the answers there and switch back to a mode that can write files before applying them. Do not substitute a text questionnaire. The first brief takes about 10 to 30 minutes of reading. Say so before you start it and post one short update per phase.

## 1. Get oriented, then ask where to look

Start with the conversation and the current project folder, if the host already identifies one. Take a shallow look at top-level names and project guidance such as `CLAUDE.md` or `AGENTS.md`. Use Claude's native file tools, or Codex's read-only workspace tools. Do not recurse, open project content yet, or scan a home directory, sibling projects, or connected services. If there is no clear project folder or no file access, skip the look. Project guidance can suggest where relevant files live, including a folder elsewhere on the computer. Offer that location as a choice if it is specific and relevant. A reference to another location does not grant permission to list or read it. Do not run the Farfield workspace or update checks before opening the picker. Put what you learned in the picker itself.

Open the structured picker with one question: **Where should I look to understand what you're working on?** Mention a specific folder or candidate documents if the quick look surfaced them. Explain that the user can describe their work and name one or more places in the same answer. You'll read a few relevant files or records from the places they approve, and their current model provider processes what you read. Offer:

- **This project only (Recommended)**, with the actual path. Offer this only for a clearly identified project.
- **Choose more places**, including this project if they want, other local folders, or specific places in connected apps.
- **Brain dump**, with custom input for what they're working on and any decision or question they'd like help with. They can include locations in the same answer or use only what they tell you. Recommend this if there is no clear current project.

Accept a custom answer in the first picker. If their choice still needs detail, use one follow-up picker with custom input: **What are you working on, and where should I look?** A rough note is enough, for example: “Use this project plus `~/notes/kiosk` and this one Drive folder [link]. I'm deciding what to test first.” If the host offers a capability inventory, check only the names and descriptions of read tools already available in this session. Surface a few relevant apps, such as Drive if it can read a selected folder. Plugin installation or connector access alone gives Farfield no scope. Do not install tools, connect accounts, list provider content, or offer an unrestricted app as a source just to build this picker. Where the picker supports multi-select, let users mark several places or apps to scope. Otherwise one custom answer can name several places.

Turn their answer into a short list of exact folders, files, or app resources and any limits they gave. A vague app name such as “Drive” is a starting point: ask in the picker for a specific folder or file link. A local path, scoped link, or selected resource from the host's picker is enough. Ask before reading a location you inferred, or one the user mentioned without saying you may read it. For a precise, explicitly approved location, find the relevant items yourself. Keep external locations that can't be read with the current tools out of the approved list and tell the user what's unavailable. They can attach files or give a brain dump instead. Follow the read limits in [context.md](context.md). Don't make them repeat what the files or conversation already tell you.

After getting context, check for an existing workspace with `HELPER where --optional` if the host can run the helper. Empty output with a successful exit means this is a first run. Reuse an existing result from brief mode. If a workspace exists and setup is complete, show its path in the picker and offer to write a brief with the saved setup or revise it. If helper access is unavailable, move setup to a session with local file and command access before asking for storage preferences. Never guess the workspace.

## 2. Ask for preferences

Use the question UI described in SKILL.md. Group these within the host's limits, recommend a default, and explain the consequence in the option description. If they already supplied an answer, use it instead of asking again. The options below are ready to show once you know whether there is a workspace. Do not run another tool to inspect or count the source catalog before asking.

1. **Where briefs go**: "Where should I keep your briefs?"
   Explain: "These are ordinary Markdown files you can keep, edit, or open in Obsidian."
   - `~/farfield` (Recommended)
   - `./farfield` inside this folder *(good for an Obsidian vault or notes repo)*
   - Somewhere else *(then ask for the path)*

2. **Public reading list**: "What outside sources should I read for your briefs?"
   Explain: "This controls the publications I follow. Your project folders and connected apps are listed separately. You can add or mute publications later."
   - The curated list (Recommended): Start with a mix of AI engineering essays, papers, newsletters and podcasts.
   - The curated list plus my own *(then ask for names or URLs in a follow-up)*
   - Only my own
3. **How often**: "How often do you want a brief?"
   Explain: "I'll write the first one now. Weekly or monthly is a preference for now; I'll offer to set it up after you've seen the result."
   - Weekly (Recommended)
   - Monthly
   - Only when I ask

Then one more call with two questions, about how they work. Explain first, in one or two sentences: "Besides reading the news for you, I can look for work that rhymes with how you work: people tackling similar problems, new methods that might fit. To do that I'd read what you typed in your recent Claude Code and Codex conversations on this computer. Not tool output or file contents; keys and emails are blanked out. The digest is saved only in your Farfield folder; like everything I read, the model provider you already use processes it. Your words are never put into searches."

4. **How you work**: "Can I look at your recent agent conversations?"
   - Yes, the last 30 days (Recommended)
   - Yes, but only conversations in the project folders I named
   - No
5. **How often**: "How often should I look for work that rhymes with yours?"
   - Monthly (Recommended) *(patterns need a few weeks to show)*
   - Every brief
   - Only when I ask

Record the answers under "How I work" in `me.md`. If they said no, skip the follow-up about how often.

## 3. Show the working picture

Tell the user which files informed the picture, with links. Show five lines and offer **Looks right** and **Make a correction** in the picker. Use its custom answer for corrections:

> **Working on:** …
> **Stuck on:** …
> **Already knows:** …
> **Will read for context:** each approved folder, file, or app location and its limits (or "only what you told me")
> **Skip:** …

After they confirm or correct it, run `HELPER init <workspace>` and write the agreed version to `me.md` using its headings. Save approved context under **Read for context**, one entry per place, using the format in [context.md](context.md). Fold the brain dump into the relevant project, question, and skip headings. Preserve existing entries when revising setup unless the user changes their scope. If a correction introduces a new place, resolve it within the scope they chose and include it in the working picture before saving.

For "Only my own", first run `HELPER source-mode <workspace> only-mine`. This keeps future catalog additions off too. Then follow [sources.md](sources.md) to resolve each named source: add a new URL, or unmute its existing ID if already in the catalog. Only explicitly selected sources should be enabled. A catalog match is still their choice, shown as "Picked from the curated list". For the curated choices, use `HELPER source-mode <workspace> curated`; existing individual mutes stay respected. If a source they name is already in the curated list, `add` says so: tell them it's already included rather than adding it twice.

Once the workspace exists, offer the optional Twitter/X question in [social.md](social.md) once. It is separate from setup and defaults to off. If any enabled source is a podcast and the user chose or added it themselves, offer the audio choice in [audio.md](audio.md) if they haven't already answered it. Otherwise leave audio on skip and don't mention it.

If they said yes to conversations, run `<skill>/scripts/threads.py digest <workspace>` (add `--days 30`) and use it for the working summary as [context.md](context.md) describes. Create the bounded working summary in `state/context.md` following [context.md](context.md). Link it alongside `me.md`; this is the agent's correctable picture of the work, not another setup questionnaire.

## 4. Write the first brief now

Run the Brief section of SKILL.md. Don't wait for anything else.

## 5. Hand over

After the brief, link the saved brief, `me.md` (what you think they're working on) and `sources.md` (what you read). Tell them the files are theirs to edit and that next time it's `brief`, `sources` or `schedule`. Use the brief's feedback picker for usefulness.

## 6. Schedule

If they chose weekly or monthly, offer **Set it up** and **Not now** in the picker. On yes follow [schedule.md](schedule.md). If the first brief wasn't useful, fix the profile or sources first and offer scheduling after a second brief.
