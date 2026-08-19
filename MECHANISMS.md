# A suite that has never failed is not evidence

Rules written in prose are advisory. The model reads them, agrees with them, and then omits the one parameter you cared about. So I mechanized the rules that mattered — hooks, a lint, a regression harness, telemetry — and immediately hit a second problem, which is the actual subject of this page:

**Once a mechanism exists, its green light becomes the thing you trust. And a green light is cheap to produce by accident.**

Everything below is the discipline that came out of that, stated so you can apply it in any language. It is not a framework. There is one runnable file in this repo ([`examples/example_suite.py`](examples/example_suite.py), standard library, ~50 lines) and it exists to show the shape, not to be depended on.

## The four-token contract

Every test a mechanism ships emits exactly one of four tokens per case:

| Token | Meaning |
|---|---|
| `PASS` | a case that should succeed, did |
| `FAIL` | a case that should succeed, didn't |
| `KNOWN-BAD-RED` | a case that **should be caught**, was caught — the mechanism demonstrably works |
| `KNOWN-BAD-GREEN` | a case that should be caught **wasn't** — the mechanism is broken *or* the test is vacuous |

The point of the split is the third token. `PASS` only tells you the happy path runs. `KNOWN-BAD-RED` tells you the thing can actually fail when it should — which is the only evidence that its greens mean anything. A suite of nothing but `PASS` lines is a suite that has never been shown to work.

A run summarizes as counts of all four, and **any `KNOWN-BAD-GREEN` fails the run**, exactly like a `FAIL`.

## The exit-code ladder

Not all failures are equally bad. Ordered from ordinary to alarming:

1. **A case failed.** Normal. Fix it.
2. **A known-bad went green.** Worse than a failure: something you thought was caught isn't.
3. **The self-test passed when it should have failed.** Worse still — the instrument is lying, so every other result from it is now unknown.
4. **Zero assertions ran.** A suite that tested nothing and reported success. `all([])` is `True` in most languages; an empty loop body is a green run.
5. **The suite couldn't run at all** and something upstream treated that as "no problems found."

Rungs 3–5 are the ones that quietly waste weeks, and they are all *reduce-over-empty* bugs. Which leads to:

## Guard the degenerate cases explicitly

- `all([])` is `True`. An empty finding list passes every "no violations" check.
- `min([])` / `max([])` throw; a naive `try/except` around a whole check turns that into a pass.
- An empty sum is `0`, which reads like a clean measurement.
- A count-based gate ("at most 40 words", "exactly 5 bullets") passes a 3-character answer, and passes a list whose last item stops mid-sentence. Check the **last unit is complete**, not just that the count is right.
- Feed every gate a deliberately degenerate input and require it to fail. Do this **before** you trust any green from it.

## The landing ritual

When a mechanism changes, in this order:

1. **Write the known-bad first and watch it go GREEN** against the *old* code. If it doesn't reproduce, you haven't found the bug you think you found.
2. Apply the fix; the known-bad goes RED.
3. Add the **positive control** — the ordinary case that must keep working. This is the step that catches over-firing.
4. Re-run *everything else* and compare against the previous run. Fixes break neighbours.
5. Leave a dated revert path.

Step 4 is not optional and it is not paranoia. Across two review rounds of my own mechanisms, **six rounds of fixes introduced regressions that only a re-run caught** — including one where a language quirk (`-and` and `-or` having equal precedence, evaluated left to right) silently disabled an unrelated rule that had been working for days. The fix was correct. The file was broken.

## Write the stop rule before the pass, not after

Adversarial review has an unbounded tail. Mine, measured: one mechanism's known-bad file went **39 → 90 → 98 → 132 → 139 cases in three days**, each round finding real defects. Separately, I planted **116 deliberate bugs** across my suites to see which ones their own tests would notice: **41 survived.** There is no point at which this returns nothing.

So "test until it's clean" is not a stopping condition — it is a decision never to finish. Fix a mechanical pass mark *in advance*. Mine:

> suite green + one bounded re-verification round + zero unaddressed blockers **in what actually ships** — not zero findings anywhere.

And keep a second number honestly: **what the mechanism has actually caught in production.** One of mine — a guard that inspects shell commands before they run — has, across 359 logged events, produced non-trivial verdicts only on its own tests and on false positives. Real accidents prevented: zero. It stays, because it costs 0.48% interruptions on a 3,968-command corpus and it writes an audit trail. But it is frozen, and it is described as a deterrent, not a safety boundary. **A mechanism you cannot show a catch for is insurance, and insurance should be priced, not polished.**

## Validate the reviewer too

If you use AI agents to review your mechanisms, the reviewers need the same treatment. Plant a known defect in a copy of the file under review and see whether the review finds it. I've done this four times; four were caught, one of them quoted the sabotaged line back verbatim. An unvalidated reviewer's clean bill of health is worth what an unvalidated suite's green is worth.

---

*Platform notes, dated and specific to my own setup (Windows, PowerShell 5.1, Claude Code CLI 2.1.226, Aug 2026) — do not read these as general claims: a hook registered with `"shell": "powershell"` and an `& '<path>'` command does **not** block on `exit 2`; the exit code is remapped and the tool call proceeds. Blocking required emitting a JSON decision on stdout. I had documentation asserting the opposite for days, which is how a blocking mechanism came to never block. Verify the equivalent on your own version rather than trusting this paragraph.*
