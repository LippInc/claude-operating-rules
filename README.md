# Operating rules for running Claude Code at scale. Measured, not vibed.

[![example suite](https://github.com/lippinc/claude-operating-rules/actions/workflows/example-suite.yml/badge.svg)](https://github.com/lippinc/claude-operating-rules/actions/workflows/example-suite.yml)

These are the operating rules I load into every Claude Code session. They exist because of a number I didn't expect: on the first build where I added up the tokens, the interactive main loop looked like nearly all of the cost and the subagent fleet looked cheap. Before announcing this repo anywhere I re-measured that across every corpus still on my disk, and the number moved. The split isn't a constant: on raw tokens my attended builds ran 60 to 67% driver, and my unattended overnight fleet runs inverted that. What the original headline got wrong, and why, is in the [update below](#update-2026-08-14-i-re-measured-the-headline), and a second correction to the same table, from 2026-10-03, is [right under it](#update-2026-10-03-the-cost-column-understated-the-driver).

The advice I'd read mostly optimized the fleet. My own numbers keep saying the driver, the main loop itself, is the bigger bill whenever I'm in the loop, so I started writing rules down and kept the ones that survived real work. About two months of heavy daily fleet use went into the first version (June through August 2026), measured as I went; the October revision followed a new model generation and a second A/B. I wrote the rules and I ran the measurements, all of it on one machine and one plan, so by the claim-flagging rule this skill itself ships (SKILL.md, section 6), most numbers here are what the skill would call SINGLE-SOURCE: one source, me. The driver/fleet split is the exception, re-measured across 36 fleet-bearing sessions. Re-measure on your own setup before trusting any of it.

What's here: [SKILL.md](SKILL.md) is the rulebook, installable as a Claude Code skill. This README is the writeup of the measurements behind it, plus a log of the rules failing, including my own routing rule failing three times in three different ways, and the README's own original headline. [MECHANISMS.md](MECHANISMS.md) is the part I added after mechanizing these rules and discovering that the mechanisms' own green lights were the next thing to stop trusting. It's not a framework or an agent pack: no hooks, no agents, no code that executes in your Claude Code session. The single runnable file is [`examples/example_suite.py`](examples/example_suite.py), standard library, about 80 lines, and it ships with `--break` and `--vacuous` flags so you can watch it fail on purpose, both of which the CI requires to fail.

## Where the cost sits depends on the shape of the work

Re-measured 2026-08-14 across every session corpus still on disk: cost-weighted (tokens times each model's price, cache reads at their own rate), deduplicated by message.id, counting only sessions that actually ran a fleet, since a session with no subagents is 100% driver by construction and says nothing about fleets.

| Corpus | Fleet-bearing sessions | Driver share (cost) | Driver share (raw tokens) |
|---|---|---|---|
| Hackathon build, Jul 2026 | 3 | 70% | 67% |
| Scheduling-app build, Jul-Aug 2026 | 13 | 66% | 60% |
| Strategy/research project, Jun-Aug 2026 | 20 | 47% | 33% |

The cost column prices my orchestrator model at twice the top public tier. When I ran the numbers that was an assumption worth 10-18 points either way; the public price list confirms it exactly (Fable 5 at $10/$50 per MTok against Opus 5 at $5/$25, both with cache reads at the standard 10%). Two other weights in that column were wrong, and correcting them raises the driver's share (the 2026-10-03 update below). The price-agnostic raw-token column rides along anyway. Within the builds, per-session driver share runs 43% to 80%, median around 55% (that range covers the scheduling build only; the 2026-10-03 update corrects it). The third corpus decomposes: ordinary interactive strategy sessions run about 59% driver, and the three real unattended overnight fleet runs in it average about 33%. The rule of thumb that survives all of it: the more attended the work, the more the driver is the bill. My original 90/10 claim came from the far pole of that spectrum, and its transcripts are gone.

What didn't move: most of the driver's cost is cache reads, roughly two-thirds of driver cost on the builds and nearly all of its raw tokens, the price of carrying a big context and re-reading it every turn. So the cheap win is still getting reference reading out of the driver: hand the corpus to a subagent that reads it and returns conclusions. And the lever I still don't pull is shrinking the driver's context mid-task: in my experience, and I have not measured this, forced compaction degrades output quality faster than it saves cost, and quality is why you run a big model in the first place.

### Update, 2026-08-14: I re-measured the headline

The first version of this README opened: "the whole subagent fleet came to about 10% of my token burn. The interactive main loop was the other 90%," resting on two July builds ("78% of spend on one and ~90% on the other"). Applying this repo's own fresh-over-cached rule before announcing it anywhere, I re-ran the measurement. The 90/10 build's transcripts are purged and can't be re-run; treat that number as unreproducible. The 78% build re-measures at 72% pooled, 70% fleet-bearing.

Three untracked choices moved the old numbers more than data did. Dedup of compaction re-logging: the long-lived driver session re-logs its history far more often than any short-lived subagent transcript, so skipping dedup inflates the driver side specifically (the same corpus reads 82% with dedup off). The assumed price of my orchestrator model. And counting fleet-less sessions, which are 100% driver by construction, in a claim about fleets. The defect this README warns about in the cost-audit method below is the defect that produced its own original headline. One related original claim, that 70% of the driver's file reads (336 of 480) were reference files it never edited, also comes from the purged corpus and can't be re-checked; it stands as recorded, single-source, unverifiable.

### Update, 2026-10-03: the cost column understated the driver

Re-checking the price list for the October revision, I found that the script behind the cost column weighted two model families wrong. It priced Sonnet 5 at $3/$15 per MTok, the price it was then scheduled to move to; it listed at $2/$10 throughout, and the increase never happened. And it priced Opus 4.8 at $15/$75, the retired Opus 4.1's price, where every Opus from 4.5 through 5 lists at $5/$25. The Fable weight above was right. Most of the mispriced calls were subagents, so the table overcharged the fleet and understated the driver.

I re-priced every session from that measurement that is still on disk and unchanged, meaning the August weights reproduce its August figures to the cent: 11 of the 13 scheduling-app sessions and 12 of the 20 strategy sessions. The others are gone or no longer reproduce, so I left them out rather than guess. The hackathon row's two big sessions are among the gone; its third session survives and reproduces (84% under both weights, since it ran a single model), which is too little to restate the row, so that row stands as recorded.

| Corpus (sessions re-priced) | Driver share (cost), August weights | Driver share (cost), list prices | Driver share (raw tokens) |
|---|---|---|---|
| Scheduling-app build (11 of 13) | 68% | 80% | 65% |
| Strategy/research project (12 of 20) | 43% | 48% | 31% |

Raw-token shares don't use prices (they differ from the table above only because these rows cover the re-priced sessions alone), and the finding's direction holds and gets stronger: the more attended the work, the more the driver is the bill. The paragraph under the table had a second slip: its per-session range ("43% to 80%, median around 55%") covered only the scheduling build. Across both builds it was 43% to 84%, median 63%, and at list prices the re-priced scheduling sessions run 52% to 90%, median 78%. Same lesson as the first update, one layer down: the reviews checked the column's arithmetic and the one price I had flagged as an assumption, and nobody checked the two I hadn't.

## Sonnet tied Opus on legwork at 40% of the list price (n=1)

Blind A/B, July 2026. Same tasks, same effort level requested on both sides (delivery unconfirmed, see the methods section below), outputs stripped of model names, graded against a rubric written before I saw any output. On my task shapes (research fan-outs, structured extraction, adversarial fact-checking) Sonnet tied or beat Opus. The 40% is the list-price ratio (Sonnet 5 at $2/$10 per MTok to Opus 4.8's $5/$25, the Opus of the day; Opus 5 lists the same), not a measured bill. And it's a single run per model per shape, so treat it as a hypothesis with receipts rather than a result.

It's been my enforced default since: legwork runs on Sonnet, and picking Opus for legwork needs a stated reason. Since October that includes hands-on coding (the October A/B below). The boundary that survived use is who sets the frame. If the spec or rubric is already decided and the agent executes inside it, Sonnet. If the agent has to set the frame itself (design, trade-offs, adjudication), review something final, or a quiet error would poison a decision downstream, Opus.

## Haiku fabricated in both runs, and the "high effort" run was the more convincing one (n=2)

Same A/B: Haiku fabricated facts and product names, complete with invented sources, quotes nobody wrote, and false "VERIFIED" labels. It got one same-day retest with the effort setting raised from low to high, and the second run fabricated more convincingly than the first. Read that as two runs, not a dial: effort requests at unsupported levels fall back quietly rather than erroring, and the docs' effort-support table, as of Aug 2026, doesn't list Haiku 4.5 at all, so the "high" run may have received the same effort as the "low" one. What isn't in doubt is the fabrication, in both runs.

Haiku keeps a narrow slot in my rules: trivially simple lookups where nothing downstream trusts its facts. "Raise the effort to rescue a cheap model" stays banned in my rules, but call that policy, not measurement: on the current fast model the dial may not exist, and the one time I turned it the output got better-decorated, not better.

### Update, 2026-08-19: the Haiku heading overclaimed

This section was first published under the heading "Raising Haiku's effort made its fabrications more convincing", which states a causal effect of a dial. Checking the claim against the model-config docs for this release showed Haiku 4.5 absent from the effort-support table, which means the effort I asked for on the retest may never have been applied. The observation (two fabricating runs, the second more convincing) stands as recorded; the causal framing is withdrawn. Same rule as the headline above: what I measured stays, what I inferred beyond it goes.

## Sonnet 5.5 matched Opus 5.5 on coding for less, and lost on critique and decisions (n=1 to 4)

A new generation shipped in late September, so on 2026-10-01 I re-ran the comparison: Sonnet 5.5 at high against Opus 5.5 at medium, high and xhigh. Three packets from my own work: a coding task (extend a module until five acceptance tests pass, two runs per config), a critique task (four artifacts, two carrying 12 planted defects between them and two clean controls, which together held three real defects nobody planted), and a decision brief graded on a 12-point rubric (four runs for each config except xhigh, which got one). 67 headless runs in all, counting the graders' runs, on a clean config with no CLAUDE.md, hooks or plugins, the resolved model checked on every run, and both graders also scored a known-bad answer in the same batch (1 of 12 with each). Cost is the CLI's own API-equivalent figure, not a bill.

| Config | Coding: tests, cost, time (2 runs) | Critique: planted caught, real unplanted caught (of 3) | Decision brief: mean score of 12 |
|---|---|---|---|
| Sonnet 5.5 high | 10/10, $0.27, 73 s | 12/12, 1 of 3 | 11.0 |
| Opus 5.5 medium | 10/10, $0.44, 80 s | 12/12, 2 of 3 | 11.4 |
| Opus 5.5 high | 10/10, $0.64, 127 s | 12/12, 3 of 3 | 12.0 |
| Opus 5.5 xhigh | 10/10, $1.14, 254 s | 12/12, 2 of 3 | 12 (one run) |

On coding every config passed every test, and Sonnet was the cheapest, at about 60% of Opus-at-medium's cost, and the fastest, so hands-on coding moved to the mid tier. On critique, Sonnet caught every planted defect but missed a real contradiction that every Opus config caught. On the decision brief, two of Sonnet's four runs gave a confident go without leaving the call to the human, Opus at medium lost points on three of its four runs, two of them for unsupported figures (one wrong number, one unsourced benchmark), and Opus at high was perfect on all eight grades. Opus at xhigh bought nothing measurable over high, at up to about twice the cost and time. So: the mid tier codes at high, the top tier critiques final work and decides at high, and xhigh is kept for the long-lived seats. One to four runs per cell on packets near the ceiling: a lead, not a result.

## The rules

The full rulebook is [SKILL.md](SKILL.md). In one screen:

| # | Rule | Gist |
|---|---|---|
| 1 | Substrate | Fleets run on the Workflow tool with model and effort set explicitly on every `agent()` call. An ad-hoc Agent-tool call can't set effort, so it inherits the session's, which is high or max exactly when you're working hard; an omitted model inherits the session's model, which in a session doing hard work is your most expensive tier. Standing custom agents can pin both in frontmatter. |
| 2 | Concurrency | Find your throughput ceiling once, then hold it yourself (mine is 8). Idle concurrency is fine; a throttled fleet is not. Big fan-outs get one agent told to refute the frame itself, because scale explores a frame and never breaks one. |
| 3 | Model tiering | Cheapest model that can't be wrong: trivial lookups on the fast tier; legwork, in-frame execution and hands-on coding on the mid tier (the default); judgment, critique of final work, the driver and orchestrators on the top tier; decisions you can't cheaply redo to the reserve pair. |
| 4 | Effort | A second dial inside the model. Set it per agent and never let it inherit (Opus 5.5 and Sonnet 5.5 default to medium). Top-tier subagents run at high, the mid tier never above high, a cheap tier's effort is never raised to rescue quality, and an unsupported level falls back quietly to the highest supported level at or below it. |
| 5 | Reserve pair | Two independent seats on one written brief (strongest model at xhigh, top tier at max) for any decision you can't cheaply redo. Agreement is the verdict; divergence goes to the human, never averaged. A big build's plan gets one blind critic before anything spawns. |
| 6 | Doctrine | Every agent prompt carries single-writer (subagents research and verify, only the orchestrator writes), honesty over scaffolding ("nothing to fix" is a valid finding), fresh-over-cached facts, and an evidence flag on every load-bearing claim. |
| 7 | Spawn checklist | Six questions before any agent spawns, plus a lane declaration: if any work is meant for a different lane or tier than the script's default, say so in one line before spawning. |
| 8 | Deadline work | On "work until X" mandates the duration is the deliverable. Agents have no clock. Check it explicitly, say the absolute deadline back, and treat an empty queue as a milestone, not a stop. |

### What changed on 2026-10-03

A new model generation and the October A/B moved the rulebook:

- The driver and every orchestrator now run the top tier at xhigh instead of the strongest model. The vendor's parity claim and the price list drove it, not a head-to-head of mine, and the vendor's own guidance cuts the other way for this seat; SKILL.md section 5 has both sides.
- The reserve tier became a pair: two independent seats on one brief for any decision you can't cheaply redo, divergence surfaced to the human, never averaged. The case it was proposed to catch is a single confident seat that was wrong (see the failure log).
- A big build's plan gets one fresh, blind top-tier critic before anything spawns.
- Hands-on coding moved to the mid tier at high; critique of final work and decisions stay on the top tier. Top-tier subagents run at high, xhigh is for the driver, orchestrators and the plan critic, max only inside the pair, and the mid tier never goes above high.
- The doctrine gained two lines: silence in the docs is not a verified negative, and a verbatim quote is checked against the raw page, not a model's answer about it.
- Dated facts were re-checked against the docs: model names and prices, effort defaults, the subagent-model variable's new precedence, what the workflows page now documents, and how a skill gets its command name.
- The cost table got a dated correction: two wrong price weights had understated the driver, re-priced where the sessions still exist (above).

## Run the measurements yourself

My numbers will rot (see Limits). The methods won't.

Blind same-effort A/B. Pick a few task shapes from your real work, not benchmarks. Run each on both models at the same effort level, otherwise you're measuring effort. Strip model identifiers, shuffle, grade against a rubric you wrote beforehand. Write your n down and let it be small. One limitation to copy better than I did: I never separately confirmed the delivered effort level on each run, and levels downgrade silently, so check yours. Check the resolved model too: aliases move with releases, and a headless run's JSON names its model in the per-model breakdown (`modelUsage`).

Cost audit. Session transcripts are JSONL under `~/.claude/projects/<project>/`; the main session logs to one file and each subagent to its own sidecar file, which is what makes the driver-versus-fleet split possible. One thing silently corrupted my first attempt, and one thing made it meaningless: compaction re-logs history, so the same message.id recurs and naive token sums came out about 4x too high (dedup by id); and nothing meaningful shows up until you split driver vs. subagents and cache reads vs. output. The table above carries both a cost-weighted share (tokens times each model's price, with cache reads at their own rate) and a raw-token share; the cost column's corrected figures, for the sessions that could be re-run, are in the 2026-10-03 update. Two more divisor guards this repo's own re-measurement taught me: exclude sessions that ran no fleet from any fleet-share claim, since they're 100% driver by construction, and drop empty session shells before computing ranges or medians, or a 0/0 division quietly poisons the statistics. And check every price weight against the list for the period you measured, not only the one you flagged as an assumption; mine carried two wrong ones (the 2026-10-03 update). And keep per-model token totals, not just the shares: two months later some of my transcripts were gone, and only the per-model totals let me re-price what was left.

Instrument validation. Before trusting any grader, gate, or analysis script, feed it a known-bad input and require a failure. No demonstrated red means the instrument is unproven, whatever its greens say. A perfect score on a non-trivial corpus is a smell, not a comfort.

Concurrency ceiling. Raise parallelism until you actually see 429s and backoff, then hold below that with margin; expect it to surface as agents stalling and retrying rather than a clean error in front of you. Mine landed at 8; yours depends on plan and workload. Don't confuse this ceiling with the platform's spawn guards (20 concurrent Agent-tool subagents by default per the docs as of Oct 2026; Workflow runs cap at 16 by default, fewer on weak CPUs), which stop spawns but say nothing about throttling. Your plan's rolling token budget is a third thing again, and you can exhaust that just fine at concurrency 1.

## Where the rules failed

This is the section I wanted to find in other people's rules and mostly didn't.

The routing rule failed three times, differently each time. I keep a rule that routes cheap grind work to a cheaper lane (mine is an off-quota third-party lane, but the same failure hits any tier split, including a plain Haiku/Sonnet/Opus one). First failure: the rule was loaded and I still didn't route anything to it under deadline pressure. The diagnosis wasn't forgetting, it was reluctance. Nobody rips out a working setup mid-race, so the fix was making the cheap lane part of normal work instead of an emergency measure. Second failure: the rule now fired at session start and still produced zero delegations, because the routing was being re-derived from scratch for every fleet, at the worst possible moment. Fix: pre-decide the routing in a template. Third failure, the interesting one: the lane decision was made correctly in prose at plan time, and then the fleet got written as a Workflow script whose model enum had no option for the planned lane. The planned lane silently fell back to the default model, and about 66% of that fleet's token flow went down the wrong lane after the right decision had already been made. A prose decision that isn't representable in the API you execute through doesn't exist. The surviving fix is in the skill now: declare the lane split in one line before anything spawns.

The cheap lane's concurrency rule started wrong in the other direction. Its first version said "max 2", copied from reports that turned out to measure a different regime (one client's internal parallelism, not independent processes). Measured properly, 4 parallel calls cost 1.43x one call's latency, and that ceiling moved to 4-6. Different rule from the 8 above, same lesson: check what regime a borrowed number was measured in before adopting it.

And my own instruments have committed the exact defect they were built to catch. Verification gates passed degenerate inputs (a 3-character answer sailed through a "40 words or less" check; count-valid bullet lists shipped ending mid-thought) until feeding every gate a known-bad first became the rule. It's now the first thing I check, including on this repo's own claims.

A confident single seat. In September a session answered a question about how my plan's usage limits behave, marked its answer VERIFIED, and was wrong: it had read silence in the help pages, plus older user reports, as a verified negative about server-side behaviour that can change, and the answer moved a real decision. Nothing in one seat's output signals that kind of error. That's the case the reserve pair was proposed to catch: decisions that can't be cheaply redone now get two independent seats, and their disagreement, not either answer alone, is what goes to me.

Mechanizing the rules produced a fresh class of failure: the mechanisms' own greens. I turned the rules above into hooks, a lint and a regression harness, and then had to build a discipline for not trusting them; that discipline is [MECHANISMS.md](MECHANISMS.md). Three of its lessons belong in this log.

A blocking mechanism that never blocked. I had a hook meant to stop a destructive command, documented as blocking by exiting 2 (which is what the hooks docs say blocks), and days of notes asserting it worked. On my setup (Windows, the hook registered with PowerShell as its shell and an `& '<path>'` command) the script's exit 2 reached Claude Code as exit 1, which is non-blocking, and the tool call proceeded every time. Blocking actually required emitting a JSON decision on stdout. Nothing in the code was wrong; the mechanism just wasn't connected to any consequence, and only a live smoke test that tried to run a real command found it. Details and scope in MECHANISMS.md.

A cleanup instrument that misread its own input in the reassuring direction. A script that flags stale notes for re-verification treats notes marked closed as exempt. Its "is this closed" test was a whole-line match, and on my real data 12 of the 17 notes it called closed were live, so those 12 were silently exempted from the staleness check they most needed. It reported a clean sweep while quietly skipping the work.

Adversarial review has no natural end, and its fixes bite back. Three days of review over these mechanisms kept finding real defects in one guard, the fixes themselves regressed neighbouring rules six times, and when I planted deliberate bugs in my own suites a third of them went unnoticed by the tests meant to catch them (the counts are in MECHANISMS.md). The lesson is that a stop rule has to be fixed in advance, because "test until it's clean" can't terminate. And the counterweight I now write down next to any mechanism: that guard has prevented zero real accidents in its logged life. It's frozen, it's described as a deterrent rather than a safety boundary, and it stays only because it's cheap. The mechanisms that measure earned their place; the one that blocks did not, and MECHANISMS.md says why that happened and what test I apply now.

The entry I least expected to write is the README's own original headline. The 90/10 split survived two multi-agent review rounds and a full prose rewrite, and fell to the first actual re-measurement (see the update above). Reviews check what a claim says; only measurement checks what it measures. The Haiku heading went the same way on 2026-08-19, for the same reason. And on 2026-10-03 the re-measurement's own cost column turned out to carry two wrong price weights: the reviews had checked its arithmetic and the one price I had flagged, not the two I hadn't.

## Limits

One person, one Windows machine, one plan tier, one working style. One to four runs per cell on the model A/Bs (July and October 2026); the driver/fleet split rests on 36 fleet-bearing sessions across three corpora, re-measured 2026-08-14 and re-priced on 2026-10-03 where the sessions still exist and reproduce (24 of the 36; 23 of them in the re-priced rows). Everything is dated June through early October 2026, and model names churn, so read the tiers by role (fast, mid, top, reserve) and treat the current names as examples. The Workflow tool is documented, and as of Oct 2026 its page covers `agent()`, `pipeline()` and `parallel()`; the per-call `model` and `effort` options are listed in the bundled `/workflow-authoring` reference rather than on the page, and the SDK reference documents the tool's own inputs. I use all of it in my own fleets, on v2.1.226 in August and v2.1.286 now. Verify in your version. Versioning: the measurements are dated where they appear and I don't retro-edit them; corrections land as dated update sections, the way the 2026-08-14, 2026-08-19 and 2026-10-03 ones did. The rulebook and MECHANISMS.md gain material as I learn things, and each change says what changed and when (the 2026-10-03 list is above). Replication results from other people get folded into the README, same as before. Not affiliated with Anthropic.

## Install

```
git clone https://github.com/lippinc/claude-operating-rules
```

Then put SKILL.md, on its own, in a folder named `claude-operating-rules` under your personal skills directory. On macOS or Linux:

```
mkdir -p ~/.claude/skills/claude-operating-rules && cp claude-operating-rules/SKILL.md ~/.claude/skills/claude-operating-rules/
```

On Windows the same directory is `%USERPROFILE%\.claude\skills\claude-operating-rules\`. Just SKILL.md is enough; don't nest the whole clone in there. The command you type is `/claude-operating-rules`: per the docs it comes from the frontmatter name, and the folder name invokes the skill too, which is one more reason to keep the two identical, as the Agent Skills spec asks. The skill also loads on its own when the model matches your request against its description. If `~/.claude/skills/` didn't exist when your session started, run `/reload-skills` once (or restart) so Claude Code picks it up. The file also reads fine as plain prose.

## License

MIT, Martin Lipp ([lippinc](https://github.com/lippinc)). If you replicate any measurement here, same result or opposite, an issue with your numbers and your n is the most useful thing you can send.
