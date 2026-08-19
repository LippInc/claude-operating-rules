---
name: claude-operating-rules
description: Operating rules for running multi-subagent fleets in Claude Code. Covers model tiering by task, per-agent reasoning effort, concurrency discipline, verification doctrine the fleet inherits, and time-boxed "work until X" mandates. Use when fanning out subagents, running the Workflow tool (agent(), parallel(), pipeline()), planning a multi-agent build, choosing a model or effort level for an agent, spawning an orchestrator, or given deadline-shaped autonomous work.
license: MIT
---

# Claude operating rules

When you scale work across many subagents, a handful of rules keep the fleet fast where it can be, cheap where it should be, rigorous where it must be, and under the throttling ceiling. You, the main loop, apply these every time you fan out work. An orchestrator subagent applies this whole skill recursively to its own fan-out.

Provenance: these rules come from one practitioner's measured daily fleet use, June through August 2026. Most measurements are a single run (n=1 per cell on the model A/B; the Haiku result got one same-day retest), all on one machine and one plan tier. Treat every number as a default to re-measure on your own setup. The full writeup, methods, and failure log: https://github.com/lippinc/claude-operating-rules

## 1. Substrate: run fleets where model AND effort are set per agent

Spawn fleets with the Workflow tool (`agent()` / `parallel()` / `pipeline()`), not bare Agent-tool calls, and set `model` and `effort` explicitly on every `agent()` call. (The Workflow tool itself is documented at code.claude.com/docs/en/workflows: v2.1.154 or later, all paid plans, and on Pro it's a toggle in `/config`. What the docs don't show as of Aug 2026 is `model` and `effort` as per-call options, or `parallel()`: in current builds `agent()` accepts `{ model, effort }` alongside the documented `{ schema, label }`, and `parallel()` ships next to the documented `pipeline()`; the workflows page points to an SDK reference that has no Workflow entry yet. Verify in your version. No Workflow tool in your build? Then your substrate is predefined custom agents, one per tier, with `model:` and `effort:` pinned in frontmatter, which is documented.)

The reason: an ad-hoc Agent-tool call has a `model` parameter but no `effort` parameter, so it inherits the session's effort. Sessions doing hard work run at high or max effort, which means every ad-hoc subagent silently runs at that level too, and the whole tiering below collapses into "everything at the session's effort": the exact cost you're trying to avoid. A predefined custom agent (`.claude/agents/*.md`) can pin both `model:` and `effort:` in frontmatter. Use that for standing specialists you reuse; use Workflow for ad-hoc fleet lenses.

Three habits to bake in:

- Set `effort` on every `agent()` call. An omitted `effort` inherits the session's. The tool gives you the lever; you still have to pull it.
- Set `model` on every call too. An omitted `model` inherits the session's model, and in a session running the top tier that is the most expensive agent there is (measured Aug 2026: a bare Agent call with no model ran the session's Fable 5). Cheap by default, expensive by explicit choice. And never set `CLAUDE_CODE_SUBAGENT_MODEL` globally: per the docs it overrides both the per-call `model` and the frontmatter `model`, so it silently undoes this whole section.
- Model orchestration as nested `parallel()`/`pipeline()` inside one script, not agents-spawning-agents. Each inner `agent()` sets its own model and effort, and each inner fan-out still obeys the concurrency rule (section 2).

The shape, so there is no doubt what "set both" means:

```js
const notes = await agent('Summarize src/auth.ts in 10 lines.', { model: 'sonnet', effort: 'medium' })
```

Carve-out: a single throwaway lookup where inherited effort is fine can use the bare Agent tool, because a workflow script for one call is ceremony; pass `model` even there. Anything that fans out, even three calls, or where effort should vary by task, runs on Workflow: bare Agent calls can't set effort at all, so "Sonnet at medium, three times" is not something they can deliver.

## 2. Concurrency: find your throughput ceiling, then hold it yourself

Run a bounded number of agents concurrently: enough to matter, few enough that you never hit throttling. The author's ceiling landed at 8 (one plan tier, July 2026), found by raising parallelism until 429s and backoff appeared, then holding below with margin. Run the same probe to find yours. Chunk large item lists into waves of at most your ceiling and await each wave; the Workflow tool queues internally at its own cap, so the wave discipline is yours to keep. Accept the trade knowingly: a small barrier between waves is far cheaper than a throttled fleet. Idle concurrency is fine; a throttled fleet is not.

Three ceilings, don't conflate them. This throughput ceiling protects against throttling. The platform's spawn guards (default 20 concurrent Agent-tool subagents via `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`, v2.1.217+; Workflow runs cap at 16, fewer on CPU-constrained machines) stop spawns but say nothing about throttling, and workflow agents follow their own limits. And your plan's rolling token budget is a third thing: concurrency discipline does not protect it, and you can exhaust it at concurrency 1.

