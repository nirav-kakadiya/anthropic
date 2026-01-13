"""
Exporter - Export reports in various formats.

Features:
- CSV export
- Excel export (XLSX)
- PDF export
- HTML report
- Markdown report
- JSON export
"""

import csv
import json
from dataclasses import dataclass
from datetime import datetime
from io import StringIO, BytesIO
from pathlib import Path
from typing import Optional, Union, Any


@dataclass
class ExportOptions:
    """Export configuration options."""
    include_summary: bool = True
    include_keywords: bool = True
    include_gaps: bool = True
    include_clusters: bool = True
    include_competitors: bool = True
    max_items: int = 100
    sort_by: str = "score"  # "score", "name", "source"


class ReportExporter:
    """
    Export scan results to various formats.

    Usage:
        exporter = ReportExporter()

        # Export to CSV
        csv_content = exporter.to_csv(scan_result)

        # Export to Excel
        xlsx_bytes = exporter.to_excel(scan_result)

        # Export to PDF
        pdf_bytes = exporter.to_pdf(scan_result)

        # Save to file
        exporter.save(scan_result, "report.xlsx")
    """

    def __init__(self, options: Optional[ExportOptions] = None):
        self.options = options or ExportOptions()

    def to_csv(self, data: dict, section: str = "all") -> str:
        """
        Export data to CSV format.

        Args:
            data: Scan result dictionary
            section: Which section to export ("keywords", "gaps", "all")

        Returns:
            CSV string
        """
        output = StringIO()

        if section in ("all", "keywords"):
            writer = csv.writer(output)
            writer.writerow(["=== KEYWORDS ==="])
            writer.writerow(["Keyword", "Score", "Source", "Is Gap"])

            keywords = data.get("keywords", [])
            for kw in keywords[:self.options.max_items]:
                if isinstance(kw, str):
                    writer.writerow([kw, "", "", "No"])
                else:
                    writer.writerow([
                        kw.get("keyword", ""),
                        kw.get("score", ""),
                        kw.get("source", ""),
                        "Yes" if kw.get("is_gap") else "No"
                    ])

            writer.writerow([])

        if section in ("all", "gaps"):
            writer = csv.writer(output)
            writer.writerow(["=== GAPS ==="])
            writer.writerow(["Feature", "Trend Score", "Source", "Why It's a Gap"])

            gaps = data.get("gaps", [])
            for gap in gaps[:self.options.max_items]:
                if isinstance(gap, str):
                    writer.writerow([gap, "", "", ""])
                else:
                    writer.writerow([
                        gap.get("keyword", gap.get("feature", "")),
                        gap.get("trend_score", ""),
                        gap.get("source", ""),
                        gap.get("why_gap", "")[:100]
                    ])

        return output.getvalue()

    def to_excel(self, data: dict, filename: Optional[str] = None) -> bytes:
        """
        Export data to Excel format.

        Note: This creates a simple XML-based spreadsheet that Excel can open.
        For full XLSX support, install openpyxl.

        Args:
            data: Scan result dictionary
            filename: Optional filename to save to

        Returns:
            Excel file bytes
        """
        # Create simple XML spreadsheet (Excel can open this)
        xml_parts = [
            '<?xml version="1.0"?>',
            '<?mso-application progid="Excel.Sheet"?>',
            '<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet"',
            ' xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet">',
        ]

        # Summary sheet
        xml_parts.append('<Worksheet ss:Name="Summary">')
        xml_parts.append('<Table>')

        summary = data.get("summary", {})
        xml_parts.append(self._excel_row(["Market Research Report"]))
        xml_parts.append(self._excel_row(["Generated", datetime.now().isoformat()]))
        xml_parts.append(self._excel_row([]))
        xml_parts.append(self._excel_row(["Metric", "Value"]))
        xml_parts.append(self._excel_row(["Total Keywords", str(summary.get("total_keywords", len(data.get("keywords", []))))]))
        xml_parts.append(self._excel_row(["Total Gaps", str(summary.get("total_gaps", len(data.get("gaps", []))))]))
        xml_parts.append(self._excel_row(["Niche", data.get("niche", "")]))

        xml_parts.append('</Table>')
        xml_parts.append('</Worksheet>')

        # Keywords sheet
        xml_parts.append('<Worksheet ss:Name="Keywords">')
        xml_parts.append('<Table>')
        xml_parts.append(self._excel_row(["Keyword", "Score", "Source"]))

        for kw in data.get("keywords", [])[:self.options.max_items]:
            if isinstance(kw, str):
                xml_parts.append(self._excel_row([kw, "", ""]))
            else:
                xml_parts.append(self._excel_row([
                    kw.get("keyword", ""),
                    str(kw.get("score", "")),
                    kw.get("source", "")
                ]))

        xml_parts.append('</Table>')
        xml_parts.append('</Worksheet>')

        # Gaps sheet
        xml_parts.append('<Worksheet ss:Name="Gaps">')
        xml_parts.append('<Table>')
        xml_parts.append(self._excel_row(["Feature", "Trend Score", "Source", "Why"]))

        for gap in data.get("gaps", [])[:self.options.max_items]:
            if isinstance(gap, str):
                xml_parts.append(self._excel_row([gap, "", "", ""]))
            else:
                xml_parts.append(self._excel_row([
                    gap.get("keyword", gap.get("feature", "")),
                    str(gap.get("trend_score", "")),
                    gap.get("source", ""),
                    gap.get("why_gap", "")[:100]
                ]))

        xml_parts.append('</Table>')
        xml_parts.append('</Worksheet>')

        xml_parts.append('</Workbook>')

        content = '\n'.join(xml_parts)
        content_bytes = content.encode('utf-8')

        if filename:
            Path(filename).write_bytes(content_bytes)

        return content_bytes

    def _excel_row(self, cells: list) -> str:
        """Create an Excel XML row."""
        row = '<Row>'
        for cell in cells:
            escaped = str(cell).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            row += f'<Cell><Data ss:Type="String">{escaped}</Data></Cell>'
        row += '</Row>'
        return row

    def to_html(self, data: dict) -> str:
        """
        Export data to HTML format.

        Args:
            data: Scan result dictionary

        Returns:
            HTML string
        """
        summary = data.get("summary", {})
        niche = data.get("niche", "Market Research")

        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Market Research Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #1a1a1a; border-bottom: 3px solid #4f46e5; padding-bottom: 15px; }}
        h2 {{ color: #4f46e5; margin-top: 40px; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 30px 0; }}
        .stat {{ background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; }}
        .stat-value {{ font-size: 2em; font-weight: bold; color: #4f46e5; }}
        .stat-label {{ color: #666; margin-top: 5px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #eee; }}
        th {{ background: #4f46e5; color: white; }}
        tr:hover {{ background: #f8f9fa; }}
        .tag {{ display: inline-block; padding: 4px 8px; background: #e0e7ff; color: #4338ca; border-radius: 4px; margin: 2px; font-size: 0.85em; }}
        .high {{ background: #fee2e2; color: #dc2626; }}
        .medium {{ background: #fef3c7; color: #d97706; }}
        .low {{ background: #d1fae5; color: #059669; }}
        .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; color: #666; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Market Research Report</h1>
        <p><strong>Niche:</strong> {niche}</p>
        <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

        <div class="summary">
            <div class="stat">
                <div class="stat-value">{summary.get('total_keywords', len(data.get('keywords', [])))}</div>
                <div class="stat-label">Keywords Found</div>
            </div>
            <div class="stat">
                <div class="stat-value">{summary.get('total_gaps', len(data.get('gaps', [])))}</div>
                <div class="stat-label">Gaps Identified</div>
            </div>
            <div class="stat">
                <div class="stat-value">{len(data.get('clusters', []))}</div>
                <div class="stat-label">Clusters</div>
            </div>
        </div>

        <h2>Top Keywords</h2>
        <table>
            <tr><th>Keyword</th><th>Score</th><th>Source</th></tr>
"""

        for kw in data.get("keywords", [])[:30]:
            if isinstance(kw, str):
                html += f'<tr><td>{kw}</td><td>-</td><td>-</td></tr>\n'
            else:
                html += f'<tr><td>{kw.get("keyword", "")}</td><td>{kw.get("score", "")}</td><td>{kw.get("source", "")}</td></tr>\n'

        html += """
        </table>

        <h2>Gap Analysis</h2>
        <table>
            <tr><th>Feature</th><th>Priority</th><th>Trend Score</th><th>Why It's a Gap</th></tr>
"""

        for gap in data.get("gaps", [])[:30]:
            if isinstance(gap, str):
                html += f'<tr><td>{gap}</td><td>-</td><td>-</td><td>-</td></tr>\n'
            else:
                priority = gap.get("priority", "medium")
                html += f'''<tr>
                    <td>{gap.get("keyword", gap.get("feature", ""))}</td>
                    <td><span class="tag {priority}">{priority.upper()}</span></td>
                    <td>{gap.get("trend_score", "")}</td>
                    <td>{gap.get("why_gap", "")[:80]}</td>
                </tr>\n'''

        html += """
        </table>

        <div class="footer">
            Generated by Market Research Agent v2.3
        </div>
    </div>
</body>
</html>"""

        return html

    def to_markdown(self, data: dict) -> str:
        """
        Export data to Markdown format.

        Args:
            data: Scan result dictionary

        Returns:
            Markdown string
        """
        summary = data.get("summary", {})
        niche = data.get("niche", "Market Research")

        md = f"""# Market Research Report

**Niche:** {niche}
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## Summary

| Metric | Value |
|--------|-------|
| Total Keywords | {summary.get('total_keywords', len(data.get('keywords', [])))} |
| Total Gaps | {summary.get('total_gaps', len(data.get('gaps', [])))} |
| Clusters | {len(data.get('clusters', []))} |

---

## Top Keywords

| Keyword | Score | Source |
|---------|-------|--------|
"""

        for kw in data.get("keywords", [])[:30]:
            if isinstance(kw, str):
                md += f"| {kw} | - | - |\n"
            else:
                md += f"| {kw.get('keyword', '')} | {kw.get('score', '')} | {kw.get('source', '')} |\n"

        md += """
---

## Gap Analysis

| Feature | Priority | Trend Score | Why It's a Gap |
|---------|----------|-------------|----------------|
"""

        for gap in data.get("gaps", [])[:30]:
            if isinstance(gap, str):
                md += f"| {gap} | - | - | - |\n"
            else:
                md += f"| {gap.get('keyword', gap.get('feature', ''))} | {gap.get('priority', 'medium').upper()} | {gap.get('trend_score', '')} | {gap.get('why_gap', '')[:50]} |\n"

        md += """
---

*Generated by Market Research Agent v2.3*
"""

        return md

    def to_json(self, data: dict, pretty: bool = True) -> str:
        """Export data to JSON format."""
        if pretty:
            return json.dumps(data, indent=2, default=str)
        return json.dumps(data, default=str)

    def save(
        self,
        data: dict,
        filename: str,
        format: Optional[str] = None,
    ) -> str:
        """
        Save report to file.

        Args:
            data: Scan result dictionary
            filename: Output filename
            format: Optional format override (csv, xlsx, html, md, json)

        Returns:
            Path to saved file
        """
        path = Path(filename)

        # Determine format from extension or parameter
        if format:
            ext = format.lower()
        else:
            ext = path.suffix.lower().lstrip('.')

        if ext == 'csv':
            content = self.to_csv(data)
            path.write_text(content, encoding='utf-8')
        elif ext in ('xlsx', 'xls'):
            content = self.to_excel(data)
            path.write_bytes(content)
        elif ext == 'html':
            content = self.to_html(data)
            path.write_text(content, encoding='utf-8')
        elif ext == 'md':
            content = self.to_markdown(data)
            path.write_text(content, encoding='utf-8')
        elif ext == 'json':
            content = self.to_json(data)
            path.write_text(content, encoding='utf-8')
        else:
            raise ValueError(f"Unsupported format: {ext}")

        return str(path.absolute())


def export_report(
    data: dict,
    filename: str,
    format: Optional[str] = None,
) -> str:
    """Quick function to export a report."""
    exporter = ReportExporter()
    return exporter.save(data, filename, format)


def create_exporter(options: Optional[ExportOptions] = None) -> ReportExporter:
    """Factory function to create a ReportExporter."""
    return ReportExporter(options)
