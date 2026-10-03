---
name: claude-operating-rules
description: Operating rules for running multi-subagent fleets in Claude Code. Covers model tiering by task, per-agent reasoning effort, concurrency discipline, verification doctrine the fleet inherits, a two-seat check for decisions you can't cheaply redo, and time-boxed "work until X" mandates. Use when fanning out subagents, running the Workflow tool (agent(), parallel(), pipeline()), planning a multi-agent build, choosing a model or effort level for an agent, spawning an orchestrator, making a call that can't be cheaply redone, or given deadline-shaped autonomous work.
license: MIT
---

# Claude operating rules

When you scale work across many subagents, a handful of rules keep the fleet fast where it can be, cheap where it should be, rigorous where it must be, and under the throttling ceiling. You, the main loop, apply these every time you fan out work. An orchestrator applies this whole skill recursively to its own nested fan-out.

Provenance: these rules come from one practitioner's measured daily fleet use, June through early October 2026. Most measurements are small (one to four runs per cell on the model A/Bs), all on one machine and one plan tier. Treat every number as a default to re-measure on your own setup. The full writeup, methods, failure log and change log: https://github.com/lippinc/claude-operating-rules

## 1. Substrate: run fleets where model AND effort are set per agent

Spawn fleets with the Workflow tool (`agent()` / `parallel()` / `pipeline()`), not bare Agent-tool calls, and set `model` and `effort` explicitly on every `agent()` call. (The docs call these dynamic workflows, at code.claude.com/docs/en/workflows: all paid plans, and on Pro it's a toggle in `/config`. As of Oct 2026 that page documents `agent()`, `pipeline()` and `parallel()`, and the per-call options, `{ model, effort }` among them, are listed in the bundled `/workflow-authoring` reference. Verify in your version. No Workflow tool in your build? Then your substrate is predefined custom agents, one per tier, with `model:` and `effort:` pinned in frontmatter, which is documented.)

The reason: an ad-hoc Agent-tool call has a `model` parameter but no `effort` parameter, so it inherits the session's effort. Sessions doing hard work run at high or max effort, which means every ad-hoc subagent silently runs at that level too, and the whole tiering below collapses into "everything at the session's effort": the exact cost you're trying to avoid. A predefined custom agent (`.claude/agents/*.md`) can pin both `model:` and `effort:` in frontmatter. Use that for standing specialists you reuse; use Workflow for ad-hoc fleet lenses.

Three habits to bake in:

- Set `effort` on every `agent()` call. An omitted `effort` inherits the session's. The tool gives you the lever; you still have to pull it.
- Set `model` on every call too. An omitted `model` inherits the session's model, which in a session doing hard work is your most expensive tier (measured Aug 2026: a bare Agent call with no model ran the session's Fable 5). Cheap by default, expensive by explicit choice. This is a deliberate departure from the bundled reference, which advises omitting `model` so each agent inherits the session's: right when every stage needs the session's tier, wrong for a tiered fleet. And never force one model onto every subagent: since v2.1.251 `CLAUDE_CODE_SUBAGENT_MODEL` is only a default that a per-call or frontmatter model beats, but adding `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1` (v2.1.257+) makes it win over both again, workflow agents included, which silently undoes this whole section. (Before v2.1.251 the plain variable already won.)
- Model orchestration as nested `parallel()`/`pipeline()` inside one script, not agents-spawning-agents. Each inner `agent()` sets its own model and effort, and each inner fan-out still obeys the concurrency rule (section 2).

The shape, so there is no doubt what "set both" means:

```js
const notes = await agent('Summarize src/auth.ts in 10 lines.', { model: 'sonnet', effort: 'medium' })
```

Carve-out: a single throwaway lookup where inherited effort is fine can use the bare Agent tool, because a workflow script for one call is ceremony; pass `model` even there. Anything that fans out, even three calls, or where effort should vary by task, runs on Workflow: a bare Agent call can't set effort per call, so "Sonnet at medium, three times" is not something it can deliver.

## 2. Concurrency: find your throughput ceiling, then hold it yourself

