from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_plugin_skill_preserves_direct_astra_without_legacy_parity_gates():
    skill = (ROOT / "plugin/skills/premium-model-budget-governor/SKILL.md").read_text(encoding="utf-8")
    skill = " ".join(skill.split())
    assert "Evaluate direct Astra first" in skill
    for obsolete in ("Before a premium call, build a capsule", "For expensive tasks, let Sol/Terra",
                     "- the task is broad exploration", "- the capsule quality score is below 70",
                     "- the premium plan exceeds the Sol-parity token ceiling"):
        assert obsolete not in skill
    assert "Capsules are optional" in skill
    assert "Broad exploration is permitted" in skill
    assert "advisory" in skill
    assert "Do not silently downgrade" in skill


def test_adoption_documents_preserve_astra_and_measure_whole_workflows():
    adoption = " ".join((ROOT / "docs/ADOPTION_GUIDE.md").read_text(encoding="utf-8").split())
    faq = " ".join((ROOT / "docs/FAQ.md").read_text(encoding="utf-8").split())
    assert "Compare equally focused direct Astra first" in adoption
    assert "not prerequisites for access to Astra" in adoption
    assert "preparation, retry, verification and recovery overhead" in adoption
    assert "Fewer calls, smaller prompts or later Astra involvement are not success criteria" in adoption
    assert "It is not a mandatory ceiling" in faq
    assert "It is not the default for expensive tasks" in faq
    assert "These tools do not dispatch model runs" in faq
    assert "Pattern scans alone cannot establish" in faq
