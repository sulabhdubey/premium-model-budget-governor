"""Allowlisted user-facing errors; never include source or host exception text."""

ISSUES = {
    "project_invalid": ("project", "Select a registered project."),
    "task_required": ("task", "Enter a task between 1 and 16000 characters."),
    "task_scan": ("task", "Task scan needs attention. Remove credentials or untrusted instructions and review again."),
    "budget_invalid": ("budget", "Enter a task budget greater than 0 and at most 1000 estimated credits."),
    "evidence_invalid": ("evidence", "Evidence selection or scan failed. Choose readable UTF-8 files inside this project, within the documented size limits; exclude credentials and unsafe content."),
    "images_invalid": ("images", "Image selection failed. Choose PNG, JPEG or WebP files inside this project, within the documented size limits."),
    "context_invalid": ("context", "Enter a whole-number context allowance between 1000 and 500000 tokens."),
    "output_invalid": ("output", "Enter a whole-number output allowance between 100 and 32000 tokens."),
    "profile_invalid": ("context-profile", "Select an inherited context profile, or use focused catalog with Direct, Astra Preferred and Low reasoning."),
    "host_unavailable": ("effort", "Requested model, effort or image capability is unavailable. Check setup and select compatible options; nothing was downgraded."),
}


class InputIssue(ValueError):
    def __init__(self, code):
        self.code = code
        self.field, message = ISSUES[code]
        super().__init__(message)
