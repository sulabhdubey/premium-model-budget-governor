from pathlib import Path


ROOT = Path(__file__).parents[1]
SITE = ROOT / "site"


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

    assert "pip install git+https://github.com/" in html
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


def test_package_version_matches_release() -> None:
    metadata = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    package = (ROOT / "src" / "premium_model_budget_governor" / "__init__.py").read_text(encoding="utf-8")

    assert 'version = "0.3.0"' in metadata
    assert '__version__ = "0.3.0"' in package
