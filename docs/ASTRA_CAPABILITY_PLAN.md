# Astra Capability and Whole-Workflow Budget Plan

Status: research-backed proposal, not implemented or measured Astra performance.
Date: 2026-09-07. Audience: Sulabh Dubey and governor maintainers.

## Decision

Replace the default Sol-first policy with capability-aware workflow planning.
Offer an Astra-preferred mode that reserves an actual Astra contribution on
eligible substantive work within an explicit total task budget. Astra can lead,
investigate, implement, or review. Routine work may still use efficient models.
Never silently replace a requested Astra contribution with Sol-only completion:
report whether it was executed, deferred, or could not fit the budget.

A universal premium-call minimum would force spending without proving value.
Make participation an explicit user preference, with a reasoned exception when
the budget cannot support it. Mandatory security approval and the task budget
still apply. Do not manufacture complex tasks merely to consume a reserve.

## Research Findings and Limits

1. [RouteLLM, ICLR 2025](https://arxiv.org/abs/2406.18665) learns strong/weak
   routing from preference data. Adopt calibration against comparative outcomes;
   do not treat a task keyword as evidence of model superiority. Its evaluations
   do not prove equivalent savings for Astra or multi-turn coding workflows.
2. [FrugalGPT](https://arxiv.org/abs/2305.05176) studies learned cascades under
   cost constraints. Consider cascade cost including unsuccessful earlier calls.
   Cheap-first is one candidate workflow, not a universal requirement.
3. [Test-time compute allocation](https://arxiv.org/abs/2408.03314) finds that
   useful compute allocation depends on problem difficulty in its studied tasks.
   Choose reasoning budgets per task; do not always force low reasoning or a
   500-word decision when a difficult derivation needs more work.
4. [LLMLingua](https://github.com/microsoft/LLMLingua) offers compression methods.
   [Lost in the Middle](https://arxiv.org/abs/2307.03172) documents evidence-position
   effects in tested models. Use relevant, traceable evidence and measure whether
   compression removes decisive information. Neither proves that compressed
   context preserves every capability of Astra.
5. [Anthropic's agent patterns](https://www.anthropic.com/engineering/building-effective-agents)
   distinguish orchestration, routing, and evaluation workflows. Let Astra choose
   specific investigations and delegate bounded execution; avoid an always-on
   premium coordinator that rereads every worker log.
6. [LLM judge evaluation](https://arxiv.org/abs/2306.05685) identifies position,
   verbosity, and self-preference biases. Prefer executable tests and blinded
   comparisons; model judgment alone is insufficient proof of improvement.
7. [Bandit-feedback routing](https://arxiv.org/abs/2510.07429) addresses learning
   when only the chosen model's outcome is observed. Reserve a bounded evaluation
   sample so Sol-only routing cannot become self-confirming. Do not train on
   unobserved outcomes as though they were failures or zero benefit.
8. [OpenAI pricing](https://learn.chatgpt.com/docs/pricing) currently lists Astra
   at 250/25/1250 and Sol at 100/10/500 credits per million ordinary input/cached
   input/output tokens. These support a 2.5 ratio for matching token composition,
   not a universal conversion of weekly percentages to credits. Image generation
   and other concurrent work can also affect included usage.
9. [OpenAI caching documentation](https://developers.openai.com/api/docs/guides/prompt-caching)
   warns that shared prefixes are not necessarily cached prefixes. Treat caching
   as observed provider behavior. Do not assume a stable brief is a cache hit or
   that API cache controls are exposed by the Codex host.

These sources establish useful mechanisms and limitations, not a tested optimal
Astra/Sol allocation. Research stopped after covering routing, budget accounting,
compression, adaptive compute, orchestration, evaluation bias, and provider costs.

## Verified Current Gaps

- policy.py returns allow_non_premium immediately for an already requested Sol
  call, without considering whether Astra could improve a stage of the task.
- Broad context is a global premium block rather than a request to prepare or
  selectively retrieve evidence for a particular stage.
- cost.py compares the premium leg with a Sol baseline, omitting worker,
  preparation, retries, and verification costs from hybrid parity.
- Read-only diagnostic: Sol baseline 5.5, Astra leg 3.75, reported parity true;
  doing both costs 9.25, approximately 68% above the Sol baseline.
- At 70% remaining, requesting Astra without capsule quality or cost data returns
  allow_premium_capsule with parity null. Required evidence is optional in code.
- shadow.py constructs approval from remaining capacity and constructs a Sol
  baseline from draft character length. Neither establishes user authorization
  or a matched workflow baseline.
- capsule.py copies the first 5,000 characters of each file; relevant later lines
  can vanish without a per-file omission notice. Quality is a formatting heuristic.
- tournament.py returns scores and IDs as finalists but omits candidate answers.
  A premium judge cannot evaluate those answers from that packet.
- predictor.py mixes a heuristic with global keyword-derived outcomes, without
  task-specific calibration. The substring 'benefit' also matches 'no benefit'.
- Doctrine aggregation counts written principles; it does not train Sol weights.
- MCP functions prepare and return data. They do not themselves execute Astra.

## Proposed Operating Contract

Input: user objective, quality target, task budget, desired Astra participation,
available model/tool capabilities, evidence state, uncertainty, and deadline.
Output: staged plan, model and role per stage, cost range, reserved verification
budget, Astra participation state, and explicit execution receipts.

Default user-selectable modes:
- Astra-preferred: include a substantive Astra stage when feasible; report unmet
  participation explicitly. Recommended for Sulabh's intended experience.
- Adaptive: choose the measured quality/cost tradeoff without a participation rule.
- Economy: minimize spend subject to the quality target.

Candidate workflows:
- Astra direct: bounded hard problem, creative synthesis, or difficult patch.
- Astra plan, efficient execution: novel multi-step work needing early direction.
- Efficient preparation, Astra investigation: retrieval-heavy task with open questions.
- Efficient draft, Astra review: mature artifact with independent supporting evidence.
- Astra investigation and implementation: tightly coupled hard bug where handoffs
  would lose context or cost more than direct premium work.
- Efficient-only: routine deterministic work, or an explicit user-approved fallback.

Capabilities are role-specific, not assumed exclusive to one model. Multimodal
tasks must retain actual relevant images, charts, or audio when supported, rather
than passing only a weaker model's description. Tool availability is checked at
runtime. Skills specify procedures; model choice determines who performs them.

## Total Budget and Leases

C_total = preparation + Astra work + worker work + handoffs + retries + verification.
C_total must fit the configured task budget, with uncertain components expressed
as ranges and a reserve for completion. Compare against a matched, equally focused
Sol workflow, not an artificially broad baseline. Record estimated vs actual cost.

Illustration only: for a 5-credit task, reserve 0.5 preparation, 1.5 Astra,
2.0 worker execution, 0.5 verification, and 0.5 contingency. This is a budget
allocation example, not proof the task can achieve equal quality at that price.

Use model-specific weighted token prices; count reasoning and cached tokens
according to provider semantics, without double counting included subsets.
Give reservations task/stage IDs, expiry, spend reconciliation, and atomic updates
to prevent concurrent work from consuming the same budget twice.

At low weekly capacity, account for time until reset and concurrent reservations.
Remaining percentage alone is inadequate. Preserve explicit emergency approval;
never convert low capacity into a silent permanent Sol-only policy.

## Evidence-on-Demand

Start with the goal, raw constraints, source manifest, key excerpts, uncertainties,
and contradictory evidence. Astra may request specific functions, test results,
images, or additional investigation within its lease. It may revise the problem
framing, reject candidate plans, or request more evidence before deciding.

Preserve source hashes and line ranges; show exclusions and truncations. Detect
stale sources and instructions embedded in untrusted material. Regex scanning is
a supplementary signal, not proof of safety. Tests and provenance support truth;
capsule headings alone do not. Reused decisions expire when their evidence changes.

## Implementation Sequence

1. Fix accounting and truth gaps in cost.py, policy.py, shadow.py, capsule.py,
   tournament.py, and predictor.py with focused behavioral regressions.
2. Add workflow plans and capability profiles; return planned roles rather than
   a single default model. Preserve existing CLI/MCP callers via versioned schemas.
3. Add evidence expansion, task-wide reservations, receipts, cancellation, retry
   limits, stale-evidence invalidation, and provider usage normalization.
4. Add a host adapter reporting whether it can execute/switch models or only
   prepare handoffs. Verify the actual model used from host metadata. Changing
   the recommendation never counts as executing Astra; no UI overclaim is allowed.
5. Align local skills, plugin, CLI, MCP, dashboard, and landing demo with one
   policy contract. Replace the independently handwritten browser router with
   shared generated policy fixtures and cross-language equivalence checks.
6. Run comparative evaluations, calibrate choices, then publish measured claims.

## Evaluation and Release Gates

Pilot 24 tasks across six families: architecture, difficult bugs, routine coding,
research synthesis, visual judgment, and release/security review. The pilot is
for discovering failures, not broad statistical claims. Use identical starting
states and evidence for Sol-only, Astra-only, current governor, and proposed
governor; repeat variable tasks and separate calibration from held-out evaluation.

Measure total cost, latency, retries, completion, correctness, regression risk,
evidence omissions, and whether Astra changed an adopted decision or artifact.
Record failed and abandoned runs. Use tests and blinded expert review with clear
rubrics; the authoring model must not be the sole quality judge. No fake scores.

Require successful actual Astra runs for direct, planning, investigation, and
review paths before claiming the capabilities are integrated. Test budget
exhaustion, cancellation, concurrent leases, unavailable models, missing telemetry,
freshness changes, malicious evidence, cache misses, and ignored worker instructions.

Evaluate quality and cost jointly. Predeclare tolerances and report uncertainty
per task family; if equal quality within Sol cost is infeasible, report that
tradeoff rather than quietly downgrading quality or inflating the baseline.

## Revised Product Promise

Use Astra where it changes the result, with control over the complete cost of
getting that result. Astra participation is visible and verifiable. Equal quality
at equal cost is an empirical target, never a universal guarantee.
