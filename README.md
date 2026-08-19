# Operating rules for running Claude Code at scale. Measured, not vibed.

These are the operating rules I load into every Claude Code session. They exist because of a number I didn't expect: on the first build where I added up the tokens, the interactive main loop looked like nearly all of the cost and the subagent fleet looked cheap. Before announcing this repo anywhere I re-measured that across every corpus still on my disk, and the number moved. The split isn't a constant: my attended builds run roughly 70/30 driver-heavy, and my unattended overnight fleet runs invert it to about 33/67. What the original headline got wrong, and why, is in the [update below](#update-2026-08-14-i-re-measured-the-headline).

The advice I'd read mostly optimized the fleet. My own numbers keep saying the driver, the main loop itself, is the bigger bill whenever I'm in the loop, so I started writing rules down and kept the ones that survived real work. About two months of heavy daily fleet use went into these (June through August 2026), measured as I went. I wrote the rules and I ran the measurements, all of it on one machine and one plan, so by the claim-flagging rule this skill itself ships (SKILL.md, section 6), most numbers here are what the skill would call SINGLE-SOURCE: one source, me. The driver/fleet split is the exception now, re-measured across 36 fleet-bearing sessions. Re-measure on your own setup before trusting any of it.

What's here: [SKILL.md](SKILL.md) is the rulebook, installable as a Claude Code skill. This README is the writeup of the measurements behind it, plus a log of the rules failing, including my own routing rule failing three times in three different ways, and now the README's own original headline. [MECHANISMS.md](MECHANISMS.md) is the part I added after mechanizing these rules and discovering that the mechanisms' own green lights were the next thing to stop trusting. It's not a framework or an agent pack: no hooks, no agents, nothing that runs inside your Claude Code session. The single runnable file is [`examples/example_suite.py`](examples/example_suite.py) - standard library, ~50 lines, and it ships with a `--break` flag so you can watch it fail on purpose.

## Where the cost sits depends on the shape of the work

Re-measured 2026-08-14 across every session corpus still on disk: cost-weighted (tokens times each model's price, cache reads at their own rate), deduplicated by message.id, counting only sessions that actually ran a fleet, since a session with no subagents is 100% driver by construction and says nothing about fleets.

| Corpus | Fleet-bearing sessions | Driver share (cost) | Driver share (raw tokens) |
|---|---|---|---|
| Hackathon build, Jul 2026 | 3 | 70% | 67% |
| Scheduling-app build, Jul-Aug 2026 | 13 | 66% | 60% |
| Strategy/research project, Jun-Aug 2026 | 20 | 47% | 33% |

The cost column assumes my orchestrator model prices at twice the top public tier (unverified; worth 10-18 points either way), which is why the price-agnostic raw-token column rides along. Within the builds, per-session driver share runs 43% to 80%, median around 55%. The third corpus decomposes: ordinary interactive strategy sessions run about 59% driver, and the three real unattended overnight fleet runs in it average about 33%. The rule of thumb that survives all of it: the more attended the work, the more the driver is the bill. My original 90/10 claim came from the far pole of that spectrum, and its transcripts are gone.

What didn't move: most of the driver's cost is not thinking, it's cache reads, roughly two-thirds of driver cost on the builds, the price of carrying a big context and re-reading it every turn. So the cheap win is still getting reference reading out of the driver: hand the corpus to a subagent that reads it and returns conclusions. And the lever I still don't pull is shrinking the driver's context mid-task, because forced compaction degrades output quality faster than it saves cost, and quality is why you run a big model in the first place.

### Update, 2026-08-14: I re-measured the headline

The first version of this README opened: "the whole subagent fleet came to about 10% of my token burn. The interactive main loop was the other 90%," resting on two July builds ("78% of spend on one and ~90% on the other"). Applying this repo's own fresh-over-cached rule before announcing it anywhere, I re-ran the measurement. The 90/10 build's transcripts are purged and can't be re-run; treat that number as unreproducible. The 78% build re-measures at 72% pooled, 70% fleet-bearing.

Three untracked choices moved the old numbers more than data did. Dedup of compaction re-logging: the long-lived driver session re-logs its history far more often than any short-lived subagent transcript, so skipping dedup inflates the driver side specifically (the same corpus reads 82% with dedup off). The assumed price of my orchestrator model. And counting fleet-less sessions, which are 100% driver by construction, in a claim about fleets. The defect this README warns about in the cost-audit method below is the defect that produced its own original headline. One related original claim, that 70% of the driver's file reads (336 of 480) were reference files it never edited, also comes from the purged corpus and can't be re-checked; it stands as recorded, single-source, unverifiable.

## Sonnet tied Opus on legwork at 40% of the cost (n=1)

Blind A/B, July 2026. Same tasks, same effort level on both sides, outputs stripped of model names, graded against a rubric written before I saw any output. On my task shapes (research fan-outs, structured extraction, adversarial fact-checking) Sonnet tied or beat Opus. That's a single run per model per shape, so treat it as a hypothesis with receipts rather than a result.

It's been my enforced default since: legwork runs on Sonnet, and picking Opus for legwork needs a stated reason. The boundary that survived use is who sets the frame. If the spec or rubric is already decided and the agent executes inside it, Sonnet. If the agent has to set the frame itself (design, trade-offs, adjudication), or a quiet error would poison a decision downstream, Opus.

## Raising Haiku's effort made its fabrications more convincing

Same A/B: Haiku fabricated facts and product names, and at high effort it fabricated more convincingly, complete with invented sources, quotes nobody wrote, and false "VERIFIED" labels. It got one same-day retest. Same direction both times. (One caveat: effort requests at unsupported levels downgrade silently rather than erroring, so check what level a run actually got before blaming it. The fabrication itself is not in doubt.)

Haiku keeps a narrow slot in my rules: trivially simple lookups where nothing downstream trusts its facts. And "raise the effort to rescue a cheap model" is banned outright. On this evidence it buys you better-decorated fabrications.

## The rules

The full rulebook is [SKILL.md](SKILL.md). In one screen:

| # | Rule | Gist |
|---|---|---|
| 1 | Substrate | Fleets run on the Workflow tool with model and effort set explicitly on every `agent()` call. An ad-hoc Agent-tool call can't set effort, so it inherits the session's, which is max exactly when you're working hard. Standing custom agents can pin both in frontmatter. |
| 2 | Concurrency | Find your throughput ceiling once, then hold it yourself (mine is 8). Idle concurrency is fine; a throttled fleet is not. Big fan-outs get one agent told to refute the frame itself, because scale explores a frame and never breaks one. |
| 3 | Model tiering | Cheapest model that can't be wrong: trivial lookups on the fast tier, legwork and in-frame execution on the mid tier (the default), frame-setting judgment on the top tier, project-deciding calls on the reserve. |
| 4 | Effort | A second dial inside the model. Set it per agent, never let it inherit, never raise a cheap tier's effort to rescue quality, and know that unsupported levels downgrade silently. |
| 5 | Reserve tier | Strongest model at top effort, for exactly two cases: calls that decide the project, and orchestrators whose plan multiplies across everyone they spawn. If everything is critical, nothing is. |
| 6 | Doctrine | Every agent prompt carries single-writer (subagents research and verify, only the orchestrator writes), honesty over scaffolding ("nothing to fix" is a valid finding), fresh-over-cached facts, and an evidence flag on every load-bearing claim. |
| 7 | Spawn checklist | Six questions before any agent spawns, plus a lane declaration: if any work is meant for a different lane or tier than the script's default, say so in one line before spawning. |
| 8 | Deadline work | On "work until X" mandates the duration is the deliverable. Agents have no clock. Check it explicitly, say the absolute deadline back, and treat an empty queue as a milestone, not a stop. |

## Run the measurements yourself

My numbers will rot (see Limits). The methods won't.

Blind same-effort A/B. Pick a few task shapes from your real work, not benchmarks. Run each on both models at the same effort level, otherwise you're measuring effort. Strip model identifiers, shuffle, grade against a rubric you wrote beforehand. Write your n down and let it be small. One limitation to copy better than I did: I never separately confirmed the delivered effort level on each run, and levels downgrade silently, so check yours.

Cost audit. Session transcripts are JSONL under `~/.claude/projects/<project>/`; the main session logs to one file and each subagent to its own sidecar file, which is what makes the driver-versus-fleet split possible. Two things silently corrupted my first attempt: compaction re-logs history, so the same message.id recurs and naive token sums came out about 4x too high (dedup by id); and nothing meaningful shows up until you split driver vs. subagents and cache reads vs. output. The percentages I quote are cost-weighted (tokens times each model's price, with cache reads at their own rate), not raw token shares. Two more divisor guards this repo's own re-measurement taught me: exclude sessions that ran no fleet from any fleet-share claim, since they're 100% driver by construction, and drop empty session shells before computing ranges or medians, or a 0/0 division quietly poisons the statistics.

Instrument validation. Before trusting any grader, gate, or analysis script, feed it a known-bad input and require a failure. No demonstrated red means the instrument is unproven, whatever its greens say. A perfect score on a non-trivial corpus is a smell, not a comfort.

Concurrency ceiling. Raise parallelism until you actually see 429s and backoff, then hold below that with margin; expect it to surface as agents stalling and retrying rather than a clean error in front of you. Mine landed at 8; yours depends on plan and workload. Don't confuse this ceiling with the platform's spawn guards (20 concurrent Agent-tool subagents by default per the docs as of Aug 2026; Workflow runs cap at 16, fewer on weak CPUs), which stop spawns but say nothing about throttling. Your plan's rolling token budget is a third thing again, and you can exhaust that just fine at concurrency 1.

## Where the rules failed

This is the section I wanted to find in other people's rules and mostly didn't.

The routing rule failed three times, differently each time. I keep a rule that routes cheap grind work to a cheaper lane (mine is an off-quota third-party lane, but the same failure hits any tier split, including a plain Haiku/Sonnet/Opus one). First failure: the rule was loaded and I still didn't route anything to it under deadline pressure. The diagnosis wasn't forgetting, it was reluctance. Nobody rips out a working setup mid-race, so the fix was making the cheap lane part of normal work instead of an emergency measure. Second failure: the rule now fired at session start and still produced zero delegations, because the routing was being re-derived from scratch for every fleet, at the worst possible moment. Fix: pre-decide the routing in a template. Third failure, the interesting one: the lane decision was made correctly in prose at plan time, and then the fleet got written as a Workflow script whose model enum had no option for the planned lane. The band silently became the default model, and about 66% of that fleet's token flow went down the wrong lane after the right decision had already been made. A prose decision that isn't representable in the API you execute through doesn't exist. The surviving fix is in the skill now: declare the lane split in one line before anything spawns.

The cheap lane's concurrency rule started wrong in the other direction. Its first version said "max 2", copied from reports that turned out to measure a different regime (one client's internal parallelism, not independent processes). Measured properly, 4 parallel calls cost 1.43x one call's latency, and that ceiling moved to 4-6. Different rule from the 8 above, same lesson: check what regime a borrowed number was measured in before adopting it.

And my own instruments have committed the exact defect they were built to catch. Verification gates passed degenerate inputs (a 3-character answer sailed through a "40 words or less" check; count-valid bullet lists shipped ending mid-thought) until feeding every gate a known-bad first became the rule. It's now the first thing I check, including on this repo's own claims. That's where the SINGLE-SOURCE label in the intro comes from.

Mechanizing the rules produced a fresh class of failure: the mechanisms' own greens. I turned the rules above into hooks, a lint and a regression harness, and then had to build a discipline for not trusting them - that discipline is [MECHANISMS.md](MECHANISMS.md). Three entries worth recording here.

A blocking mechanism that never blocked. I had a hook meant to stop a destructive command, documented as blocking by returning a non-zero exit code, and days of notes asserting it worked. On my setup, registered the way I had registered it, the exit code is remapped before anything acts on it, and the tool call proceeded every time. Blocking actually required emitting a JSON decision on stdout. Nothing in the code was wrong; the mechanism just wasn't connected to any consequence, and only a live smoke test that tried to run a real command found it.

A cleanup instrument that misread its own input in the reassuring direction. A script that flags stale notes for re-verification treats notes marked closed as exempt. Its "is this closed" test was a whole-line match, and on my real data 12 of the 17 notes it called closed were live - so those 12 were silently exempted from the staleness check they most needed. It reported a clean sweep while quietly skipping the work.

Adversarial review has no natural end, and its fixes bite back. Two escalating review rounds over these mechanisms took one guard's known-bad file from 39 to 139 cases in three days, each round finding real defects. In six of those rounds the fixes themselves introduced regressions - once because two logical operators in the language I wrote it in have equal precedence and evaluate left to right, which silently switched off a neighbouring rule that had worked for days. Separately, I planted 116 deliberate bugs across my suites to see which their own tests would notice: 41 survived. The lesson isn't "review more", it's that a stop rule has to be fixed in advance, because "test until it's clean" can't terminate. And the counterweight I now write down next to any mechanism: that guard, in 359 logged events, has produced non-trivial verdicts only on its own tests and on false positives. Real accidents prevented: zero. It's frozen, it's described as a deterrent rather than a safety boundary, and it stays only because it's cheap.

The newest entry in this log is the README's own original headline. The 90/10 split survived two multi-agent review rounds and a full register rewrite, and fell to the first actual re-measurement (see the update above). Reviews check what a claim says; only measurement checks what it measures.

## Limits

One person, one Windows machine, one plan tier, one working style. n=1 per cell on the model A/B (the Haiku result got one retest); the driver/fleet split rests on 36 fleet-bearing sessions across three corpora, re-measured 2026-08-14. Everything is dated July and August 2026, and model names churn, so read the tiers by role (fast, mid, top, reserve) and treat the current names as examples. The Workflow tool's per-call model and effort options, and its `parallel()` primitive, exist in my install (I've run all of them on v2.1.226) but aren't in the public docs as of this writing; the docs even point at an SDK reference page that has no Workflow entry yet. Verify in your version. Versioning: the measurements are dated where they appear and I don't retro-edit them - corrections land as dated update sections, the way the 2026-08-14 re-measurement did. The rulebook and MECHANISMS.md may gain material as I learn things; each change says what changed and when. Replication results from other people get folded into the README, same as before. Not affiliated with Anthropic.

## Install

```
git clone https://github.com/lippinc/claude-operating-rules
```

Copy the folder containing SKILL.md to `~/.claude/skills/claude-operating-rules/`. Just SKILL.md is enough, and the folder name is what identifies the skill (the frontmatter name is cosmetic for personal skills). It loads when the model matches your request against its description, or invoke it directly with `/claude-operating-rules`. If `~/.claude/skills/` didn't exist on your machine before this, restart Claude Code once so it starts watching the new directory. The file also reads fine as plain prose.

## License

MIT, Martin Lipp ([lippinc](https://github.com/lippinc)). If you replicate any measurement here, same result or opposite, an issue with your numbers and your n is the most useful thing you can send.