Run a bounded number of agents concurrently: enough to matter, few enough that you never hit throttling. The author's ceiling landed at 8 (one plan tier, July 2026), found by raising parallelism until 429s and backoff appeared, then holding below with margin. Run the same probe to find yours. Chunk large item lists into waves of at most your ceiling and await each wave; the Workflow tool queues internally at its own cap, so the wave discipline is yours to keep. Accept the trade knowingly: a small barrier between waves is far cheaper than a throttled fleet. Idle concurrency is fine; a throttled fleet is not.

Three ceilings, don't conflate them. This throughput ceiling protects against throttling. The platform's spawn guards (default 20 concurrent Agent-tool subagents via `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`, v2.1.217+; Workflow runs cap at 16 concurrent agents by default, fewer on CPU-constrained machines) stop spawns but say nothing about throttling, and workflow agents follow their own limits. And your plan's rolling token budget is a third thing: concurrency discipline does not protect it, and you can exhaust it at concurrency 1.

What scale buys, and what it doesn't: more agents buy coverage, verification, and diversity inside the current frame. Fan-out explores within a frame; it does not break one. A large fleet pointed at the wrong question manufactures confident thoroughness. When the stakes are a framing choice, pair scale with one independent agent tasked to refute the frame itself ("is this the right axis?"). The frame error is the one more agents won't catch.

## 3. Model tiering: cheapest model that can't be wrong

Pay for intelligence only where it changes the outcome. Tiers by role, with the current mapping as a dated example (Oct 2026: Haiku 4.5 / Sonnet 5.5 / Opus 5.5, with Fable 5.1 as one seat of the reserve pair):

| Task | Tier |
|---|---|
| Trivially simple, non-fact-critical lookups: fetch a known file, grep one fact, list a directory. Hard limits: its output never carries facts downstream unverified; no web-heavy tasks | Fast tier (Haiku) |
| The fleet default: research fan-outs, multi-file search, structured extraction, digests, fact-verification sweeps, execution inside a fixed frame (implement to a clear spec, mechanical refactors, apply a fixed rubric), and hands-on coding to a spec or inside an agreed design | Mid tier (Sonnet) |
| Judgment: decisions and recommendations, critique or review of anything final, open-ended reasoning, design, synthesis, anything load-bearing that doesn't need the pair; and the driver (the main loop) and every orchestrator | Top tier (Opus) |
| A big build's plan | Top tier writes it; one fresh, blind top-tier critic checks it before anything spawns (section 5) |
| Decisions you can't cheaply redo | Reserve: a pair of independent seats (section 5) |

The mid-tier default is measured (small n), not folklore. Author's blind A/B, July 2026, same effort both sides, single run per model per task shape: Sonnet tied or beat Opus on research, extraction, and adversarial fact-verification at 40% of the list price. A second A/B in October (Sonnet 5.5 at high against Opus 5.5 at medium, high and xhigh, one to four runs per cell, packets near the ceiling) moved hands-on coding down: every config passed every test, and Sonnet was the cheapest, at about 60% of Opus-at-medium's cost, and the fastest. The same A/B is why critique and decisions stay on top: Sonnet caught every planted defect but missed a real, unplanted one that every Opus config caught, and on a decision brief two of its four runs gave a confident verdict without leaving the call to the human. So the mid tier is the enforced default for legwork, in-frame execution and coding, and picking the top tier for that work is the deviation that needs a reason. The boundary is who sets the frame: frame already decided, mid tier executes inside it; agent must set the frame, review something final, or a quiet error would corrupt a gate, top tier.

The fast tier is where degradation lives (the July A/B): Haiku fabricated facts and product names in both of its runs, and the run labelled high effort fabricated more convincingly. Read that as two runs, not a dial: per the docs Haiku 4.5 doesn't support effort at all (models missing from the effort table don't), so the "high" run may have received no extra effort. Hence its hard limits, and never reach for more effort to rescue it (section 4).

When unsure, tier up, but only if the task feeds a load-bearing decision. A cheap wrong answer that corrupts a downstream gate is the expensive outcome; a cheap right answer on legwork is free money.

