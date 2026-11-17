# Optional Twitter / X discovery

Offer this once after the four setup choices, or when the user asks about social sources. Use the host's question UI:

“Want to include Twitter/X? It can find firsthand posts related to your work. It needs an OpenRouter account and credits. A small pass is estimated at $0.15–$0.75 per brief, roughly $1–$4 a month for weekly briefs. That is an estimate, not a spending cap.”

- Not now (Recommended): continue with the existing sources.
- Add Twitter/X: explain the budget and help connect OpenRouter.

Record the answer in `<workspace>/social.json`. No sets `enabled: false`; don't offer again unless asked. No answer leaves it off. A key already present for transcription is not consent to social search. Do not block the first brief on this optional connection.

## If yes

Use a dedicated key with a $5 monthly limit (or the user's explicitly chosen limit) in [OpenRouter's key settings](https://openrouter.ai/settings/keys). The user creates the account, funds it and sets the limit. Explain that queries go to OpenRouter and its model provider. Open `HELPER keys --open` for them to paste the key locally, never in chat. Verify presence using `HELPER keys`, never print its value.

Write `social.json` with `enabled: true`, `monthly_limit_usd: 5`, and optionally `handles: [...]` only after they have agreed. If a total rather than monthly key limit is available, that stricter limit is fine. Do not claim a limit has been configured without verification. The adapter checks the key's actual limit before sending a paid request.

Then offer the separate cloud transcription choice in [audio.md](audio.md). Connecting OpenRouter never changes audio settings by itself.

## During a brief

`SOCIAL` means `<skill>/scripts/social.py` via python3. Run `SOCIAL estimate` for the recorded price assumptions. Derive one or two short generalized research questions from confirmed decisions; do not send private project notes, customer names or the context summary. Respect source mutes, including named authors, when choosing handles and candidates.

Run `SOCIAL search <workspace> "<generalized questions>" --since YYYY-MM-DD --until YYYY-MM-DD`. The end date is exclusive, the window is at most 31 days. `--dry-run` builds the request without credentials or spending. A real run requires explicit opt-in and a bounded provider key. One attempt per UTC day prevents accidental repeat charges; reuse the saved result. A timed-out request is not automatically retried because it may have incurred cost.

Read the returned result file. Inspect tool activity and citations; a generated answer alone does not prove an X search occurred. If there is no evidence of retrieval, mark it unverified and do not include claims as checked evidence. Follow linked papers, repos and articles. Store the original URL, author, date and exact excerpt only after checking it. All X coverage is partial; popularity is not relevance. Related posts from one launch are one evidence chain. Store actual usage/cost when reported; missing cost is unknown, not zero.

## Cost assumptions, checked 2026-11-17

A small pass: 20 posts, 2 profile lookups, 10k input and 1k output tokens, 1 web search: about $0.15. A larger pass: 100 posts, 10 profiles, 50k input and 3k output tokens, 2 web searches: about $0.73. These are hypothetical quantities, not a measured workload. Search loops can exceed them. Native Grok ignores `max_results` and `max_uses`, so those are not spending controls. Credit purchase fees/taxes are excluded.

Rates: $0.005/post, $0.01/profile; Grok 4.7 $2/million input and $6/million output tokens; web search $0.005/call. Verify current rates before connecting a user. [Search pricing and controls](https://openrouter.ai/docs/guides/features/server-tools/web-search), [model catalog](https://openrouter.ai/api/v1/models), [key budget API](https://openrouter.ai/docs/api/api-reference/api-keys/get-current-api-key).

The adapter is tested with mocked responses. A paid end-to-end run has not yet been verified. Report that honestly if it fails; continue the ordinary brief without X.
