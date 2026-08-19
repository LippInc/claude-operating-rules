# A suite that has never failed is not evidence

*Added 2026-08-18 after three days of turning the rules in [SKILL.md](SKILL.md) into hooks, a lint, a regression harness and telemetry. Every number here is from that work, Aug 2026, one machine, and is dated where it appears. The discipline is also one line of the rulebook itself (SKILL.md, section 6, instrument validation).*

Rules written in prose are advisory. The model reads them, agrees with them, and then omits the one parameter you cared about. So I mechanized the rules that mattered and immediately hit a second problem, which is the actual subject of this page: once a mechanism exists, its green light becomes the thing you trust, and a green light is cheap to produce by accident.

Everything below is the discipline that came out of that, stated so you can apply it in any language. It's not a framework. There is one runnable file in this repo ([`examples/example_suite.py`](examples/example_suite.py), standard library, about 80 lines) and it exists to show the shape, not to be depended on. The mechanisms themselves stay on my machine; the section "Which mechanisms earned their place" says why.

## The four-token contract

Every test a mechanism ships emits exactly one of four tokens per case:

| Token | Meaning |
|---|---|
| `PASS` | a case that should succeed, did |
| `FAIL` | a case that should succeed, didn't |
| `KNOWN-BAD-RED` | a case that should be caught, was caught; the mechanism demonstrably works |
| `KNOWN-BAD-GREEN` | a case that should be caught, wasn't; the mechanism is broken *or* the test is vacuous |

The point of the split is the third token. `PASS` only tells you the happy path runs. `KNOWN-BAD-RED` tells you the thing can actually fail when it should, which is the only evidence that its greens mean anything. A suite of nothing but `PASS` lines is a suite that has never been shown to work.

A run summarizes as counts of all four, and any `KNOWN-BAD-GREEN` fails the run, exactly like a `FAIL`.

## The exit-code ladder

