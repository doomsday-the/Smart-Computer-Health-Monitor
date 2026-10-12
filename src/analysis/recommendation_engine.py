"""
Smart Recommendation Engine.
Produces targeted, explainable, actionable recommendations based on active insights and system state.
Strictly advisory and safe: never automatically deletes files, alters system registries, or terminates processes.
"""

from dataclasses import dataclass, asdict
from typing import List, Dict, Any
from src.analysis.interpretation_engine import Insight


@dataclass
class Recommendation:
    id: str
    title: str
    priority: str  # High, Medium, Low
    related_resource: str
    related_insight_id: str
    reason: str
    related_measurement: str
    suggested_steps: List[str]
    expected_benefit: str
    safety_note: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class RecommendationEngine:
    """Generates structured advisory guidance for active system insights."""

    @staticmethod
    def generate_recommendations(insights: List[Insight]) -> List[Recommendation]:
        recommendations: List[Recommendation] = []

        for ins in insights:
            if ins.status not in ("new", "ongoing"):
                continue

            if ins.resource == "CPU":
                top_procs = ins.evidence.get("top_cpu_processes", [])
                proc_names = [p.get("name", "") for p in top_procs if isinstance(p, dict)]
                procs_text = ", ".join(proc_names[:2]) if proc_names else "heavy processes"
                
                recommendations.append(Recommendation(
                    id=f"rec_{ins.id}",
                    title=f"Investigate CPU-Intensive Tasks ({procs_text})",
                    priority="High" if ins.severity == "critical" else "Medium",
                    related_resource="CPU",
                    related_insight_id=ins.id,
                    reason=f"Sustained processor workload ({ins.observed_value}) reduces scheduling availability for interactive desktop applications.",
                    related_measurement=ins.observed_value,
                    suggested_steps=[
                        f"Open the Process Explorer tab and observe CPU utilization of {procs_text}.",
                        "Determine if these tasks represent intended foreground workloads (e.g., video rendering, game, code compilation).",
                        "If the task is an unneeded background service or hung application, save your work in other programs before manually closing it."
                    ],
                    expected_benefit="Restores CPU scheduling cycles, reducing interface lag and thermal load.",
                    safety_note="Do NOT terminate critical operating system processes (e.g., System, csrss, svchost, explorer)."
                ))

            elif ins.resource == "RAM":
                top_procs = ins.evidence.get("top_memory_processes", [])
                proc_names = [p.get("name", "") for p in top_procs if isinstance(p, dict)]
                procs_text = ", ".join(proc_names[:2]) if proc_names else "high-memory applications"

                recommendations.append(Recommendation(
                    id=f"rec_{ins.id}",
                    title=f"Relieve Working-Set Memory Pressure ({procs_text})",
                    priority="High" if ins.severity == "critical" else "Medium",
                    related_resource="RAM",
                    related_insight_id=ins.id,
                    reason=f"Physical RAM allocation is high ({ins.observed_value}), increasing risk of swap/paging thrashing.",
                    related_measurement=ins.observed_value,
                    suggested_steps=[
                        "Inspect open web browser windows and close inactive tabs or memory-heavy extensions.",
                        "Close dormant development environments, containers, or virtual machines not currently required.",
                        "Avoid launching additional memory-intensive software until current applications finish."
                    ],
                    expected_benefit="Prevents disk swap paging thrash, keeping foreground applications responsive.",
                    safety_note="Ensure any unsaved documents or browser form submissions are saved prior to closing applications."
                ))

            elif ins.resource == "Disk":
                free_gb = ins.evidence.get("free_gb", "unknown")
                mount = ins.evidence.get("mount_path", "system drive")

                recommendations.append(Recommendation(
                    id=f"rec_{ins.id}",
                    title=f"Reclaim Free Storage Capacity on {mount}",
                    priority="High" if ins.severity == "critical" else "Medium",
                    related_resource="Disk",
                    related_insight_id=ins.id,
                    reason=f"Storage volume has only {free_gb} GB remaining ({ins.observed_value}). Operating systems need free space for updates and paging.",
                    related_measurement=ins.observed_value,
                    suggested_steps=[
                        "Launch native Disk Cleanup or Storage Sense to clear temporary setup files and caches.",
                        "Inspect personal Downloads and Videos directories for large forgotten installers or archives.",
                        "Empty the desktop Recycle Bin / Trash after verifying deleted items are no longer needed."
                    ],
                    expected_benefit="Ensures sufficient storage margin for operating system updates, paging files, and software logs.",
                    safety_note="Review files manually before deleting. Never delete unfamiliar files in operating system folders."
                ))

            elif ins.resource == "Battery":
                is_crit = (ins.severity == "critical")

                recommendations.append(Recommendation(
                    id=f"rec_{ins.id}",
                    title="Connect AC Power Source Immediately" if is_crit else "Connect Charger or Enable Battery Saver",
                    priority="High" if is_crit else "Medium",
                    related_resource="Battery",
                    related_insight_id=ins.id,
                    reason=f"Battery level is low ({ins.observed_value}) while operating on mobile DC power.",
                    related_measurement=ins.observed_value,
                    suggested_steps=[
                        "Plug the laptop into its AC mains power adapter.",
                        "If away from a power source, immediately save all open work.",
                        "Enable Windows Battery Saver and reduce display brightness to extend uptime."
                    ],
                    expected_benefit="Protects against sudden emergency shutdown and potential unsaved data loss.",
                    safety_note="Ensure correct charger wattage is used to avoid battery wear."
                ))

            elif ins.resource == "System":
                recommendations.append(Recommendation(
                    id=f"rec_{ins.id}",
                    title="Address Concurrent CPU and Memory Contention",
                    priority="High",
                    related_resource="System",
                    related_insight_id=ins.id,
                    reason="Both processor and memory are concurrently saturated, causing system-wide latency.",
                    related_measurement=ins.observed_value,
                    suggested_steps=[
                        "Pause background synchronization, file backups, or batch jobs.",
                        "Check the Process Explorer to isolate whether a single application or multiple programs are competing for resources.",
                        "Allow current compilation or heavy tasks to complete before initiating new workflows."
                    ],
                    expected_benefit="Alleviates bottlenecking across memory bus and CPU execution pipelines.",
                    safety_note="Avoid force-restarting the computer while heavy disk or compile operations are actively writing data."
                ))

        # Sort recommendations by priority (High -> Medium -> Low)
        priority_rank = {"High": 1, "Medium": 2, "Low": 3}
        recommendations.sort(key=lambda r: priority_rank.get(r.priority, 4))
        return recommendations
