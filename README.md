# Farfield

There’s a lot happening in AI. Farfield reads essays, papers, and podcasts with your work in mind, and brings back a few ideas worth looking into.

A skill for Claude Code and Codex (CLI or desktop). It runs through your existing agent account. No additional account or API key is needed.

[Website](https://farfield.newyorkai.org) · [Setup instructions](AGENTS.md) · [Sources](skills/farfield/catalog.json)

## Quick start

Paste this into your agent:

```text
Set up Farfield for me. Fetch https://farfield.newyorkai.org/setup.md and follow it: install the skill, ask me the setup questions and wait for my answers, then write my first brief.
```

The website serves [AGENTS.md](AGENTS.md) as `/setup.md`. You can also give your agent this repository URL and ask it to follow that file.

## What you get

A short Markdown brief with zero to four findings. Each includes the idea, why it might matter to a named project or question, a source passage, and a link to read more. If nothing clears the bar, it says so.

It starts with an opinionated source list. Add your own sources, mute someone, or use only your own. Tell it which findings were useful, already known, or irrelevant.

## Install

### Claude Code

```
/plugin marketplace add derek-larson14/farfield
/plugin install farfield@farfield
/farfield:start
```

### Claude desktop app or Cowork without a shell

Customize > Browse plugins > Personal > Add marketplace from GitHub. Paste `derek-larson14/farfield`, install, then type `/farfield:start`.

### Codex

Paste the prompt at the top of this page. It copies one folder to `~/.agents/skills/farfield`. Then:

```
$farfield start
```

### Anything else

Any agent that can read files and browse can follow [`skills/farfield/SKILL.md`](skills/farfield/SKILL.md). See the testing status below for what has actually been verified.

Setup is one question about your work and four choices (a folder it may read, where briefs go, which sources, how often). It shows what it understood in five lines for you to correct, writes the first brief, and offers to schedule it.

## How it works

Every brief is the same five steps. Your agent does all of them; there is no service behind it.

1. **Read your note.** `me.md` says what you're working on, what you're stuck on, and what you already know. If you named a folder, it looks at what changed there.
2. **Read the sources.** Everything on your list published since the last brief, up to about 40 items read in full. About a fifth of the reading goes to fields outside your usual ones.
3. **Keep passages, not summaries.** For anything promising it saves the exact quote, the link and the date. A small script fetches the page itself and checks the quote is really on it. A quote that isn't there is dropped.
4. **Choose.** It keeps what could change how you approach a named project or question, skips what you already know or have been shown, and holds model releases and tool news to a third of the brief.
5. **Write.** Zero to four findings in `briefs/`, with the evidence behind them in `evidence/`. Your feedback on each one shapes the next brief.

| Command | Does |
|---------|------|
| `/farfield:start` | Set up, or change your setup |
| `/farfield:brief` | Write a brief now |
| `/farfield:sources` | See, add, mute or suggest a source |
| `/farfield:schedule` | Run it weekly or monthly |

In Codex: `$farfield start`, `brief`, `sources`, `schedule`.

## Sources

It starts from a curated list, [`catalog.json`](skills/farfield/catalog.json). `sources.md` in your folder always shows what it reads.

| Kind | On the starting list | What a brief reads |
|------|----------------------|--------------------|
| Newsletters and blogs | Simon Willison, Import AI, Interconnects, One Useful Thing | The full post |
| Podcasts | Hard Fork, The Cognitive Revolution, Odd Lots | The published transcript, otherwise show notes |
| Papers | Hugging Face daily papers | Title and abstract |
| Discussion | Hacker News front page | The linked piece |
| Yours | Any feed, channel, site, or a search to re-run each time | Whatever the page gives |

Say "add this podcast", "mute Hacker News" or "suggest this for everyone". Adding is yours alone. The agent can draft a suggestion for you to review. No suggestion is sent automatically; see [CONTRIBUTING.md](CONTRIBUTING.md).

**Podcast audio** is off by default. Say yes when it asks and it sets up [Parakeet](https://github.com/senstella/parakeet-mlx) on your Mac (Apple Silicon, a 2.3 GB download, no key), then transcribes episodes that have no transcript. It tells you how many hours that is first. On other machines it uses Whisper.

## Your folder

```
your-folder/
  me.md            what you're working on; edit it any time
  sources.md       what it reads: curated, yours, muted
  briefs/
    2026-11-16.md
  evidence/        the exact quotes and links behind each brief
  feedback.md      useful, already knew, not relevant
  state/           what it has already shown you
```

It's all plain files. Delete the folder and it's gone.

## Scheduling

Ask `/farfield:schedule` (Codex: `$farfield schedule`) after trying a brief. The agent explains the options available in your environment and asks before creating a schedule. Local runs require the computer to be awake and the relevant app or scheduler available. Scheduling has not yet been verified end to end across every supported host.

## Updating, privacy, keys

- **Updating:** `/plugin marketplace update farfield`, then `/plugin update farfield@farfield`. In Codex, paste the install prompt again. Updates never touch your folder, and the skill never updates its own code.
- **Privacy:** your files stay on your machine. The text your agent reads goes to the model provider you already use, under your account's settings. Nothing personal goes to this repo or the shared source list.
- **Keys:** none are needed. An [Exa](https://exa.ai) key makes searching outside your usual sources better. If you add one, it goes in a private file that the skill opens for you, never in the chat.

## Status

Early experimental release.

- The shared, pre-read evidence feed isn't published yet. Today each brief reads its sources live through your agent's web access.
- Automated helper tests and an isolated Codex onboarding rehearsal have passed. The rehearsal used a preloaded skill and a bounded source sample.
- Fresh-machine installation and every CLI/desktop combination have not yet been verified.

For development and source proposals, see [CONTRIBUTING.md](CONTRIBUTING.md).

Built by [Derek Larson](https://dtlarson.com).

## License

[MIT](LICENSE)
