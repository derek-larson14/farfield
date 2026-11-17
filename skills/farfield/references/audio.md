# Podcast audio

Most of a brief comes from text. Some podcasts publish transcripts; a brief uses those for free. This file is for episodes that have audio only. `AUDIO` means `<this skill's folder>/scripts/audio.py`, run directly.

Default is **skip**: an episode without a transcript contributes its show notes and nothing more. Don't bring audio up unless the user picked or added a podcast themselves.

## The one question (in start, or when a podcast is added)

Run `AUDIO find` and `AUDIO estimate <workspace>` first so the question has real numbers. Then:

"<N> podcast episodes from the last 30 days have no transcript, about <H> hours. Want me to transcribe them on this computer? It's free and takes one setup: about 3 GB of downloads (a 2.3 GB model plus 650 MB of software)."

- **Yes, set it up** (Recommended)
- **No, show notes are fine**

Keep the local choice simple. If the user is connecting OpenRouter, also offer the cloud choice below once; otherwise do not list alternatives unless asked.

## Setting it up (on yes)

Run `AUDIO install` and relay its three progress lines. It does everything: ffmpeg through Homebrew if it's missing, Parakeet in a private folder (`~/.local/share/farfield/parakeet`, nothing global), the model download, and a test. It can take several minutes on a slow connection; say so before starting. Then:

1. `AUDIO use <workspace> parakeet`
2. `AUDIO transcribe <workspace> <audio URL of a recent episode that has no published transcript> --max-secs 120` and show the first two sentences, so they see it work. A clip streams only those seconds; it doesn't download the whole episode. Many shows open with an ad; if the sentences are an ad, say so rather than presenting them as the show.

If `install` fails, read its message: it says exactly what is missing (Homebrew, or Python 3.10+). Fix that one thing with them, or leave audio on skip. Never leave a half-installed state unmentioned.

## Not an Apple Silicon Mac, or another language

`AUDIO find` says `"suggested": "whisper"`. Whisper large-v3-turbo through whisper.cpp: they need `whisper-cli` and a ggml model file (`AUDIO find` lists any already on the machine). `AUDIO use <workspace> whisper --model <path>`. Parakeet covers English and about 25 European languages; anything else is also Whisper.

## Optional cloud choice when connecting OpenRouter

Ask separately: “Now that OpenRouter is connected, do you want to keep transcription local, or use a cloud model for episodes without transcripts?” Explain that cloud transcription sends the audio to OpenRouter and the provider. A yes to Twitter does not mean yes to audio uploads.

Show the current choice first as recommended; offer “Compare cloud options” and “Skip audio” alongside it. Record that the offer was answered in `audio-cloud-offer.json` so it is not repeated. No answer leaves the existing setting unchanged. On compare, use the actual selected, unread, uncached episodes and known duration to show:

| Model | Per audio hour | Example: 10 hours |
|---|---:|---:|
| Local Parakeet / Whisper | $0 API spend | $0 |
| Whisper Turbo via OpenRouter | about $0.012 | $0.12 |
| Microsoft MAI-Transcribe 2 via OpenRouter | $0.10 | $1.00 |
| ElevenLabs Scribe v2 via OpenRouter | $0.22 | $2.20 |

Rates checked 2026-11-17 against [OpenRouter's transcription catalog](https://openrouter.ai/api/v1/models?output_modalities=transcription) and model pages. Recheck before paid use. These estimate cost, not quality: no comparative accuracy test has been run. Credit fees/taxes are excluded. Unknown durations mean an incomplete estimate. Feed-only `AUDIO estimate` can overcount missing transcripts; inspect the episode pages first. An episode with a published transcript costs nothing to transcribe because it should not be transcribed.

After they choose, use `AUDIO use <workspace> openrouter --model <id> --budget <agreed dollars per run>` with `openai/whisper-large-v3-turbo`, `microsoft/mai-transcribe-2`, or `elevenlabs/scribe-v2` (budget default $1). Before sending anything, `transcribe` refuses any episode that would cost more than that budget. Use `HELPER keys --open` only if needed. Show the batch's estimated charge before authorizing it; keep it within the user's agreed audio budget and recommend a capped OpenRouter key. Setting up a provider is not blanket approval for unlimited audio. Show actual reported cost afterward; missing usage is unknown.

Existing local model preferences remain supported. For local Whisper, use `AUDIO use <workspace> whisper --model <path>`.

## During a brief

If `audio.json` is not `skip`, podcasts are read like articles, from their transcripts:

1. Right after discovery, pick the episodes worth hearing: the ones whose titles and show notes bear on `me.md`, not every episode. Skip any with a published transcript (read that instead).
2. Start their transcriptions first, before or alongside the text reading, one `AUDIO transcribe <workspace> <audio url>` per episode. Each can take several minutes.
3. Wait for them. Don't select ideas or write the brief until every started transcription has finished or failed. A transcript that arrives after the brief is wasted.
4. Read each transcript (`raw` path) like any other page. Quotes from it are checked against that file, and the brief marks them "machine transcript" because names and numbers can be wrong.

Identical audio URL, model and clip length reuse the saved transcript without downloading or paying again. A short test clip is not a complete episode. Cap: 6 hours of audio per run unless `me.md` says otherwise; say what was left out. A failed transcription is a skipped episode noted in the footer, not a failed brief.

## Unattended

Never install anything or change the audio choice in a scheduled run.
