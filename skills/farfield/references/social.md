# Optional X discovery: implementation notes

Status: researched, not integrated or live-tested. Farfield currently has no direct X collector. Its standard brief needs no extra account. A Grok model call by itself does not request X search.

[OpenRouter documents](https://openrouter.ai/docs/guides/features/server-tools/web-search) native X search for Grok 4 and later through `openrouter:web_search` with `parameters.engine: "native"` and an explicit `parameters.x_search` object. That object supports handle and date filters. Check current model support before implementation; this is a beta API. [xAI's direct API](https://docs.x.ai/developers/tools/x-search) also exposes keyword, semantic and thread search. Date windows use YYYY-MM-DD and an exclusive end date.

For a future opt-in pilot:

1. Derive two generalized queries from the user's confirmed decisions. Do not send their private context summary. Use a small explicit set of researchers/builders plus one broader question search.
2. Limit the dates to the brief's window. Prefer recent firsthand work over viral commentary. Return post URL, author, timestamp, exact excerpt and linked original. Report search coverage as partial, never “all posts.”
3. Follow linked papers, repos and essays. Posts from the same project, launch or interview are not independent evidence. Unsupported claims stay leads.
4. Require explicit opt-in and a provider-side spending limit. Search/tool limits and output token limits alone do not guarantee a dollar cap; X retrieval is billed in addition to inference. Record actual usage and costs, inspect returned citations and verify the tool really ran. No paid test has been performed yet.
5. Use a key from the user's private local configuration, never chat. Having an OpenRouter key for another feature does not enable social discovery automatically. Do not add X to default onboarding or make it a requirement for a brief.

A small pilot should compare the same project brief with and without X discovery. Keep it only if it yields useful original leads missed by the existing sources at an acceptable cost.
