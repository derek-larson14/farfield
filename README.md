# Farfield

There’s a lot happening in AI. Most of it doesn’t matter to your work.

Farfield sifts through essays, papers, and podcasts with your work in mind, and brings back a few ideas worth exploring.

Works with your existing Claude Code and Codex accounts.

## Get started

Paste this into your agent:

```text
Set up Farfield for me. Read https://raw.githubusercontent.com/derek-larson14/farfield/main/AGENTS.md in full (the file itself, not a summary) and follow it: install the skill, ask me the setup questions and wait for my answers, then write my first brief.
```

Tell it what you’re working on. It asks a few questions, then reads for 10 to 30 minutes and writes a short brief with source passages, links, and why each idea might matter. If nothing is worth including, it says so.

Or install it yourself. In Claude Code:

```text
/plugin marketplace add derek-larson14/farfield
/plugin install farfield@farfield
/farfield:start
```

In Codex or a terminal: `curl -fsSL https://farfield.newyorkai.org/install.sh | sh`, then `$farfield start` in Codex. The script is [site/install.sh](site/install.sh); read it first if you like.

After setup, ask for another brief, change your sources, or set up a schedule. In Claude Code: `/farfield:brief`, `/farfield:sources`, `/farfield:schedule`. In Codex: `$farfield brief`, `sources`, or `schedule`.

## Sources

Practitioners, researchers, independent evaluations, interviews, and recent papers. [See the reading list](SOURCES.md). Add your own, mute anyone, or use only your sources. [Suggest a source](https://github.com/derek-larson14/farfield/issues/new?template=source.yml). Twitter/X and cloud transcription are optional paid additions; setup shows estimates before enabling either.

## Privacy

Briefs and notes are files in a folder you choose. Your agent reads only the context you permit, such as a project folder or, if you say yes, what you typed in your recent Claude Code and Codex conversations. That text is processed by your existing model provider, and searches use general descriptions, never your words. Farfield does not upload your workspace to this repository. Browsing contacts the source sites. Audio downloads and scheduling require your approval.

Experimental. Full installation and onboarding have not been verified across every supported host.

[Setup details](AGENTS.md) · [Contributing](CONTRIBUTING.md) · [MIT license](LICENSE) · Built by [Derek Larson](https://dtlarson.com)