Aliases move with releases. `sonnet` and `opus` resolve to the newest model of the family for your client version and provider, so the same script can run a different model after an update, and a family alias passed to a subagent resolves to the session's own model when the session runs that family. Confirm what an alias resolves to on a new install; a headless run's JSON output names the model in its per-model breakdown (`modelUsage`).

Where the cost sits depends on the work's shape. Author's re-measurement (2026-08-14, 36 fleet-bearing sessions across three corpora): on raw tokens, attended builds ran 60 to 67% driver, unattended overnight fleet runs inverted that, and nearly all of the driver's tokens were cache reads from carrying a big context. (The cost-weighted version carried two wrong price weights that overcharged the fleet; re-priced at list prices, the driver's cost share on the build that could be re-run rises to 80%. Details in the README's 2026-10-03 update.) The quality-safe lever is offloading reference material to subagents that read and return conclusions; don't starve the driver by shrinking its context mid-task, which forces compaction and, in the author's unmeasured experience, degrades quality faster than it saves cost.

## 4. Effort: the dial inside the model

Each agent picks its effort inside its model's band, based on how hard the specific task is, not how important it feels.

| Tier | Band | Notes |
|---|---|---|
| Fast (Haiku) | `low`, always (per the docs Haiku 4.5 doesn't support effort; set it anyway so a future fast-tier model never inherits the session's) | never raise it to rescue quality; policy, not a measured dial (section 3) |
| Mid (Sonnet) | `medium` to `high`, never `xhigh` or `max` | top of the band when the search is broad, execution spans many files, or the task is hands-on coding. Above `high`, an Opus run one level lower scored as well or better for less on the Artificial Analysis index (Oct 2026, a third-party benchmark) |
| Top (Opus) | `high` for every top-tier subagent; `xhigh` for the driver, orchestrators and the plan critic | `max` only as a reserve seat (section 5) |
| Reserve | the section 5 recipe: `xhigh` on the strongest model, `max` on the top tier | always, the recipe defines it |

The top tier's band is measured, small n. In the October A/B, `xhigh` bought nothing measurable over `high` on the coding, critique and decision packets, at up to about twice the cost and time, and `medium` lost points on three of its four decision briefs, two of them for unsupported figures. Hence `high` as the working level for judgment, not `medium`. The `xhigh` seats are policy, not a measured win: long-lived or frame-setting work where a slip compounds.

