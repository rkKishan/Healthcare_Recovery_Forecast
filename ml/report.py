"""
PDF report generation.

Three reports share one visual language, one per job:

  * `cohort_report`   -- a dataset-wide summary for capacity planning (analyst).
  * `caseload_report` -- a ward-round handover across a clinician's own
                         admissions, ordered by what needs doing today (doctor).
  * `patient_report`  -- a single admission, printable for a patient file.

Charts are rendered with Matplotlib into in-memory PNGs and placed by
ReportLab. Nothing touches the filesystem: the caller gets bytes and decides
what to do with them, which keeps the generator testable and keeps patient
data out of temp files.

The palette is imported from the risk-tier definitions rather than restated,
so a tier can never be one colour in the dashboard and another in the PDF.
"""

from __future__ import annotations

import io
from datetime import UTC, datetime
from typing import Any

import matplotlib

# A server has no display; select the non-interactive backend before pyplot is
# imported anywhere, or Matplotlib tries to open a GUI window and fails.
matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
from reportlab.lib import colors  # noqa: E402
from reportlab.lib.enums import TA_CENTER  # noqa: E402
from reportlab.lib.pagesizes import A4  # noqa: E402
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet  # noqa: E402
from reportlab.lib.units import mm  # noqa: E402
from reportlab.platypus import (  # noqa: E402
    Image,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from ml.schema import RISK_TIER_LABELS  # noqa: E402

# --------------------------------------------------------------------------
# Palette -- mirrors frontend/src/theme.js
# --------------------------------------------------------------------------

TIER_COLORS = {
    "Very Low": "#0a8f82",
    "Low": "#22a30c",
    "Moderate": "#edaa00",
    "High": "#dd5c28",
    "Very High": "#9e1c1c",
}

ACCENT = "#0a8f82"
SHAP_UP = "#dd5c28"
SHAP_DOWN = "#0a8f82"

INK = "#1a1f24"
INK_MUTED = "#6b7280"
RULE = "#dfe3e1"
SURFACE_ALT = "#f6f8f7"

PAGE_MARGIN = 16 * mm
CONTENT_WIDTH = A4[0] - 2 * PAGE_MARGIN

# Charts are drawn at 2x the placed size so they stay sharp in print.
CHART_DPI = 200


# --------------------------------------------------------------------------
# Styles
# --------------------------------------------------------------------------


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "title", parent=base["Title"], fontName="Helvetica-Bold",
            fontSize=19, leading=23, textColor=colors.HexColor(INK),
            alignment=0, spaceAfter=2,
        ),
        "subtitle": ParagraphStyle(
            "subtitle", parent=base["Normal"], fontSize=9.5, leading=13,
            textColor=colors.HexColor(INK_MUTED), spaceAfter=10,
        ),
        "h2": ParagraphStyle(
            "h2", parent=base["Heading2"], fontName="Helvetica-Bold",
            fontSize=12, leading=15, textColor=colors.HexColor(INK),
            spaceBefore=13, spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "body", parent=base["Normal"], fontSize=9.5, leading=14,
            textColor=colors.HexColor(INK), spaceAfter=5,
        ),
        "muted": ParagraphStyle(
            "muted", parent=base["Normal"], fontSize=8, leading=11,
            textColor=colors.HexColor(INK_MUTED),
        ),
        "kpi_value": ParagraphStyle(
            "kpi_value", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=17, leading=20, textColor=colors.HexColor(INK),
            alignment=TA_CENTER,
        ),
        "kpi_label": ParagraphStyle(
            "kpi_label", parent=base["Normal"], fontSize=7.2, leading=9,
            textColor=colors.HexColor(INK_MUTED), alignment=TA_CENTER,
        ),
    }


# --------------------------------------------------------------------------
# Chart helpers
# --------------------------------------------------------------------------


def _figure_to_image(figure, width: float) -> Image:
    """Render a Matplotlib figure to a flowable, then release it."""
    buffer = io.BytesIO()
    figure.savefig(
        buffer, format="png", dpi=CHART_DPI, bbox_inches="tight",
        facecolor="white", edgecolor="none",
    )
    plt.close(figure)
    buffer.seek(0)

    reader = Image(buffer)
    aspect = reader.imageHeight / float(reader.imageWidth)
    reader.drawWidth = width
    reader.drawHeight = width * aspect
    return reader


