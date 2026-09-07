"""Narrow opt-in host overrides; never accept arbitrary client configuration."""


def context_profile_config(profile, *, model, effort):
    if not isinstance(profile, str) or profile not in {"inherit", "focused_catalog"}:
        raise ValueError("unsupported context profile")
    if profile == "inherit":
        return {}
    if model != "gpt-6-astra" or effort != "low":
        raise ValueError("focused context profile requires Astra with low reasoning")
    return {"skills.max_context_tokens": 1024}
