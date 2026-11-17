# Farfield

There’s a lot happening in AI. Most of it doesn’t matter to your work.

Farfield reads essays, papers and podcasts with your projects in mind, and brings back a short brief of ideas worth exploring, each with its source.

Runs in Claude Code or Codex on the subscription you already have. No new account or API key.

## Get started

Paste this into your agent:

```text
Set up Farfield for me. Fetch https://farfield.newyorkai.org/install.md with curl (or open it if you can't run commands), read all of it, and follow it: install the skill, ask me the setup questions and wait for my answers, then write my first brief.
```

Tell it what you’re working on. It asks a few questions, then reads for 10 to 30 minutes and writes a short brief with source passages, links, and why each idea might matter. If nothing is worth including, it says so.

Or install it yourself. In Claude Code:

```text
/plugin marketplace add https://farfield.newyorkai.org/marketplace.json
/plugin install farfield@farfield
/farfield:start
```

In the Claude desktop app: Customize → Plugins → Add marketplace → `derek-larson14/farfield`, or upload [farfield.zip](https://farfield.newyorkai.org/farfield.zip) on the same page.

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
- Your agent reads only what you allow: a project folder, and if you say yes, your recent Claude Code and Codex prompts.
- Searches use general descriptions, never your words. [What gets written where](AGENTS.md#what-gets-written-where).

Experimental. [Setup details](AGENTS.md) · [Contributing](CONTRIBUTING.md) · [MIT license](LICENSE) · Built by [Derek Larson](https://dtlarson.com)