def _style_axes(axes) -> None:
    """One consistent chart chrome: no top/right spines, muted ticks."""
    for side in ("top", "right"):
        axes.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        axes.spines[side].set_color(RULE)
    axes.tick_params(colors=INK_MUTED, labelsize=7.5, length=3)
    axes.set_axisbelow(True)


def _risk_donut(distribution, width: float) -> Image:
    """
    Tier mix as a donut, always drawn in tier order.

    The dashboard sends a list of {tier, count, percentage}; a plain
    {tier: count} mapping is accepted too so the generator is usable directly.
    """
    if isinstance(distribution, list):
        counts = {row.get("tier"): row.get("count", 0) for row in distribution}
    else:
        counts = dict(distribution or {})

    labels, values, tier_colors = [], [], []
    for tier in RISK_TIER_LABELS:
        count = int(counts.get(tier, 0) or 0)
        if count:
            labels.append(tier)
            values.append(count)
            tier_colors.append(TIER_COLORS[tier])

    figure, axes = plt.subplots(figsize=(4.4, 2.9))
    if not values:
        axes.text(0.5, 0.5, "No predictions", ha="center", va="center",
                  color=INK_MUTED, fontsize=9)
        axes.axis("off")
        return _figure_to_image(figure, width)

    total = sum(values)
    wedges, _ = axes.pie(
        values, colors=tier_colors, startangle=90,
        wedgeprops={"width": 0.42, "edgecolor": "white", "linewidth": 1.6},
    )
    axes.text(0, 0.08, f"{total:,}", ha="center", va="center",
              fontsize=15, fontweight="bold", color=INK)
    axes.text(0, -0.22, "patients", ha="center", va="center",
              fontsize=8, color=INK_MUTED)

    # Tiers are always labelled, never colour alone -- the palette note in
    # theme.js applies here too.
    axes.legend(
        wedges,
        [f"{name} — {count:,} ({count / total:.0%})"
         for name, count in zip(labels, values, strict=True)],
        loc="center left", bbox_to_anchor=(1.0, 0.5),
        frameon=False, fontsize=7.5, labelcolor=INK,
    )
    axes.axis("equal")
    return _figure_to_image(figure, width)


def _bed_forecast_chart(forecast: list[dict], width: float) -> Image:
    figure, axes = plt.subplots(figsize=(7.2, 2.6))

    days = [row["day"] for row in forecast]
    occupied = [row["occupied_beds"] for row in forecast]
    capacity = forecast[0]["capacity"] if forecast else 0

    axes.bar(days, occupied, color=ACCENT, width=0.62, label="Occupied beds")
    if capacity:
        axes.axhline(capacity, color=SHAP_UP, linestyle="--", linewidth=1.1,
                     label=f"Capacity ({capacity:,})")

    axes.set_xlabel("Days ahead", fontsize=8, color=INK_MUTED)
    axes.set_ylabel("Beds", fontsize=8, color=INK_MUTED)
    axes.set_xticks(days)
    axes.grid(axis="y", color=RULE, linewidth=0.7)
    # Above the axes, not inside: at high occupancy the bars reach the top of
    # the plot and an inset legend sits on top of the data.
    axes.legend(
        frameon=False, fontsize=7.5, labelcolor=INK, ncol=2,
        loc="lower left", bbox_to_anchor=(0, 1.01, 1, 0.12), mode="expand",
        borderaxespad=0,
    )
    # Headroom so the capacity line is never flush against the frame.
    axes.set_ylim(0, max(max(occupied, default=0), capacity) * 1.08 or 1)
    _style_axes(axes)
    return _figure_to_image(figure, width)


def _los_histogram(histogram: list[dict], width: float) -> Image:
    figure, axes = plt.subplots(figsize=(3.5, 2.2))

    labels = [row.get("range", row.get("label", "")) for row in histogram]
    counts = [row.get("count", 0) for row in histogram]

    axes.bar(range(len(counts)), counts, color=ACCENT, width=0.72)
    axes.set_xticks(range(len(labels)))
    axes.set_xticklabels(labels, rotation=45, ha="right", fontsize=6.5)
    axes.set_ylabel("Patients", fontsize=8, color=INK_MUTED)
    axes.grid(axis="y", color=RULE, linewidth=0.7)
    _style_axes(axes)
    return _figure_to_image(figure, width)


