# Farfield

There’s a lot happening in AI. Most of it doesn’t matter to your work.

Farfield reads essays, papers and podcasts with your projects in mind, and brings back a short brief of ideas worth exploring, each with its source.

Runs in Claude Code or Codex on the subscription you already have. No new account or API key.

## Get started

Paste this into your agent:

```text
Set up Farfield for me. Fetch https://farfield.newyorkai.org/install.md with curl (or open it if you can't run commands), read all of it, and follow it: install the skill, ask me the setup questions and wait for my answers, then write my first brief.
```

Farfield asks where to look for project context. You can name the current project, other folders on your computer, or a specific folder in a connected app like Drive. You can include all of that in a brain dump about what you’re working on. Farfield finds the relevant files and saves the locations you approve in `me.md`. After a few choices, it reads for 10 to 30 minutes and writes a short brief with source passages, links, and why each idea might matter. If nothing is worth including, it says so.

In **Claude desktop**, open **Customize → Plugins → + Add → Add marketplace → Add from a repository**. Click **Select a repository**, enter `derek-larson14/farfield`, choose **Use “derek-larson14/farfield”**, and click **Sync**. Under **Discover**, open **Farfield** and click **Add**. No GitHub connection is needed. You can also download [farfield.zip](https://farfield.newyorkai.org/farfield.zip) and select it under **Plugins → + Add → Upload plugin**.

In a new session in the desktop **Code** tab, type `/farfield` and select **farfield:start** to open the setup picker.

In the **Claude Code terminal**, use the hosted marketplace:

```text
/plugin marketplace add https://farfield.newyorkai.org/marketplace.json
/plugin install farfield@farfield
/farfield:start
```

In Codex or a terminal: `curl -fsSL https://farfield.newyorkai.org/install.sh | sh`, then `$farfield start` in Codex. The script is [site/install.sh](site/install.sh); read it first if you like.

## After setup

- **Another brief:** `/farfield:brief` (Codex: `$farfield brief`)
- **Change sources:** `/farfield:sources` (Codex: `$farfield sources`)
- **Schedule it:** `/farfield:schedule` (Codex: `$farfield schedule`) runs it weekly or monthly, on this computer, in the Claude desktop app, or in the cloud. It suggests an off-peak time so runs use less of your plan.

## Sources

Practitioners, researchers, independent evaluations, interviews, and recent papers. [See the reading list](https://farfield.newyorkai.org/sources). Add your own, mute anyone, or use only your sources. [Suggest a source](https://github.com/derek-larson14/farfield/issues/new?template=source.yml).

Optional, paid: Twitter/X and cloud podcast transcription through OpenRouter. Setup shows cost estimates and keeps both off unless you turn them on.

## Privacy

- Briefs and notes stay in a folder you choose. Nothing is uploaded here.
- Your agent reads the project locations you approve. Reading recent Claude Code and Codex prompts is a separate choice.
- Searches use general descriptions, never your words. [What gets written where](AGENTS.md#what-gets-written-where).

Experimental. [Setup details](AGENTS.md) · [Contributing](CONTRIBUTING.md) · [MIT license](LICENSE) · Built by [Derek Larson](https://dtlarson.com)