What scale buys, and what it doesn't: more agents buy coverage, verification, and diversity inside the current frame. Fan-out explores within a frame; it does not break one. A large fleet pointed at the wrong question manufactures confident thoroughness. When the stakes are a framing choice, pair scale with one independent agent tasked to refute the frame itself ("is this the right axis?"). The frame error is the one more agents won't catch.

## 3. Model tiering: cheapest model that can't be wrong

Pay for intelligence only where it changes the outcome. Tiers by role, with the current mapping as a dated example (Aug 2026: Haiku / Sonnet / Opus):

| Task | Tier |
|---|---|
| Trivially simple, non-fact-critical lookups: fetch a known file, grep one fact, list a directory. Hard limits: its output never carries facts downstream unverified; no web-heavy tasks | Fast tier (Haiku) |
| The fleet default: research fan-outs, multi-file search, structured extraction, digests, fact-verification sweeps, and execution inside a fixed frame (implement to a clear spec, mechanical refactors, apply a fixed rubric) | Mid tier (Sonnet) |
| Judgment: open-ended reasoning, design, synthesis, anything load-bearing that isn't reserve-tier | Top tier (Opus) |
| Project-deciding calls and orchestrators (section 5) | Reserve tier |

The mid-tier default is measured (small n), not folklore. Author's blind A/B, July 2026, same effort both sides, single run per model per task shape: Sonnet tied or beat Opus on research, extraction, and adversarial fact-verification at 40% of the list price. So mid-tier is the enforced default for that band, and picking the top tier for legwork is the deviation that needs a reason. The boundary is who sets the frame: frame already decided, mid tier executes inside it; agent must set the frame, or a quiet error would corrupt a gate, top tier.

The fast tier is where degradation lives (same A/B): Haiku fabricated facts and product names in both of its runs, and the run labelled high effort fabricated more convincingly. Read that as two runs, not a dial: Haiku 4.5 is absent from the docs' effort-support table as of Aug 2026, so the "high" run may have received no extra effort at all. Hence its hard limits, and never reach for more effort to rescue it (section 4).

When unsure, tier up, but only if the task feeds a load-bearing decision. A cheap wrong answer that corrupts a downstream gate is the expensive outcome; a cheap right answer on legwork is free money.

Where the cost sits depends on the work's shape. Author's re-measurement (2026-08-14, 36 fleet-bearing sessions across three corpora): attended builds run roughly 70/30 driver-heavy, unattended overnight fleet runs invert to about 33/67, and roughly two-thirds of driver cost on builds is cache reads from carrying a big context. The quality-safe lever is offloading reference material to subagents that read and return conclusions; don't starve the driver by shrinking its context mid-task, which forces compaction and, in the author's unmeasured experience, degrades quality faster than it saves cost.

## 4. Effort: the dial inside the model

Each agent picks its effort inside its model's band, based on how hard the specific task is, not how important it feels.

| Tier | Band | Top of band when... |
|---|---|---|
| Fast (Haiku) | `low`, always (Haiku 4.5 is absent from the docs' effort-support table as of Aug 2026; set it anyway so a future fast-tier model never inherits the session's) | never raise it to rescue quality; policy, not a measured dial (section 3) |
| Mid (Sonnet) | `medium` to `high` | the search is broad, execution spans many files, or judgment is non-trivial |
| Top (Opus) | `high` to `xhigh` | the reasoning or synthesis is genuinely hard |
| Reserve | the section 5 recipe: `xhigh` on Fable 5, `max` on Opus | always, the recipe defines it |