def _department_chart(departments: list[dict], width: float) -> Image:
    figure, axes = plt.subplots(figsize=(3.5, 2.2))

    top = departments[:8][::-1]
    names = [row["department"] for row in top]
    values = [row["avg_los_days"] for row in top]

    axes.barh(range(len(values)), values, color=ACCENT, height=0.62)
    axes.set_yticks(range(len(names)))
    axes.set_yticklabels(names, fontsize=7)
    axes.set_xlabel("Average stay (days)", fontsize=8, color=INK_MUTED)
    axes.grid(axis="x", color=RULE, linewidth=0.7)
    _style_axes(axes)
    return _figure_to_image(figure, width)


def _discharge_schedule_chart(schedule: list[dict], width: float) -> Image:
    """
    Expected discharges per day.

    Day 0 is drawn in the High tier colour because it is not really "today" --
    the dashboard collapses every overdue stay onto it, so it is the bar a
    clinician has to act on. It is labelled "Now" rather than left to colour.
    """
    figure, axes = plt.subplots(figsize=(7.2, 2.4))

    days = [row["day"] for row in schedule]
    patients = [row["patients"] for row in schedule]
    bar_colors = [TIER_COLORS["High"] if day == 0 else ACCENT for day in days]

    axes.bar(days, patients, color=bar_colors, width=0.62)
    axes.set_xlabel("Days ahead", fontsize=8, color=INK_MUTED)
    axes.set_ylabel("Patients", fontsize=8, color=INK_MUTED)
    axes.set_xticks(days)
    axes.set_xticklabels(["Now" if day == 0 else f"+{day}" for day in days])
    axes.grid(axis="y", color=RULE, linewidth=0.7)
    # Whole patients only; a "2.5 discharges" tick would be nonsense.
    axes.yaxis.get_major_locator().set_params(integer=True)
    _style_axes(axes)
    return _figure_to_image(figure, width)


def _shap_chart(features: list[dict], width: float, unit: str = "days") -> Image:
    """Diverging bars: warm pushes the stay longer, cool pulls it shorter."""
    figure, axes = plt.subplots(figsize=(6.6, 0.42 * max(len(features), 1) + 0.9))

    ordered = features[::-1]
    labels = [row.get("label") or row.get("feature", "") for row in ordered]
    # `shap_value` is the contribution in days; `value` is the scaled feature
    # value and plotting it would contradict the narrative above the chart.
    values = [float(row.get("shap_value", 0)) for row in ordered]
    bar_colors = [SHAP_UP if v >= 0 else SHAP_DOWN for v in values]

    axes.barh(range(len(values)), values, color=bar_colors, height=0.6)
    axes.axvline(0, color=INK_MUTED, linewidth=0.9)
    axes.set_yticks(range(len(labels)))
    axes.set_yticklabels(labels, fontsize=7.5)
    axes.set_xlabel(f"Contribution ({unit})", fontsize=8, color=INK_MUTED)
    axes.grid(axis="x", color=RULE, linewidth=0.7)

    span = max((abs(v) for v in values), default=1) or 1
    for index, value in enumerate(values):
        offset = span * 0.03
        axes.text(
            value + (offset if value >= 0 else -offset), index,
            f"{value:+.2f}", va="center",
            ha="left" if value >= 0 else "right",
            fontsize=6.8, color=INK,
        )
    axes.set_xlim(-span * 1.32, span * 1.32)
    _style_axes(axes)
    return _figure_to_image(figure, width)


# --------------------------------------------------------------------------
# Layout helpers
# --------------------------------------------------------------------------


def _kpi_row(items: list[tuple[str, str]], styles) -> Table:
    """Evenly spaced metric tiles."""
    cells = [
        [
            Paragraph(value, styles["kpi_value"]),
        ]
        for value, _ in items
    ]
    labels = [[Paragraph(label, styles["kpi_label"])] for _, label in items]

    table = Table(
        [[c[0] for c in cells], [lab[0] for lab in labels]],
        colWidths=[CONTENT_WIDTH / len(items)] * len(items),
    )
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(SURFACE_ALT)),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor(RULE)),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor(RULE)),
        ("TOPPADDING", (0, 0), (-1, 0), 9),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return table


def _detail_table(rows: list[tuple[str, str]]) -> Table:
    table = Table(rows, colWidths=[CONTENT_WIDTH * 0.34, CONTENT_WIDTH * 0.66])
    table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor(INK_MUTED)),
        ("TEXTCOLOR", (1, 0), (1, -1), colors.HexColor(INK)),
        ("LINEBELOW", (0, 0), (-1, -2), 0.4, colors.HexColor(RULE)),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return table


