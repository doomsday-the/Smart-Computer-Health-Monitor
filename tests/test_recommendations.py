"""
Tests for RecommendationEngine.
Validates generation of targeted, prioritized, and advisory recommendations.
"""

from src.analysis.interpretation_engine import Insight
from src.analysis.recommendation_engine import RecommendationEngine


def make_insight(ins_id, resource, severity, status="new"):
    return Insight(
        id=ins_id,
        resource=resource,
        severity=severity,
        title=f"Test {resource} Issue",
        observed_value="95%",
        rule_triggered="Exceeds threshold",
        explanation="Testing OS explanation",
        evidence={"top_cpu_processes": [{"name": "compile.exe"}], "free_gb": 2.5},
        possible_cause="High load task",
        confidence_label="High Confidence",
        recommendation="Review high resource processes.",
        status=status,
        created_at="2026-10-10T12:00:00Z",
        updated_at="2026-10-10T12:00:00Z"
    )


def test_cpu_and_disk_recommendation_mapping():
    insights = [
        make_insight("cpu_1", "CPU", "critical"),
        make_insight("disk_1", "Disk", "warning")
    ]
    recs = RecommendationEngine.generate_recommendations(insights)

    assert len(recs) == 2
    # Critical CPU recommendation should be High priority
    cpu_rec = [r for r in recs if r.related_resource == "CPU"][0]
    assert cpu_rec.priority == "High"
    assert "compile.exe" in cpu_rec.title
    assert len(cpu_rec.suggested_steps) >= 2
    assert "Safety Notice" in cpu_rec.safety_note or len(cpu_rec.safety_note) > 0

    # Disk recommendation should be Medium priority
    disk_rec = [r for r in recs if r.related_resource == "Disk"][0]
    assert disk_rec.priority == "Medium"
    assert "2.5 GB" in disk_rec.reason


def test_resolved_insights_do_not_generate_recommendations():
    insights = [
        make_insight("ram_1", "RAM", "critical", status="resolved")
    ]
    recs = RecommendationEngine.generate_recommendations(insights)
    assert len(recs) == 0