Not all failures are equally bad. Ordered from ordinary to alarming (this ranks severity; it isn't a table of exit codes, and the example file uses its own):

1. A case failed. Normal. Fix it.
2. A known-bad went green. Worse than a failure: something you thought was caught isn't.
3. The self-test passed when it should have failed. Worse still: the instrument is lying, so every other result from it is now unknown.
4. Zero assertions ran. A suite that tested nothing and reported success. Python's `all([])` is `True`, JavaScript's `[].every()` is `true`, and an empty loop body is a green run.
5. The suite couldn't run at all, and something upstream treated that as "no problems found."

Rungs 3 to 5 are the ones that quietly waste weeks, and they share a shape: an absence of evidence read as evidence of absence. Rung 4 is the pure reduce-over-empty case, which leads to:

## Guard the degenerate cases explicitly

- `all([])` is `True`. An empty finding list passes every "no violations" check.
- `min([])` / `max([])` throw; a naive `try/except` around a whole check turns that into a pass.
- An empty sum is `0`, which reads like a clean measurement.
- A count-based gate ("at most 40 words", "exactly 5 bullets") passes a 3-character answer, and passes a list whose last item stops mid-sentence. Check that the last unit is complete, not just that the count is right.
- Feed every gate a deliberately degenerate input and require it to fail. Do this before you trust any green from it.

## The landing ritual

When a mechanism changes, in this order:

1. Write the known-bad first and watch it go GREEN against the *old* code. If it doesn't reproduce, you haven't found the bug you think you found.
2. Apply the fix; the known-bad goes RED.
3. Add the positive control: the ordinary case that must keep working. This is the step that catches over-firing.
4. Re-run *everything else* and compare against the previous run. Fixes break neighbours.
5. Leave a dated revert path.

Step 4 is not optional and it is not paranoia. Over two review rounds of my own mechanisms (Aug 2026), the fixes themselves introduced regressions six times that only a re-run caught, including one where a language quirk (`-and` and `-or` having equal precedence, evaluated left to right) silently disabled an unrelated rule that had been working for days. The fix was correct. The file was broken.

## Write the stop rule before the pass, not after

Adversarial review has an unbounded tail. Mine, measured: one mechanism's known-bad file went from 39 to 90 to 98 to 132 to 139 cases in three days (Aug 15 to 18, 2026), each pass finding real defects. Separately, I planted 116 deliberate bugs across my suites to see which ones their own tests would notice: 41 survived. There is no point at which this returns nothing.

So "test until it's clean" is a decision never to finish. Fix a mechanical pass mark in advance. Mine:

> suite green + one bounded re-verification round + zero unaddressed blockers in what actually ships (not zero findings anywhere).

And keep a second number honestly: what the mechanism has actually caught in production. One of mine, a guard that inspects shell commands before they run, has produced non-trivial verdicts only on its own tests and on false positives across 359 logged live events. Real accidents prevented: zero. It stays because it's cheap (replayed over 3,968 commands from my own history it would have interrupted 19, 0.48%, all legitimate) and because it writes an audit trail. But it is frozen, and it is described as a deterrent, not a safety boundary.

## Which mechanisms earned their place

Measured over the same three days, the mechanisms that *measure* paid for themselves and the one that *blocks* did not. The regression harness caught the six fix-induced regressions above. The telemetry that counts how my own fleets are actually spawned surfaced a number prose never could: by Aug 19, 2026 (77 `agent()` calls since it went live, my sessions only, probe runs excluded), `effort` was still omitted on 2 calls and `model` on 2, with the rule loaded and a warning lint running. Small, not zero, and unknown before the counter existed. The guard, as recorded above, caught nothing real, and it would not have prevented the one real data-loss incident in my record either: that command was well-formed and its glob was too wide.

The root cause is worth naming because it generalizes. The rules in the skill were incident-driven: each one was paid for by something that went wrong. The mechanization wave was gap-driven: I had noticed that other people build mechanisms and I don't. A gap analysis is not a need analysis. The test I now apply before building or keeping any mechanism: can it name the specific thing that actually went wrong, in my own record, that it would have caught? Measuring mechanisms earn their place cheaply, because they show what prose can't. Blocking mechanisms need a named catch. If you can't show one, it's insurance: price it, freeze it, call it a deterrent, and stop polishing it. The tell that this was real: the one rule my own incident did earn (print the match list before a wildcard delete) had been implemented by nothing while the elaborate guard got polished.

That is also why the hooks, the harness and the telemetry are not in this repo. They are Windows PowerShell with my absolute paths in them, and the one that blocks has caught nothing real. Shipping a mechanism to strangers that I froze for that reason is the wrong move; describing the discipline so you can build your own is the honest one.

## Validate the reviewer too

If you use AI agents to review your mechanisms, the reviewers need the same treatment. Plant a known defect in a copy of the file under review and see whether the review finds it. The protocol matters more than the score: a catch counts only when the review names the planted line, and the plants are written down before the review runs so a lucky unrelated finding can't be counted afterwards. I've run it in three review sessions so far, ten planted defects in all, each caught by at least one reviewer; one reviewer quoted the sabotaged line back verbatim. Ten for ten is a small n and, by this page's own rule, a perfect score is a smell: the next plants need to be harder than the last. An unvalidated reviewer's clean bill of health is worth what an unvalidated suite's green is worth.

---

*Platform notes, dated and specific to my own setup (Windows, PowerShell 5.1, Claude Code CLI 2.1.226, Aug 2026); do not read these as general claims. The docs say a hook that exits 2 blocks. On my setup, a hook registered with `"shell": "powershell"` and an `& '<path>'` command did not: PowerShell's `-Command` invocation turns the script's `exit 2` into process exit 1, Claude Code logs a non-blocking error, and the tool call proceeds. Blocking required emitting a JSON decision on stdout. I had documentation asserting the opposite for days, which is how a blocking mechanism came to never block. Verify the equivalent on your own version rather than trusting this paragraph.*