def _tier_badge_table(tier: str, confidence: float, styles) -> Table:
    """The risk tier as a filled block -- colour plus the label, never colour alone."""
    swatch = colors.HexColor(TIER_COLORS.get(tier, INK_MUTED))
    table = Table(
        [[Paragraph(
            f'<font color="white"><b>{tier.upper()}</b></font>',
            ParagraphStyle("badge", parent=styles["body"], fontSize=12,
                           leading=15, alignment=TA_CENTER),
        )],
         [Paragraph(f"{confidence * 100:.1f}% confidence", styles["kpi_label"])]],
        colWidths=[CONTENT_WIDTH * 0.34],
        hAlign="LEFT",
    )
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), swatch),
        ("BACKGROUND", (0, 1), (0, 1), colors.HexColor(SURFACE_ALT)),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor(RULE)),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return table


def _page_furniture(title: str):
    """Header rule and footer with page numbers, drawn on every page."""

    def draw(canvas, document):
        canvas.saveState()
        width, height = A4

        canvas.setStrokeColor(colors.HexColor(ACCENT))
        canvas.setLineWidth(2)
        canvas.line(PAGE_MARGIN, height - 11 * mm, width - PAGE_MARGIN, height - 11 * mm)

        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(colors.HexColor(INK_MUTED))
        canvas.drawString(PAGE_MARGIN, height - 8.5 * mm, title)

        canvas.setStrokeColor(colors.HexColor(RULE))
        canvas.setLineWidth(0.5)
        canvas.line(PAGE_MARGIN, 13 * mm, width - PAGE_MARGIN, 13 * mm)
        canvas.drawString(
            PAGE_MARGIN, 9 * mm,
            "Decision support only — not a substitute for clinical judgement.",
        )
        canvas.drawRightString(width - PAGE_MARGIN, 9 * mm, f"Page {document.page}")
        canvas.restoreState()

    return draw


def _build(story: list, title: str, subject: str) -> bytes:
    buffer = io.BytesIO()
    document = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=PAGE_MARGIN, rightMargin=PAGE_MARGIN,
        topMargin=18 * mm, bottomMargin=18 * mm,
        title=title, subject=subject, author="Healthcare Recovery Forecast",
    )
    document.build(story, onFirstPage=_page_furniture(title),
                   onLaterPages=_page_furniture(title))
    return buffer.getvalue()


def _timestamp() -> str:
    return datetime.now(UTC).strftime("%d %b %Y, %H:%M UTC")


# --------------------------------------------------------------------------
# Reports
# --------------------------------------------------------------------------


