# Reviewable Experiment Summary

Local development feature in Workbench's Evidence view. Select a comparison JSON
packet (at most 64 KB), inspect enrollment and quality regressions, then use
**Review export**. The download remains disabled until review is acknowledged.
The downloaded JSON is exactly the content displayed in the preview. Nothing is
posted or sent to a model. A new file clears the preview and consent; reopening
the dialog requires review again.

The server builds an allowlisted summary from the existing comparison result. It
omits task, arm, snapshot, rubric, receipt and model identifiers; source contents,
prompts, paths and arbitrary extra fields do not enter the summary. Candidates
are numbered, not named. It retains missing enrollment, unmatched runs, cost
basis, quality regressions, time differences and unknown values.

Numeric patterns can still identify an experiment. This is content minimization,
not an anonymity or confidentiality guarantee. All grading and receipt provenance
remain caller-supplied; a review checkbox does not establish independent quality.
The summary explicitly sets savings_proven and independent_grading_verified false.
Its review_required flag remains true for any further sharing context.

Only standard estimated-credit and supplied billed-credit basis labels are exported;
they are not dollars or weekly allowances. Mixed bases are not averaged. No upload,
automatic promotion, remote analytics or cloud account is required.

The comparison upload is processed in memory by the local authenticated service,
not saved as a journal or retention policy. Browser downloads are user-owned files;
clearing or closing this preview does not delete those files. Long-work journal
export, scheduling a weekly digest and retention controls are separate features.
