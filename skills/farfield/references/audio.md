# Podcast audio

Most of a brief comes from text. Some podcasts publish transcripts; a brief uses those for free. This file is for episodes that have audio only. `AUDIO` means `<this skill's folder>/scripts/audio.py`, run directly.

Default is **skip**: an episode without a transcript contributes its show notes and nothing more. Don't bring audio up unless the user picked or added a podcast themselves.

## The one question (in start, or when a podcast is added)

Run `AUDIO find` and `AUDIO estimate <workspace>` first so the question has real numbers. Then:

"<N> podcast episodes from the last 30 days have no transcript, about <H> hours. Want me to transcribe them on this computer? It's free and takes one setup: about a 2.3 GB download."

- **Yes, set it up** (Recommended)
- **No, show notes are fine**

No API key, no account, no model choice. Don't list alternatives unless they ask.

## Setting it up (on yes)

Run `AUDIO install` and relay its three progress lines. It does everything: ffmpeg through Homebrew if it's missing, Parakeet in a private folder (`~/.local/share/farfield/parakeet`, nothing global), the model download, and a test. It can take several minutes on a slow connection; say so before starting. Then:

1. `AUDIO use <workspace> parakeet`
2. `AUDIO transcribe <workspace> <one recent episode's audio URL> --max-secs 120` and show the first two sentences, so they see it work.

If `install` fails, read its message: it says exactly what is missing (Homebrew, or Python 3.10+). Fix that one thing with them, or leave audio on skip. Never leave a half-installed state unmentioned.

## Not an Apple Silicon Mac, or another language

`AUDIO find` says `"suggested": "whisper"`. Whisper large-v3-turbo through whisper.cpp: they need `whisper-cli` and a ggml model file (`AUDIO find` lists any already on the machine). `AUDIO use <workspace> whisper --model <path>`. Parakeet covers English and about 25 European languages; anything else is also Whisper.

## Backups, only if they ask

- **They already have a model and prefer it:** use it. `AUDIO find` lists what's in the usual folders, or they give a path.
- **They want cloud transcription:** `AUDIO use <workspace> openrouter`, key through `HELPER keys --open` (never in chat). `AUDIO estimate` shows the monthly cost for the supported providers.

## During a brief

For each podcast episode in the window with no published transcript, if `audio.json` is not `skip`: `AUDIO transcribe <workspace> <audio url>`. It prints a `raw` path; quotes from that episode use it like any other raw page, and the brief marks them "machine transcript" because names and numbers can be wrong. Cap: 6 hours of audio per run unless `me.md` says otherwise; say what was left out. A failed transcription is a skipped episode noted under "what was read", not a failed brief.

## Unattended

Never install anything or change the audio choice in a scheduled run.
