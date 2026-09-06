# Governor Decision Record

This record captures the policy decision used for the launch-docs upgrade of
this repository.

## Task

Upgrade the public GitHub repo so people can understand, test, cite, and adopt
Premium Model Budget Governor.

## Requested Direction

Use the governor in the current chat to decide which model should perform the
work.

## Packet

```json
{
  "requested_model": "gpt-6-astra",
  "remaining_limit_percent": 12,
  "task_kind": "broad_repo_exploration",
  "explicit_approval": false,
  "broad_context": true,
  "sol_baseline_tokens": {"input": 90000, "output": 9000},
  "premium_plan_tokens": {"input": 45000, "output": 5000}
}
```

## Decision

```text
recommended_model: gpt-5.6-sol
decision: block_or_route_to_sol
```

## Reasons

- emergency budget requires explicit approval
- broad context should be compressed before premium use
- repo polish is a low-leverage premium task shape
- the hypothetical premium plan exceeded the Sol-parity ceiling

## Outcome

The repo upgrade should be performed Sol-first. Astra should be reserved for a
later compact decision packet, such as a final security/architecture
contradiction review after the repo has a bounded capsule.

