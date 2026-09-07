# Human Onboarding Trial

Status: protocol ready; no volunteer sessions recorded.
Purpose: test whether people can install, complete a task, and understand the result
without confusing estimated credits with weekly allowance or believing all chats
are automatically governed.

## Participants

Recruit at least one technical and one nontechnical volunteer for formative trials.
This is an initial usability check, not a representative population study.
Record a pseudonymous participant ID and self-reported experience only. Obtain
consent before observing or recording; recordings and personal details stay private.

## Tasks

1. From the public README, explain what the governor can and cannot do.
2. Install using the supported path and resolve any compatibility warning.
3. Preview an Astra-preferred review of a non-sensitive sample project.
4. Explain the proposed model, total estimate, uncertainty and approval boundary.
5. After separate spending consent, execute one bounded task and find its receipt.
   Without spending consent, test the clearly labeled offline path and mark actual
   execution untested. Never present a fixture result as a real model result.
6. Explain whether the receipt proves money saved or weekly allowance remaining.
7. Find help and removal instructions; uninstall the isolated runtime.

Use the same fixture and task wording for comparisons. Do not guide participants
silently: log each intervention. Stop on possible unintended spending, unsafe file
selection, credential disclosure or confusing approval behavior.

The [public starter suite](../examples/field-trial/README.md) supplies fixed tasks,
inputs and grader criteria. Use `prepare_trial_task.py` to stage one task without
its grading criteria before the session. Record the snapshot hash and task ID.
Preparing files is facilitator work: include its time and any help in the trial
record rather than treating the user's start screen as effortless installation.
Five authored tasks are not a substitute for independent project validation.

## Record

For each task record completion, elapsed seconds, errors, help requests,
facilitator interventions and a short participant explanation in their own words.
Record operating system and release version. Do not collect prompts, credentials,
personal repository paths or billing screenshots in the public report.

Acceptance for the first release: no unresolved critical consent/privacy issue;
both experience groups can finish the supported primary journey and correctly
distinguish actual tokens, projected credits, unavailable weekly attribution and
the scope of governor control. Fix observed blockers and repeat affected tasks.
Do not average away a nontechnical participant's failure with developer successes.

Publish sanitized observations and limitations, including unsuccessful attempts.
Automated browser QA is a separate prerequisite and cannot replace these trials.