Never leave `effort` to inherit. An omitted effort defaults to the session's, which is whatever you raised it to for hard work, and otherwise the model's default in Claude Code: `high` on most models that support effort, but `medium` on Opus 5.5 and Sonnet 5.5 (and `xhigh` on Opus 4.7; the raw API's defaults differ). On the top tier, `medium` is the level that slipped on judgment above. And verify a level actually stuck: per the docs, a level the model doesn't support falls back to the highest supported level at or below it, and in my runs that produced no error, so an `xhigh` request on a model that doesn't support it is just a quieter run. Level names are also calibrated per model, so the same name doesn't mean the same depth on two models. (The bands above are policy, not capability limits; as of Oct 2026 Sonnet 5.5 supports `xhigh` and `max`, this rulebook just doesn't spend them there.)

## 5. The reserve pair: two seats for what you can't cheaply redo

The test is one question: if this is wrong, can it be cheaply redone? If not, it's a pair call: a go/kill verdict, the core architecture decision, a gate that decides the whole project, a pricing, launch or rules change you can't walk back. Run two independent seats on one written brief: your strongest model at `xhigh`, and the top tier at `max` with the keyword "ultrathink" in its prompt (Oct 2026: Fable 5.1 and Opus 5.5). Per the docs, "ultrathink" adds an in-context request for deeper reasoning without changing the effort sent. The docs describe it for prompts you type, and whether it fires in a prompt a script passes to `agent()` isn't documented, so the explicit effort is what each seat rests on and the keyword is a cheap extra. Both are fresh agents, not the driver, whose context already carries the session's framing. Each gets the brief and the evidence, and neither sees the other's answer.

- Agreement is the verdict. Label it two-seat.
- Divergence is a finding, not noise. Run one reconciliation round in which each seat reads the other's reasoning and updates or holds. Whatever still diverges goes to the human with both readings and the point where they split. Never average the two, and never let the driver quietly pick its favourite.
- No strongest model (not on your plan, or it would bill somewhere you don't want): two top-tier `max` seats with the keyword and separate contexts, and say so in the verdict ("two-seat, same-family"). The diversity then comes from independence, not from the model family.

Why two seats: one seat gives you no divergence signal. The incident this rule was proposed to catch: a single seat answered a question about how the usage limits on the author's plan behave, marked its answer VERIFIED, and was wrong. It had read silence in the help pages plus older user reports as a verified negative about server-side behaviour that can change. One seat, confident, no signal; a second independent seat is the cheapest way to get one. Decisions are short, so the pair is cheap, and it is the only place this rulebook plans to spend the strongest model. (Fable 5.1 is in the `/model` picker on the Anthropic API unless your organization excludes it, and depending on plan and seat tier it can bill to usage credits; Mythos 5.1 is the invitation-only sibling.)

The driver and orchestrators run the top tier, not the reserve. Until late September 2026 the reserve also took every orchestrator. Now the driver and every orchestrator run the top tier at `xhigh`. The reasons are the vendor's statements and the price list, not a head-to-head I measured. The launch page says Opus 5.5 "performs at the level of Claude Fable 5.1 on most work". It lists at 40% of Fable 5.1's price for input, output and cache writes ($4/$20 against $10/$50 per MTok), though at 80% of it for cache reads ($0.20 against $0.25), which are most of a long-lived driver's tokens. And the orchestrator is the longest-lived, most context-heavy seat there is, so its model is most of the bill (section 3). The vendor's guidance cuts the other way for this one seat: start most workloads on Opus 5.5, but use Fable 5.1 for "demanding reasoning and long-horizon agentic work" or when evals on Opus 5.5 at higher effort fall short (models overview, Oct 2026), and a long orchestrator run arguably is that. I spend the strongest model where a decision can't be redone instead of on carrying context; if your orchestrator's plans start slipping, re-test this choice first. An orchestrator applies this entire skill to its own nested fan-out: same wave cap, same tiering, same bands, same pair test.

A big build's plan: the top tier writes it, and before anything spawns, one fresh top-tier critic at `xhigh` checks it blind. The critic gets the written brief, answers it first without seeing the plan, then reads the plan and returns its objections. The driver fixes or answers each one, and an objection it can't settle goes to the human. A decision inside the plan that can't be cheaply redone (the core architecture, go/kill) still goes to the pair. (From late September plans went through the pair; in October they moved to a single blind critic after one multi-stage build ran that way and held up on its own checks; it hasn't been judged externally yet. A judgment on n=1, not a comparison.)

Don't spend the pair as a default. If everything is critical, nothing is.

## 6. The doctrine the whole fleet inherits

Put the relevant rules into each agent's prompt, so a subagent with no other context still behaves correctly:

- Single-writer: only the orchestrator authors deliverables. Subagents research, critique, and verify; they never edit the deliverable. One coherent voice, no merge chaos.
- Honesty over scaffolding: never fabricate a finding or verdict. "Nothing to fix" is a valid, expected result; never invent a problem to look productive. Report failures and skipped steps plainly.
- Fresh over cached: anything from memory, a config file, or a prior session is fine for conventions, never the basis for a load-bearing claim. Re-confirm load-bearing facts fresh from primary source each run.
- Flag every load-bearing claim with its evidentiary status: VERIFIED (checked against the primary source this run), SINGLE-SOURCE (one source, unconfirmed), LEAD-ONLY (a hint worth following, not a fact), DERIVED (reasoned from other facts), VERIFIED-NEGATIVE (looked in the right place and it is absent; silence in the docs is not that, for behaviour that can change server-side). A LEAD-ONLY claim never decides anything load-bearing.
- Quote from the raw text. A fetch tool that answers through a model (WebFetch runs a small fast model over the page) can paraphrase or misattribute a quote, and a verifier reading that answer can then refute a true claim it never saw. Check a verbatim quote against the raw page.
- Deepen the how, never change the what: add rigor freely; never silently rescope or skip a hard gate. Requested counts are floors, not ceilings.
- Density: state once, reference, don't restate. Each rule keeps one canonical home.
- Instrument validation: before trusting any grader, gate, checker or analysis script, yours or a subagent's, feed it a known-bad input and require it to fail. No demonstrated red means the instrument is unproven, whatever its greens say; a perfect score on a non-trivial corpus is a smell, not a comfort. (The fuller discipline: MECHANISMS.md in the repo.)

## 7. The spawn checklist

Run this for every agent in the fleet:

0. Lane declared? If any of the work belongs on a different lane than the script's default (a cheaper external leg, a different model band), say so in one line before anything spawns. A prose lane decision that isn't representable in the API you execute through doesn't exist; it silently becomes the default model.
1. Substrate? Workflow `agent()` so model and effort are set per call; bare Agent tool only for a single throwaway helper (section 1).
2. Complexity to tier? Trivial non-fact-critical lookup: fast. Legwork, extraction, verification, in-frame execution, hands-on coding: mid (the default). Judgment, decisions, critique of anything final, a gate-corrupting error risk, the driver or an orchestrator: top. A big build's plan: top, plus one blind top-tier critic. Can't be cheaply redone: the reserve pair (section 5).
3. Effort? Explicit, inside the band. Fast `low`, mid `medium|high`, top `high` (`xhigh` for the driver, orchestrators and the plan critic; `max` only as a pair seat). Never inherit.
4. Can't be cheaply redone? Two independent seats on one written brief, divergence surfaced, never averaged. An orchestrator? Top tier at `xhigh`. In practice it's the driver itself, with its fan-out nested in one script (section 1) rather than a spawned orchestrator agent, and it applies this skill to that fan-out.
5. Wave size? At most your measured ceiling live at once; chunk bigger fan-outs into waves.
6. Prompt hygiene? Bake in single-writer (research-only unless this agent is the writer), the doctrine rules that apply, and the claim-flagging requirement.

Mnemonic: Workflow for fleets, cheapest model that can't be wrong, lowest effort in its band that does the job, the top tier drives and decides, two seats for what can't be cheaply redone, never more than your ceiling at once.

## 8. Deadline-shaped work: "work until X"

Some mandates are time-boxed, not task-boxed: "work until 3am," "keep going for two hours," an overnight run. In those, the duration is the deliverable and the task list is just fuel. Finishing the queue early is not finishing the mandate. (Origin: a session once finished its queued tasks in about 20 minutes of a multi-hour mandate and stopped, silently converting "work until 3am" into "finish these tasks.")

- You have no native clock. Never infer time from feel, turn count, or output volume. The clock is an explicit check, `Get-Date` (PowerShell) or `date` (bash), every time you need the time.
- On receiving the mandate: check the clock, resolve to an absolute deadline, and say it back ("deadline = 03:00 local") so a misread surfaces immediately. Write it into a state file you name for the run, next to the task list.
- Before ending any turn: check the clock. If time remains, pick the next unit of work and continue. Completing the current task is a milestone, not a stop. The only valid early stops: a fresh clock check shows the deadline passed, or a hard blocker only the user can clear (then say which, and leave state pointing at what you'd do next).
- Where the extra work comes from when the queue empties: deepen the how. Verification passes over what was built, instrument validation, hardening, docs, prep for the next stage. Never gated or irreversible actions, and never invented scope to look busy.
- Log each clock check, one timestamped line per batch, so the discipline is auditable and a resumed session can see the runway.
- Bound the spend before you bound the time. Every unattended headless run (`claude -p`, a scheduled job) carries `--max-budget-usd` and `--max-turns`; per the docs the budget flag is print-mode only, subagent spend counts toward it, and spawns fail once it is reached (v2.1.217+). Check how your plan bills the strongest model before any headless run: per the docs it can bill to usage credits depending on plan and seat tier, and in `-p` mode, or in an Agent SDK app that doesn't show the consent prompt, Claude Code bills that without asking. An interactive overnight session has no budget flag, so there the clock rule and your plan's meter are the bound.