def cohort_report(
    payload: dict[str, Any],
    *,
    generated_by: str = "",
    model: dict[str, Any] | None = None,
) -> bytes:
    """
    Dataset-wide capacity summary.

    `payload` is the /api/dashboard/kpis response, used as-is so the PDF and
    the dashboard can never disagree about the same numbers.

    `model` is the /api/predict/model payload. It is optional because the
    generator must still produce a report when the caller cannot read model
    internals -- but an analyst's job is as much "is this model still
    trustworthy" as it is "how many beds", so when it is supplied the
    held-out metrics are printed alongside the capacity figures.
    """
    styles = _styles()
    story: list = []

    kpis = payload.get("kpis", {})
    source = payload.get("source", {}) or {}

    story.append(Paragraph("Recovery Forecast — Cohort Report", styles["title"]))
    story.append(Paragraph(
        f"{source.get('filename', 'Current dataset')} · generated {_timestamp()}"
        + (f" · {generated_by}" if generated_by else ""),
        styles["subtitle"],
    ))

    story.append(_kpi_row([
        (f"{kpis.get('total_patients', 0):,}", "PATIENTS"),
        (f"{kpis.get('avg_los_days', 0):.1f}", "AVG STAY (DAYS)"),
        (f"{kpis.get('median_los_days', 0):.1f}", "MEDIAN (DAYS)"),
        (f"{kpis.get('high_risk_patients', 0):,}", "HIGH RISK"),
        (f"{kpis.get('total_bed_days', 0):,}", "BED DAYS"),
    ], styles))

    story.append(Paragraph("Discharge-risk mix", styles["h2"]))
    story.append(_risk_donut(payload.get("risk_distribution", {}) or {}, CONTENT_WIDTH * 0.92))

    forecast = payload.get("bed_forecast") or []
    if forecast:
        story.append(Paragraph(
            f"Projected bed occupancy — next {len(forecast)} days", styles["h2"]
        ))
        story.append(_bed_forecast_chart(forecast, CONTENT_WIDTH))
        peak = max(forecast, key=lambda row: row["occupied_beds"])
        story.append(Paragraph(
            f"Occupancy peaks on day {peak['day']} ({peak['date']}) at "
            f"{peak['occupied_beds']:,} of {peak['capacity']:,} beds — "
            f"{peak['occupancy_rate'] * 100:.0f}% of capacity, "
            f"{peak['available_beds']:,} free.",
            styles["body"],
        ))

    histogram = payload.get("los_histogram") or []
    departments = payload.get("department_breakdown") or []
    if histogram or departments:
        block: list = [Paragraph("Distribution and departments", styles["h2"])]
        half = CONTENT_WIDTH / 2 - 4 * mm
        side_by_side = Table(
            [[
                _los_histogram(histogram, half) if histogram else Paragraph("", styles["body"]),
                _department_chart(departments, half) if departments else Paragraph("", styles["body"]),
            ]],
            colWidths=[CONTENT_WIDTH / 2, CONTENT_WIDTH / 2],
        )
        side_by_side.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]))
        block.append(side_by_side)
        # Heading and charts move to the next page together rather than the
        # heading stranding at the foot of this one.
        story.append(KeepTogether(block))

    if departments:
        story.append(Paragraph("Department detail", styles["h2"]))
        rows = [["Department", "Patients", "Avg stay (days)"]]
        rows += [
            [row["department"], f"{row.get('patients', 0):,}", f"{row['avg_los_days']:.1f}"]
            for row in departments[:12]
        ]
        table = Table(rows, colWidths=[CONTENT_WIDTH * 0.5, CONTENT_WIDTH * 0.25,
                                       CONTENT_WIDTH * 0.25])
        table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(SURFACE_ALT)),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor(INK)),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.HexColor(RULE)),
            ("TOPPADDING", (0, 0), (-1, -1), 4.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4.5),
        ]))
        story.append(table)

    if model:
        story.append(Paragraph("Model performance", styles["h2"]))
        story.append(Paragraph(
            "Scores on the held-out test split. The selected algorithm is the "
            "one every figure in this report was produced with.",
            styles["muted"],
        ))
        story.append(Spacer(1, 4))
        story.append(_model_comparison_table(model))

    story.append(Paragraph("Provenance", styles["h2"]))
    provenance = [
        ["Dataset", str(source.get("filename", "—"))],
        ["Uploaded", str(source.get("uploaded_at", "—"))[:19].replace("T", " ")],
        ["Model version", str(payload.get("model_version", "—"))],
    ]
    if model:
        provenance += [
            ["Model trained", str(model.get("trained_at", "—"))[:19].replace("T", " ")],
            ["Training rows", f"{model.get('training_rows', 0):,}"],
        ]
    provenance.append(["Report generated", _timestamp()])
    story.append(_detail_table(provenance))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "Figures are model estimates over the uploaded cohort. Bed projections "
        "assume admissions continue at the observed rate and do not account for "
        "transfers, cancellations, or seasonal effects.",
        styles["muted"],
    ))

    return _build(story, "Recovery Forecast — Cohort Report", "Cohort capacity summary")


