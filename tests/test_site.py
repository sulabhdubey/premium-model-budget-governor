from pathlib import Path
import json


ROOT = Path(__file__).parents[1]
SITE = ROOT / "site"


def test_readme_explains_installation_scope_before_tour_and_evidence():
    readme = " ".join((ROOT / "README.md").read_text(encoding="utf-8").split())
    boundary = "Installing Governor does not automatically reduce token use in your existing Codex chats."
    assert boundary in readme
    assert readme.index(boundary) < readme.index("site/assets/tour-poster.png")
    assert "Task explicitly started through the supported Governor runner" in readme
    assert "prove savings from a single receipt" in readme


def test_landing_page_assets_and_core_sections_exist() -> None:
    html = (SITE / "index.html").read_text(encoding="utf-8")

    assert 'id="demo"' in html
    assert 'id="proof"' in html
    assert 'id="origin"' in html
    assert 'id="install"' in html
    assert "governor-aperture.png" in html
    assert (SITE / "assets" / "governor-aperture.png").stat().st_size > 100_000
    assert (SITE / "styles.css").is_file()
    assert (SITE / "app.js").is_file()


def test_landing_page_uses_honest_install_and_product_copy() -> None:
    html = (SITE / "index.html").read_text(encoding="utf-8")

    assert "python install_governor.py install --wheel premium_model_budget_governor-0.4.0rc6-py3-none-any.whl" in html
    assert "Add the governor in one minute" not in html
    assert "releases/download/v0.4.0-rc.6/install_governor.py" in html
    assert "releases/download/v0.4.0-rc.6/premium_model_budget_governor-0.4.0rc6-py3-none-any.whl" in html
    assert "Use frontier models for judgment, not waste." in html
    assert "No model calls, account connection, or live billing" in html
    assert "76% avoided overhead" not in html
    assert "BENCHMARK_RESULTS.md" in html
    assert 'id="host-context"' in html
    assert "Idea, research guidance &amp; product management: Sulabh Dubey" in html
    assert "Not an OpenAI product" in html


def test_pages_workflow_publishes_only_site_directory() -> None:
    workflow = (ROOT / ".github" / "workflows" / "pages.yml").read_text(encoding="utf-8")

    assert "actions/upload-pages-artifact@v3" in workflow
    assert "path: site" in workflow
    assert "pages: write" in workflow


def test_development_versions_are_distinct_from_public_beta() -> None:
    metadata = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    package = (ROOT / "src" / "premium_model_budget_governor" / "__init__.py").read_text(encoding="utf-8")

    assert 'version = "0.5.0.dev1"' in metadata
    assert '__version__ = "0.5.0.dev1"' in package
    plugin = json.loads((ROOT / "plugin/.codex-plugin/plugin.json").read_text(encoding="utf-8"))
    assert plugin["version"] == "0.5.0-dev.1"
    assert "releases/tag/v0.4.0-rc.6" in (ROOT / "README.md").read_text(encoding="utf-8")


def test_product_tour_has_accessible_controls_and_real_assets() -> None:
    html = (SITE / "index.html").read_text(encoding="utf-8")
    assert 'id="tour"' in html
    assert 'id="tour-play"' in html
    assert 'role="tablist"' in html
    assert 'aria-controls="tour-panel"' in html
    assert 'id="tour-panel"' in html
    assert 'Development captures' in html
    for name in ("direct", "prepared", "focused"):
        for size in ("desktop", "mobile"):
            assert (SITE / "assets" / f"tour-{name}-{size}.png").is_file()
    js = (SITE / "tour.js").read_text(encoding="utf-8")
    assert "prefers-reduced-motion" in js
    assert "visibilitychange" in js
    assert "ArrowRight" in js
    assert "clearInterval" in js
