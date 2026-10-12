"""
Report Exporter module.
Supports CSV export for metrics and alerts, and PDF report generation via ReportLab.
"""

import csv
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger("HealthMonitor.ReportExporter")


class ReportExporter:
    """Exports performance data to CSV and formatted PDF reports."""

    @staticmethod
    def export_metrics_to_csv(metrics: List[Dict[str, Any]], target_path: Path) -> bool:
        """Export system metrics rows to a CSV file."""
        if not metrics:
            logger.warning("No metrics provided for CSV export.")
            return False

        try:
            target_path = Path(target_path)
            target_path.parent.mkdir(parents=True, exist_ok=True)
            fieldnames = list(metrics[0].keys())

            with open(target_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for row in metrics:
                    writer.writerow(row)
            return True
        except Exception as e:
            logger.error(f"Error exporting metrics to CSV: {e}", exc_info=True)
            return False

    @staticmethod
    def export_alerts_to_csv(alerts: List[Dict[str, Any]], target_path: Path) -> bool:
        """Export alerts to a CSV file."""
        if not alerts:
            # Write empty file with header
            fieldnames = ["id", "timestamp", "severity", "resource", "message", "acknowledged", "resolved"]
        else:
            fieldnames = list(alerts[0].keys())

        try:
            target_path = Path(target_path)
            target_path.parent.mkdir(parents=True, exist_ok=True)
            with open(target_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for row in alerts:
                    writer.writerow(row)
            return True
        except Exception as e:
            logger.error(f"Error exporting alerts to CSV: {e}", exc_info=True)
            return False

    @staticmethod
    def export_pdf_report(
        target_path: Path,
        summary_stats: Optional[Dict[str, Any]],
        recent_metrics: List[Dict[str, Any]],
        insights: List[Dict[str, Any]],
        recommendations: List[Dict[str, Any]],
        alerts: List[Dict[str, Any]]
    ) -> bool:
        """Generate a structured system health PDF report using ReportLab."""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib import colors
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

            target_path = Path(target_path)
            target_path.parent.mkdir(parents=True, exist_ok=True)

            doc = SimpleDocTemplate(
                str(target_path),
                pagesize=letter,
                rightMargin=36,
                leftMargin=36,
                topMargin=36,
                bottomMargin=36
            )

            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'ReportTitle',
                parent=styles['Heading1'],
                fontSize=20,
                leading=24,
                textColor=colors.HexColor('#0F172A'),
                spaceAfter=10
            )
            h2_style = ParagraphStyle(
                'ReportHeading2',
                parent=styles['Heading2'],
                fontSize=14,
                leading=18,
                textColor=colors.HexColor('#1E293B'),
                spaceBefore=12,
                spaceAfter=6
            )
            body_style = ParagraphStyle(
                'ReportBody',
                parent=styles['Normal'],
                fontSize=10,
                leading=14,
                textColor=colors.HexColor('#334155')
            )
            bold_style = ParagraphStyle(
                'ReportBold',
                parent=styles['Normal'],
                fontSize=10,
                leading=14,
                fontName='Helvetica-Bold',
                textColor=colors.HexColor('#0F172A')
            )

            elements = []

            # 1. Header & Metadata
            now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            elements.append(Paragraph("Smart Computer Health Monitor - Diagnostic Report", title_style))
            elements.append(Paragraph(f"<b>Generated:</b> {now_str}", body_style))
            elements.append(Paragraph("<b>Domain:</b> Operating Systems & Resource Health Interpretation", body_style))
            elements.append(Spacer(1, 12))

            # 2. Executive Summary
            elements.append(Paragraph("1. Executive Summary & Resource Aggregates", h2_style))
            if summary_stats:
                summary_data = [
                    [Paragraph("<b>Metric</b>", bold_style), Paragraph("<b>Value</b>", bold_style)],
                    [Paragraph("Total Metric Samples", body_style), Paragraph(str(summary_stats.get("count", 0)), body_style)],
                    [Paragraph("Average CPU Utilization", body_style), Paragraph(f"{summary_stats.get('avg_cpu', 0.0)}%", body_style)],
                    [Paragraph("Peak CPU Utilization", body_style), Paragraph(f"{summary_stats.get('peak_cpu', 0.0)}%", body_style)],
                    [Paragraph("Average RAM Utilization", body_style), Paragraph(f"{summary_stats.get('avg_ram', 0.0)}%", body_style)],
                    [Paragraph("Peak RAM Utilization", body_style), Paragraph(f"{summary_stats.get('peak_ram', 0.0)}%", body_style)],
                    [Paragraph("Average Health Score", body_style), Paragraph(f"{summary_stats.get('avg_health_score', 100.0)} / 100", body_style)],
                    [Paragraph("Minimum Health Score", body_style), Paragraph(f"{summary_stats.get('min_health_score', 100.0)} / 100", body_style)],
                ]
            else:
                summary_data = [
                    [Paragraph("<b>Status</b>", bold_style), Paragraph("No historical data recorded during session.", body_style)]
                ]

            t_sum = Table(summary_data, colWidths=[200, 300])
            t_sum.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E2E8F0')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
                ('PADDING', (0, 0), (-1, -1), 5),
            ]))
            elements.append(t_sum)
            elements.append(Spacer(1, 14))

            # 3. Active & Recent Insights
            elements.append(Paragraph("2. Explainable Health Insights (Interpretation Layer)", h2_style))
            if insights:
                insight_data = [
                    [
                        Paragraph("<b>Severity / Resource</b>", bold_style),
                        Paragraph("<b>Diagnosis & Evidence</b>", bold_style),
                        Paragraph("<b>Possible Cause & Action</b>", bold_style)
                    ]
                ]
                for ins in insights[:8]:
                    res_tag = f"[{ins.get('severity', 'info').upper()}] {ins.get('resource', '')}"
                    diag_text = f"<b>{ins.get('title', '')}</b><br/>{ins.get('explanation', '')}<br/><i>Observed: {ins.get('observed_value', '')}</i>"
                    action_text = f"<b>Possible factor:</b> {ins.get('possible_cause', '')}<br/><b>Action:</b> {ins.get('recommendation', '')}"
                    insight_data.append([
                        Paragraph(res_tag, body_style),
                        Paragraph(diag_text, body_style),
                        Paragraph(action_text, body_style)
                    ])
                t_ins = Table(insight_data, colWidths=[110, 200, 230])
                t_ins.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E2E8F0')),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('PADDING', (0, 0), (-1, -1), 4),
                ]))
                elements.append(t_ins)
            else:
                elements.append(Paragraph("No abnormal health conditions detected. System operated within healthy margins.", body_style))

            elements.append(Spacer(1, 14))

            # 4. Actionable Recommendations
            elements.append(Paragraph("3. Actionable Advisory Recommendations", h2_style))
            if recommendations:
                rec_data = [
                    [
                        Paragraph("<b>Priority</b>", bold_style),
                        Paragraph("<b>Recommendation</b>", bold_style),
                        Paragraph("<b>Expected Benefit & Safety Note</b>", bold_style)
                    ]
                ]
                for rec in recommendations[:6]:
                    rec_data.append([
                        Paragraph(rec.get("priority", "Medium"), body_style),
                        Paragraph(f"<b>{rec.get('title', '')}</b><br/>{rec.get('reason', '')}", body_style),
                        Paragraph(f"{rec.get('expected_benefit', '')}<br/><i>Safety: {rec.get('safety_note', '')}</i>", body_style)
                    ])
                t_rec = Table(rec_data, colWidths=[70, 230, 240])
                t_rec.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E2E8F0')),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('PADDING', (0, 0), (-1, -1), 4),
                ]))
                elements.append(t_rec)
            else:
                elements.append(Paragraph("No active recommendations required at this time.", body_style))

            elements.append(Spacer(1, 14))

            # 5. Scientific Limitations Note
            elements.append(Paragraph("4. Academic Disclaimer & Limitations", h2_style))
            elements.append(Paragraph(
                "This report was generated deterministically by the Smart Computer Health Monitor interpretation layer. "
                "Correlations between resource metrics and processes are advisory and do not guarantee hardware failure or malware presence. "
                "No automated modifications or file deletions have been performed.",
                body_style
            ))

            doc.build(elements)
            logger.info(f"PDF report generated successfully at {target_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to generate PDF report: {e}", exc_info=True)
            return False