def _model_comparison_table(model: dict[str, Any]) -> Table:
    """
    Every candidate algorithm side by side, as the analyst dashboard shows it.

    The linear family is trained as least squares for the stay and a logistic
    link for the tier, so its two halves live under different names in the
    metrics; they are paired back up here rather than being reported as two
    unrelated models.
    """
    comparison = model.get("comparison", {}) or {}
    regression = comparison.get("regression", {}) or {}
    classification = comparison.get("classification", {}) or {}
    selected = (model.get("regressor") or {}).get("algorithm")

    rows = [["Algorithm", "LOS RMSE", "LOS R²", "Tier accuracy", "Macro F1"]]
    highlight: list[tuple] = []

    for index, (name, reg) in enumerate(regression.items(), start=1):
        clf_name = "Logistic Regression" if name == "Linear Regression" else name
        clf = classification.get(clf_name) or {}
        label = (
            "Linear / Logistic Regression" if name == "Linear Regression" else name
        )
        if name == selected:
            label = f"{label}  (selected)"
            highlight.append(
                ("FONTNAME", (0, index), (-1, index), "Helvetica-Bold")
            )
            highlight.append(
                ("BACKGROUND", (0, index), (-1, index), colors.HexColor("#e7f4f2"))
            )
        rows.append([
            label,
            f"{reg.get('rmse', 0):.3f}",
            f"{reg.get('r2', 0):.4f}",
            f"{clf['accuracy'] * 100:.2f}%" if "accuracy" in clf else "—",
            f"{clf['macro_f1']:.3f}" if "macro_f1" in clf else "—",
        ])

    table = Table(
        rows,
        colWidths=[CONTENT_WIDTH * w for w in (0.36, 0.16, 0.16, 0.17, 0.15)],
    )
    table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(SURFACE_ALT)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor(INK)),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.HexColor(RULE)),
        ("TOPPADDING", (0, 0), (-1, -1), 4.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4.5),
        *highlight,
    ]))
    return table


def _worklist_table(entries: list[dict], *, compact: bool = False) -> Table:
    """
    The worklist as a printable table.

    Rows carry the tier colour as a left-hand rule and the tier name as text,
    the same bargain the dashboard strikes: the colour makes a row findable
    while scanning, the words are what actually say how sick someone is.
    """
    header = ["Patient", "Dept", "Risk", "Stay", "Discharge", "Due", "Conf."]
    rows: list[list[str]] = [header]
    for entry in entries:
        rows.append([
            str(entry.get("patient_ref", "—")),
            str(entry.get("department") or "—"),
            str(entry.get("risk_tier", "—")),
            f"{entry.get('los_days', 0):.1f} d",
            str(entry.get("expected_discharge", "—")),
            _due_label(entry.get("days_remaining", 0)),
            f"{entry.get('confidence', 0) * 100:.0f}%",
        ])

    widths = [0.17, 0.16, 0.14, 0.11, 0.17, 0.15, 0.10]
    table = Table(
        rows,
        colWidths=[CONTENT_WIDTH * w for w in widths],
        repeatRows=1,
    )

    style = [
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7.6 if compact else 8.2),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(SURFACE_ALT)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor(INK)),
        ("ALIGN", (3, 0), (3, -1), "RIGHT"),
        ("ALIGN", (6, 0), (6, -1), "RIGHT"),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.HexColor(RULE)),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]

    for index, entry in enumerate(entries, start=1):
        tier = entry.get("risk_tier")
        if tier in TIER_COLORS:
            style.append(
                ("LINEBEFORE", (0, index), (0, index), 2.2,
                 colors.HexColor(TIER_COLORS[tier]))
            )
        # An overdue row is the one thing on this page that must not be
        # missed, so it gets a wash as well as the words in the Due column.
        # Strictly negative: an admission due *today* has not run late yet,
        # and shading it the same as a three-day overstay would blunt the
        # only marking on the page that is meant to prompt an action.
        if int(entry.get("days_remaining", 1)) < 0:
            style.append(
                ("BACKGROUND", (0, index), (-1, index), colors.HexColor("#fdeceb"))
            )
            style.append(
                ("TEXTCOLOR", (5, index), (5, index), colors.HexColor(TIER_COLORS["Very High"]))
            )

    table.setStyle(TableStyle(style))
    return table


def _tier_rank(tier: object) -> int:
    """Severity order, so "Very High" sorts above "Low" rather than under V."""
    try:
        return RISK_TIER_LABELS.index(tier)
    except ValueError:
        return -1


def _due_label(days: int) -> str:
    """Same wording as the dashboard's Expected discharge column."""
    days = int(days)
    if days < 0:
        return f"{abs(days)}d overdue"
    if days == 0:
        return "Today"
    if days == 1:
        return "Tomorrow"
    return f"In {days} days"


