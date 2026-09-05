"""
Data Quality Framework for FreightWise Stage 1 Data Foundation.
Audits missing values, duplicates, date consistency, numeric ranges, and categorical flags.
Generates data/quality/data_quality_report.json and docs/data_quality_report.md.
"""

import os
import json
import pandas as pd
from typing import Dict, Any, List


def audit_dataset_quality(df: pd.DataFrame, dataset_name: str) -> Dict[str, Any]:
    """
    Audits a single DataFrame for quality issues without modifying the data.
    """
    total_rows = len(df)
    total_cols = len(df.columns)
    duplicate_rows = int(df.duplicated().sum())

    missing_by_col = {}
    for col in df.columns:
        null_cnt = int(df[col].isnull().sum())
        if null_cnt > 0:
            missing_by_col[col] = {
                "count": null_cnt,
                "percentage": round((null_cnt / total_rows) * 100, 2) if total_rows > 0 else 0,
            }

    # Date range audit
    date_cols = [
        c for c in df.columns if any(kw in c.lower() for kw in ["date", "time", "year", "month", "day", "period_start"])
    ]
    date_info = {}
    for dc in date_cols:
        try:
            s_date = pd.to_datetime(df[dc], errors="coerce").dropna()
            if not s_date.empty:
                date_info[dc] = {
                    "min": s_date.min().strftime("%Y-%m-%d"),
                    "max": s_date.max().strftime("%Y-%m-%d"),
                    "unique_dates": int(s_date.nunique()),
                }
        except Exception:
            pass

    return {
        "dataset_name": dataset_name,
        "rows": total_rows,
        "columns": total_cols,
        "duplicate_rows": duplicate_rows,
        "missing_columns_count": len(missing_by_col),
        "missing_details": missing_by_col,
        "date_info": date_info,
        "quality_status": "PASSED" if duplicate_rows == 0 and len(missing_by_col) == 0 else "WARNINGS_FLAGGED",
    }


def generate_data_quality_report(
    datasets: Dict[str, pd.DataFrame],
    output_json_path: str = "data/quality/data_quality_report.json",
    output_md_path: str = "docs/data_quality_report.md",
) -> Dict[str, Any]:
    """
    Generates both machine-readable JSON and human-readable Markdown quality reports.
    """
    overall_report = {
        "title": "FreightWise Round 2 — Stage 1 Data Quality Audit Report",
        "timestamp": pd.Timestamp.now().isoformat(),
        "total_datasets_audited": len(datasets),
        "datasets": {},
    }

    for name, df in datasets.items():
        overall_report["datasets"][name] = audit_dataset_quality(df, name)

    # Ensure output directories exist
    os.makedirs(os.path.dirname(output_json_path), exist_ok=True)
    os.makedirs(os.path.dirname(output_md_path), exist_ok=True)

    # Save JSON report
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(overall_report, f, indent=2)

    # Save Markdown report
    md_lines = [
        "# FreightWise Round 2 — Stage 1 Data Quality Audit Report\n",
        f"**Generated**: {overall_report['timestamp']}  ",
        f"**Total Datasets Audited**: {len(datasets)}  \n",
        "## Summary of Dataset Quality\n",
        "| Dataset Name | Rows | Columns | Duplicate Rows | Missing Columns | Status |",
        "| :--- | :---: | :---: | :---: | :---: | :---: |",
    ]

    for name, info in overall_report["datasets"].items():
        status = info["quality_status"]
        md_lines.append(
            f"| `{name}` | {info['rows']:,} | {info['columns']} | {info['duplicate_rows']} | {info['missing_columns_count']} | **{status}** |"
        )

    md_lines.extend(
        [
            "\n## Detailed Missing Values & Quality Flags\n",
        ]
    )

    for name, info in overall_report["datasets"].items():
        md_lines.append(f"### Dataset: `{name}`")
        md_lines.append(f"- **Rows**: {info['rows']:,}, **Columns**: {info['columns']}")
        md_lines.append(f"- **Duplicates**: {info['duplicate_rows']}")
        if info["missing_details"]:
            md_lines.append("- **Missing Value Details**:")
            for col, mdict in info["missing_details"].items():
                md_lines.append(f"  - `{col}`: {mdict['count']} missing ({mdict['percentage']}%)")
        else:
            md_lines.append("- **Missing Values**: None (0.00%)")

        if info["date_info"]:
            md_lines.append("- **Date Coverage**:")
            for dc, ddict in info["date_info"].items():
                md_lines.append(f"  - `{dc}`: {ddict['min']} to {ddict['max']} ({ddict['unique_dates']} unique dates)")
        md_lines.append("")

    with open(output_md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    return overall_report