Never leave `effort` to inherit. An omitted effort defaults to the session's, which is high by default on every model that supports effort (Opus 4.7 defaults to xhigh) and max whenever you've raised it for hard work. And verify a level actually stuck: per the docs, a level the model doesn't support falls back to the highest supported level at or below it, and in my runs that produced no error, so an `xhigh` request on a model that doesn't support it is just a quieter run. (The bands above are policy, not capability limits; as of Aug 2026 Sonnet 5 supports `xhigh` and Fable 5 supports `max`, this rulebook just doesn't spend them there.)

## 5. The reserve tier: for what decides the project

The top of the ladder is your strongest available model at the top of the effort band this rulebook spends. As of Aug 2026 that's Fable 5 at `xhigh` where your plan or organization has it (Fable 5 is generally available, but the picker only lists it once the server reports it for your org, and on some plans it bills to usage credits, so not every setup sees it; Mythos 5 is the invitation-only sibling), otherwise Opus at `max` with the keyword "ultrathink" in the agent's prompt (per the docs it adds an in-context request for deeper reasoning without changing the effort sent). Note the two recipes are shaped differently on purpose: the explicit effort is the whole Fable recipe, the keyword belongs to the Opus one. Reserve this tier for the two cases where being wrong is unrecoverable or compounds:

1. Load-bearing calls: the result decides the project's future. A go/kill verdict, the core architecture decision, a gate. The decisions you cannot cheaply redo.
2. Orchestrators: a stage whose job is running a big fan-out. Its plan multiplies across everyone it spawns, so a flaw at the top propagates to all of them. An orchestrator applies this entire skill to its own nested fan-out: same wave cap, same tiering, same bands.

Don't spend the reserve tier as a default. If everything is critical, nothing is.

## 6. The doctrine the whole fleet inherits

Put the relevant rules into each agent's prompt, so a subagent with no other context still behaves correctly:

- Single-writer: only the orchestrator authors deliverables. Subagents research, critique, and verify; they never edit the deliverable. One coherent voice, no merge chaos.
- Honesty over scaffolding: never fabricate a finding or verdict. "Nothing to fix" is a valid, expected result; never invent a problem to look productive. Report failures and skipped steps plainly.
- Fresh over cached: anything from memory, a config file, or a prior session is fine for conventions, never the basis for a load-bearing claim. Re-confirm load-bearing facts fresh from primary source each run.
- Flag every load-bearing claim with its evidentiary status: VERIFIED (checked against the primary source this run), SINGLE-SOURCE (one source, unconfirmed), LEAD-ONLY (a hint worth following, not a fact), DERIVED (reasoned from other facts), VERIFIED-NEGATIVE (looked in the right place and it is absent). A LEAD-ONLY claim never decides anything load-bearing.
- Deepen the how, never change the what: add rigor freely; never silently rescope or skip a hard gate. Requested counts are floors, not ceilings.
- Density: state once, reference, don't restate. Each rule keeps one canonical home.
- Instrument validation: before trusting any grader, gate, checker or analysis script, yours or a subagent's, feed it a known-bad input and require it to fail. No demonstrated red means the instrument is unproven, whatever its greens say; a perfect score on a non-trivial corpus is a smell, not a comfort. (The fuller discipline: MECHANISMS.md in the repo.)

## 7. The spawn checklist

Run this for every agent in the fleet:

0. Lane declared? If any of the work belongs on a different lane than the script's default (a cheaper external leg, a different model band), say so in one line before anything spawns. A prose lane decision that isn't representable in the API you execute through doesn't exist; it silently becomes the default model.
1. Substrate? Workflow `agent()` so model and effort are set per call; bare Agent tool only for a single throwaway helper (section 1).
2. Complexity to tier? Trivial non-fact-critical lookup: fast. Legwork, extraction, verification, in-frame execution: mid (the default). Frame-setting judgment or gate-corrupting error risk: top. Project-deciding or orchestrator: reserve (section 5).
3. Effort? Explicit, inside the band. Fast `low`, mid `medium|high`, top `high|xhigh`. Never inherit.
4. Load-bearing, or an orchestrator? Reserve tier, and it applies this skill to its own fan-out.
5. Wave size? At most your measured ceiling live at once; chunk bigger fan-outs into waves.
6. Prompt hygiene? Bake in single-writer (research-only unless this agent is the writer), the doctrine rules that apply, and the claim-flagging requirement.

Mnemonic: Workflow for fleets, cheapest model that can't be wrong, lowest effort in its band that does the job, reserve the top for what decides the project, never more than your ceiling at once.

## 8. Deadline-shaped work: "work until X"

Some mandates are time-boxed, not task-boxed: "work until 3am," "keep going for two hours," an overnight run. In those, the duration is the deliverable and the task list is just fuel. Finishing the queue early is not finishing the mandate. (Origin: a session once finished its queued tasks in about 20 minutes of a multi-hour mandate and stopped, silently converting "work until 3am" into "finish these tasks.")

- You have no native clock. Never infer time from feel, turn count, or output volume. The clock is an explicit check, `Get-Date` (PowerShell) or `date` (bash), every time you need the time.
- On receiving the mandate: check the clock, resolve to an absolute deadline, and say it back ("deadline = 03:00 local") so a misread surfaces immediately. Write it into a state file you name for the run, next to the task list.
- Before ending any turn: check the clock. If time remains, pick the next unit of work and continue. Completing the current task is a milestone, not a stop. The only valid early stops: a fresh clock check shows the deadline passed, or a hard blocker only the user can clear (then say which, and leave state pointing at what you'd do next).
- Where the extra work comes from when the queue empties: deepen the how. Verification passes over what was built, instrument validation, hardening, docs, prep for the next stage. Never gated or irreversible actions, and never invented scope to look busy.
- Log each clock check, one timestamped line per batch, so the discipline is auditable and a resumed session can see the runway.
- Bound the spend before you bound the time. Every unattended headless run (`claude -p`, a scheduled job) carries `--max-budget-usd` and `--max-turns`; per the docs the budget flag is print-mode only, subagent spend counts toward it, and spawns fail once it is reached (v2.1.217+). An interactive overnight session has no such flag, so there the clock rule and your plan's meter are the bound.
