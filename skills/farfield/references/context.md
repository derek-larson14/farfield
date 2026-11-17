# Keep a useful picture of the work

`me.md` is the user's corrected description, preferences and allowed context paths. `state/context.md` is a short working summary for the agent, refreshed before each brief. Neither belongs in the distributed skill or a shared feed.

During setup, use the conversation and the permitted project files to identify one to three active projects, their current stage, constraints and decisions. Prefer a current project overview or recent decision note over a pile of old documents. Read at most five files per project and only within the paths the user allowed. Skip secrets and dependency folders. Don't scan other projects or connected services just because access exists.

Write at most 500 words in `state/context.md`, dated, with:

- Each project's name, intended outcome and current stage.
- Its next unresolved decision or bottleneck, and what new evidence would change the approach.
- Approaches already tried or understood; avoid rediscovering them.
- Supporting local paths and document dates, or the dated user statement. Distinguish confirmed facts from inferences and stale information.
- Two or three research questions derived from those decisions, plus one adjacent mechanism worth exploring.

At each brief, read `me.md` and the previous context summary first, then check permitted files for changes. Update the derived summary with supported changes. The user's explicit corrections override inference. Never silently rewrite `me.md` or turn a speculative interpretation into a new goal. If work appears to have changed, label it tentative, propose a correction after the brief, and use the confirmed goals until corrected. In unattended mode record the uncertainty without asking a question.

Filter each candidate by asking: which named decision could this affect, what is new relative to what they already know, and why now? If the answer is only “they work in AI,” it is too generic. A surprising connection needs a plausible mechanism and a small way to check it, not a motivational analogy. Relevant contrary evidence matters too.

Search with generalized technical questions. Do not send private customer names, confidential plans or raw project notes to search engines or optional external APIs. Read the summary locally with the user's existing model provider. Link it after the first brief as “My working picture” so they can correct it.
