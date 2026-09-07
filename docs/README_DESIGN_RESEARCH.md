# Product Presentation Research

Reviewed 2026-09-08. This is a deliberately varied reference set, not a claim to
have inspected every leading repository or established a star-based ranking.
Repository layouts and product websites change. No third-party branding,
screenshots, testimonials, metrics, or design code were copied into this project.

## Reference Set

| Primary source | Pattern considered | Governor decision |
| --- | --- | --- |
| [shadcn/ui](https://github.com/shadcn-ui/ui/blob/main/README.md) | Brief proposition, hero media, direct documentation path | Shorten the opening and link detail instead of repeating it |
| [uv](https://github.com/astral-sh/uv) | Early visual benchmark linked to its scope | Keep results adjacent to limitations, not a large unqualified savings badge |
| [Onlook](https://github.com/onlook-dev/onlook/blob/main/README.md) | Product/demo entry points and explicit early-access distinction | Separate the beta Workbench from the illustrative public demo |
| [Activepieces](https://github.com/activepieces/activepieces) | Visible routes to docs, deployment, and contribution | Provide distinct Workbench, MCP, and tester paths |
| [Gum](https://github.com/charmbracelet/gum) | Concrete command examples and platform installation choices | Keep runnable preview commands rather than abstract installation claims |
| [Zed](https://github.com/zed-industries/zed) | Product category and concise project navigation | State the audience and integration boundary early |
| [Ollama](https://github.com/ollama/ollama) | OS-specific download and setup sections | Retain Windows and Linux/macOS commands; do not assume a universal executable path |
| [Plate](https://github.com/udecode/plate) | Explicit starting-point choices | Use a small integration table, not a large undifferentiated feature list |
| [Flowise](https://github.com/FlowiseAI/Flowise) | Table of contents, quickstart, developer documentation separation | Keep advanced developer instructions collapsible; reference is presentation only, not a maintenance recommendation |
| [Dyad](https://github.com/dyad-sh/dyad) | Local product identity and download orientation | Put the actual local Workbench ahead of a conceptual illustration |
| [Dify](https://github.com/langgenius/dify) | Prerequisites, setup, and help path together | Keep technical prerequisites and recovery visible |
| [Zed website](https://zed.dev/) | Product-led presentation and focused navigation | Give the product name first-viewport prominence |
| [Onlook website](https://www.onlook.com/) | Visual product presentation | Add a three-view tour based on our own development captures |
| [Dyad website](https://www.dyad.sh/) | Direct explanation of local product use | Connect the tour to installation and feedback |

These are design interpretations, not evidence that copying a pattern increases
conversion or that these projects endorse the governor.

## Implementation

- README: compact linked product-tour poster, explicit audience and non-fit,
  collapsible origin and internal controls, preserved founder attribution.
- Website: larger product identity, three selectable Workbench views, optional
  playback, keyboard navigation, reduced-motion support, visibility-aware stop.
- Tour images are unchanged copies of existing development preview captures.
  They do not imply successful model execution or independent quality validation.
- Poster is a browser-rendered capture of the tour, not generated product UI.
- Public demo remains a separate illustrative planner with no model calls.
- No remote animation runtime, tracking, new forms, or paid media generation.

## Intentionally Not Added

Fake customer logos, fabricated testimonials, star-history decoration, universal
savings claims, automatically looping README animation, third-party contact
forms, and pricing for a nonexistent Pro product.

## Verification Contract

Check 1440, 390, and 320 widths; keyboard tab selection and wrapping; manual
play/pause; Escape; reduced motion; hidden-page/offscreen stop; image loading;
download paths; original planner decisions; and GitHub rendering. Public text
passes the private-term preflight before publication. No checks imply independent
human onboarding or a security certification.