def caseload_report(
    payload: dict[str, Any],
    *,
    generated_by: str = "",
    clinician: str = "",
) -> bytes:
    """
    A clinician's own caseload, laid out as a ward-round handover.

    `payload` is the /api/dashboard/clinical response, used as-is so the sheet
    someone carries onto the ward and the screen they printed it from cannot
    drift apart.

    The ordering is the point of this report. It opens with the admissions
    that have run past their predicted discharge date, because those are the
    only rows on the page that imply an action today; capacity totals and
    model metrics belong to the analyst's cohort report and are deliberately
    absent here.
    """
    styles = _styles()
    story: list = []

    caseload = payload.get("caseload", {}) or {}
    worklist = payload.get("worklist", []) or []
    schedule = payload.get("discharge_schedule", []) or []

    story.append(Paragraph("Recovery Forecast — Caseload Report", styles["title"]))
    story.append(Paragraph(
        (f"{clinician} · " if clinician else "")
        + f"generated {_timestamp()}"
        + (f" · {generated_by}" if generated_by and generated_by != clinician else ""),
        styles["subtitle"],
    ))

    patients = int(caseload.get("patients", 0) or 0)
    if not patients:
        story.append(Paragraph(
            "No admissions have been scored under this account yet, so there "
            "is no caseload to report. Score an admission and it will appear "
            "here with an expected discharge date.",
            styles["body"],
        ))
        return _build(story, "Recovery Forecast — Caseload Report",
                      "Clinical caseload handover")

    story.append(_kpi_row([
        (f"{patients:,}", "ADMISSIONS"),
        (f"{caseload.get('due_within_48h', 0):,}", "DUE WITHIN 48H"),
        (f"{caseload.get('high_risk', 0):,}", "HIGH RISK"),
        (f"{caseload.get('avg_los_days', 0):.1f}", "AVG STAY (DAYS)"),
        (f"{caseload.get('scored_today', 0):,}", "SCORED TODAY"),
    ], styles))

    # --- what needs doing today ------------------------------------------
    #
    # "Overdue" is strictly past the date; due-today counts as imminent, which
    # is also how the dashboard's due_within_48h KPI counts it (0..2 days), so
    # the sentence below and the tile above it can never contradict each other.
    overdue = [e for e in worklist if int(e.get("days_remaining", 1)) < 0]
    imminent = [e for e in worklist if 0 <= int(e.get("days_remaining", 1)) <= 2]

    story.append(Paragraph("Priority actions", styles["h2"]))
    if overdue or imminent:
        story.append(Paragraph(
            f"{len(overdue)} admission{'' if len(overdue) == 1 else 's'} past the "
            f"predicted discharge date and {len(imminent)} due within the next "
            "48 hours. Start discharge paperwork or record the reason for the "
            "delay.",
            styles["body"],
        ))
        story.append(Spacer(1, 3))
        # The main worklist below is ordered for a ward round (sickest first).
        # This block answers a different question -- what is late -- so it is
        # ordered by how late, with risk only breaking ties.
        priority = sorted(
            overdue + imminent,
            key=lambda e: (int(e.get("days_remaining", 0)), -_tier_rank(e.get("risk_tier"))),
        )
        story.append(_worklist_table(priority))
    else:
        story.append(Paragraph(
            "Nothing in this caseload is overdue or due within 48 hours.",
            styles["body"],
        ))

    # --- when the beds free up -------------------------------------------
    if schedule:
        block = [
            Paragraph(
                f"Expected discharges — next {max(row['day'] for row in schedule)} days",
                styles["h2"],
            ),
            _discharge_schedule_chart(schedule, CONTENT_WIDTH),
            Paragraph(
                "Each stay is counted from the date it was scored. The first "
                "bar carries every overdue admission as well as today's, which "
                "is why it is usually the tallest.",
                styles["muted"],
            ),
        ]
        story.append(KeepTogether(block))

    # --- how sick the caseload is ----------------------------------------
    distribution = payload.get("risk_distribution") or {}
    if distribution:
        block = [
            Paragraph("Caseload by discharge risk", styles["h2"]),
            _risk_donut(distribution, CONTENT_WIDTH * 0.92),
        ]
        story.append(KeepTogether(block))

    # --- the round itself -------------------------------------------------
    story.append(Paragraph("Discharge worklist", styles["h2"]))
    story.append(Paragraph(
        "Highest risk first, then soonest out — the order a ward round works "
        "in. Overdue rows are shaded.",
        styles["muted"],
    ))
    story.append(Spacer(1, 4))
    story.append(_worklist_table(worklist, compact=len(worklist) > 18))

    story.append(Paragraph("Provenance", styles["h2"]))
    story.append(_detail_table([
        ["Clinician", clinician or "—"],
        ["Admissions in caseload", f"{patients:,}"],
        ["Mean model confidence", f"{caseload.get('avg_confidence', 0) * 100:.1f}%"],
        ["Model version", str(payload.get("model_version", "—"))],
        ["Report generated", _timestamp()],
    ]))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "Expected discharge is the model's predicted length of stay counted "
        "from when each admission was scored. It is a planning aid for "
        "discharge coordination and is not a clinical recommendation; it does "
        "not account for complications, transfers, or social care delays.",
        styles["muted"],
    ))

    return _build(story, "Recovery Forecast — Caseload Report",
                  "Clinical caseload handover")


def patient_report(
    record: dict[str, Any],
    prediction: dict[str, Any],
    *,
    generated_by: str = "",
    patient_ref: str | None = None,
) -> bytes:
    """Single-admission summary, printable for a patient file."""
    styles = _styles()
    story: list = []

    story.append(Paragraph("Recovery Forecast — Patient Report", styles["title"]))
    story.append(Paragraph(
        (f"Patient {patient_ref} · " if patient_ref else "")
        + f"generated {_timestamp()}"
        + (f" · {generated_by}" if generated_by else ""),
        styles["subtitle"],
    ))

    story.append(_kpi_row([
        (f"{prediction.get('los_days', 0):.1f}", "PREDICTED STAY (DAYS)"),
        (str(prediction.get("estimated_discharge", "—")), "ESTIMATED DISCHARGE"),
        (f"{prediction.get('confidence', 0) * 100:.0f}%", "CONFIDENCE"),
    ], styles))

    story.append(Paragraph("Discharge risk", styles["h2"]))
    story.append(_tier_badge_table(
        prediction.get("risk_tier", "—"), prediction.get("confidence", 0), styles
    ))
    if prediction.get("guidance"):
        story.append(Spacer(1, 7))
        story.append(Paragraph(prediction["guidance"], styles["body"]))

    story.append(Paragraph("Admission record", styles["h2"]))
    story.append(_detail_table([
        [_humanise(key), _format_value(value)] for key, value in record.items()
    ]))

    probabilities = prediction.get("tier_probabilities") or {}
    if probabilities:
        story.append(Paragraph("Tier probabilities", styles["h2"]))
        rows = [["Tier", "Probability"]]
        rows += [
            [tier, f"{probabilities.get(tier, 0) * 100:.1f}%"]
            for tier in RISK_TIER_LABELS
        ]
        table = Table(rows, colWidths=[CONTENT_WIDTH * 0.5, CONTENT_WIDTH * 0.5])
        table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(SURFACE_ALT)),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.HexColor(RULE)),
            ("TOPPADDING", (0, 0), (-1, -1), 4.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4.5),
        ]))
        # Highlight the predicted tier's row.
        predicted = prediction.get("risk_tier")
        if predicted in RISK_TIER_LABELS:
            index = RISK_TIER_LABELS.index(predicted) + 1
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, index), (-1, index),
                 colors.HexColor(TIER_COLORS[predicted])),
                ("TEXTCOLOR", (0, index), (-1, index), colors.white),
                ("FONTNAME", (0, index), (-1, index), "Helvetica-Bold"),
            ]))
        story.append(table)

    shap = prediction.get("shap_values") or {}
    features = shap.get("top_features") or []
    if features:
        block = [Paragraph("Why this prediction", styles["h2"])]
        if shap.get("narrative"):
            block.append(Paragraph(shap["narrative"], styles["body"]))
        block.append(_shap_chart(features, CONTENT_WIDTH))
        if shap.get("base_value") is not None:
            block.append(Paragraph(
                f"Baseline for an average patient is {shap['base_value']:.2f} days; "
                f"the factors above adjust that to {prediction.get('los_days', 0):.2f} days.",
                styles["muted"],
            ))
        story.append(KeepTogether(block))

    story.append(Spacer(1, 10))
    story.append(Paragraph(
        f"Model version {prediction.get('model_version', '—')}. This estimate is "
        "decision support for capacity planning and does not constitute a "
        "clinical recommendation.",
        styles["muted"],
    ))

    return _build(story, "Recovery Forecast — Patient Report", "Patient recovery summary")


def _humanise(name: str) -> str:
    return name.replace("_", " ").capitalize()


def _format_value(value: Any) -> str:
    """Render a field for display; whole numbers lose the '.0' tail."""
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if isinstance(value, float):
        return f"{value:g}"
    return str(value)
