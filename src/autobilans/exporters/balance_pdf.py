from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


BALANCE_LABELS: dict[str, str] = {
    "Aktywa_A_I_3": "Inne wartości niematerialne i prawne",
    "Aktywa_A_II_1_A": "Grunty, w tym prawo użytkowania wieczystego gruntu",
    "Aktywa_A_II_1_B": "Budynki, lokale, prawa do lokali i obiekty inżynierii lądowej i wodnej",
    "Aktywa_A_II_1_C": "Urządzenia techniczne i maszyny",
    "Aktywa_A_II_1_D": "Środki transportu",
    "Aktywa_A_II_1_E": "Inne środki trwałe",
    "Aktywa_A_II_2": "Środki trwałe w budowie",
    "Aktywa_A_III_3": "Długoterminowe aktywa finansowe w pozostałych jednostkach",
    "Aktywa_A_IV_3_A": "Aktywa z tytułu odroczonego podatku dochodowego",
    "Aktywa_A_IV_3_B": "Inne rozliczenia międzyokresowe długoterminowe",
    "Aktywa_A_IV_3_C": "Pozostałe rozliczenia międzyokresowe długoterminowe",
    "Aktywa_A_V": "Należne wpłaty na kapitał podstawowy",
    "Aktywa_A_V_2": "Inne rozliczenia międzyokresowe długoterminowe",
    "Aktywa_B_I_4": "Towary",
    "Aktywa_B_II_1_A_1": "Należności z tytułu dostaw i usług od jednostek powiązanych",
    "Aktywa_B_II_1_B": "Inne należności od jednostek powiązanych",
    "Aktywa_B_II_2_A": "Należności z tytułu dostaw i usług od pozostałych jednostek",
    "Aktywa_B_II_3_A_1": "Należności z tytułu dostaw i usług od pozostałych jednostek",
    "Aktywa_B_II_3_B": "Należności z tytułu podatków, dotacji, ceł, ubezpieczeń społecznych i zdrowotnych",
    "Aktywa_B_II_3_C": "Inne należności krótkoterminowe",
    "Aktywa_B_III_1_A": "Krótkoterminowe aktywa finansowe w jednostkach powiązanych",
    "Aktywa_B_III_1_B": "Krótkoterminowe aktywa finansowe w pozostałych jednostkach",
    "Aktywa_B_III_1_C_1": "Środki pieniężne w kasie i na rachunkach",
    "Aktywa_B_III_1_C_2": "Inne środki pieniężne",
    "Aktywa_B_IV": "Krótkoterminowe rozliczenia międzyokresowe",
    "Aktywa_C": "Należne wpłaty na kapitał podstawowy",
    "Aktywa_D": "Udziały własne",
    "Pasywa_A_I": "Kapitał podstawowy",
    "Pasywa_A_II": "Kapitał zapasowy",
    "Pasywa_A_VI": "Zysk/strata z lat ubiegłych",
    "Pasywa_B_I_2": "Rezerwa na świadczenia emerytalne i podobne",
    "Pasywa_B_I_3": "Pozostałe rezerwy",
    "Pasywa_B_II_3": "Inne zobowiązania długoterminowe",
    "Pasywa_B_III_1_A_1": "Zobowiązania z tytułu dostaw i usług wobec jednostek powiązanych",
    "Pasywa_B_III_2_A": "Zobowiązania z tytułu dostaw i usług wobec pozostałych jednostek",
    "Pasywa_B_III_3_A": "Kredyty i pożyczki",
    "Pasywa_B_III_3_D_1": "Zobowiązania z tytułu dostaw i usług",
    "Pasywa_B_III_3_G": "Zobowiązania z tytułu podatków, ceł, ubezpieczeń społecznych i zdrowotnych",
    "Pasywa_B_III_3_H": "Zobowiązania z tytułu wynagrodzeń",
    "Pasywa_B_III_3_I": "Inne zobowiązania krótkoterminowe",
    "Pasywa_B_IV_2_2": "Inne rozliczenia międzyokresowe",
}


BALANCE_ORDER = [
    "Aktywa_A_I_3",
    "Aktywa_A_II_1_A",
    "Aktywa_A_II_1_B",
    "Aktywa_A_II_1_C",
    "Aktywa_A_II_1_D",
    "Aktywa_A_II_1_E",
    "Aktywa_A_II_2",
    "Aktywa_A_III_3",
    "Aktywa_A_IV_3_A",
    "Aktywa_A_IV_3_B",
    "Aktywa_A_IV_3_C",
    "Aktywa_A_V",
    "Aktywa_A_V_2",
    "Aktywa_B_I_4",
    "Aktywa_B_II_1_A_1",
    "Aktywa_B_II_1_B",
    "Aktywa_B_II_2_A",
    "Aktywa_B_II_3_A_1",
    "Aktywa_B_II_3_B",
    "Aktywa_B_II_3_C",
    "Aktywa_B_III_1_A",
    "Aktywa_B_III_1_B",
    "Aktywa_B_III_1_C_1",
    "Aktywa_B_III_1_C_2",
    "Aktywa_B_IV",
    "Aktywa_C",
    "Aktywa_D",
    "Pasywa_A_I",
    "Pasywa_A_II",
    "Pasywa_A_VI",
    "Pasywa_B_I_2",
    "Pasywa_B_I_3",
    "Pasywa_B_II_3",
    "Pasywa_B_III_1_A_1",
    "Pasywa_B_III_2_A",
    "Pasywa_B_III_3_A",
    "Pasywa_B_III_3_D_1",
    "Pasywa_B_III_3_G",
    "Pasywa_B_III_3_H",
    "Pasywa_B_III_3_I",
    "Pasywa_B_IV_2_2",
]


def _font_names() -> tuple[str, str]:
    regular = Path(r"C:\Windows\Fonts\arial.ttf")
    bold = Path(r"C:\Windows\Fonts\arialbd.ttf")
    if regular.exists() and bold.exists():
        if "ArialAutoBilans" not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont("ArialAutoBilans", str(regular)))
        if "ArialAutoBilans-Bold" not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont("ArialAutoBilans-Bold", str(bold)))
        return "ArialAutoBilans", "ArialAutoBilans-Bold"
    return "Helvetica", "Helvetica-Bold"


def _display_amount(code: str, value: float) -> float:
    if code.startswith("Pasywa_"):
        return abs(value)
    return value


def _format_money(value: float) -> str:
    formatted = f"{value:,.2f}"
    return formatted.replace(",", " ").replace(".", ",")


def _build_section_rows(
    *,
    section: str,
    current_balance: dict[str, float],
    previous_balance: dict[str, float],
    current_label: str,
    previous_label: str,
    styles: dict[str, ParagraphStyle],
) -> list[list[object]]:
    rows: list[list[object]] = [
        [
            Paragraph(section.upper(), styles["section"]),
            "",
            Paragraph(current_label, styles["amount_header"]),
            Paragraph(previous_label, styles["amount_header"]),
        ]
    ]
    prefix = "Aktywa_" if section == "Aktywa" else "Pasywa_"
    for code in BALANCE_ORDER:
        if not code.startswith(prefix):
            continue
        current = _display_amount(code, float(current_balance.get(code, 0.0)))
        previous = _display_amount(code, float(previous_balance.get(code, 0.0)))
        if abs(current) < 0.005 and abs(previous) < 0.005:
            continue
        rows.append(
            [
                Paragraph(code, styles["code"]),
                Paragraph(BALANCE_LABELS.get(code, code), styles["label"]),
                Paragraph(_format_money(current), styles["amount"]),
                Paragraph(_format_money(previous), styles["amount"]),
            ]
        )
    return rows


def export_balance_pdf(
    *,
    company: str,
    year: int,
    current_balance: dict[str, float],
    previous_balance: dict[str, float],
    output_dir: Path,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / "bilans.pdf"

    doc = SimpleDocTemplate(
        str(target),
        pagesize=landscape(A4),
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        topMargin=10 * mm,
        bottomMargin=10 * mm,
    )
    sample = getSampleStyleSheet()
    regular_font, bold_font = _font_names()
    styles = {
        "title": ParagraphStyle("title", parent=sample["Title"], fontName=bold_font, fontSize=14, leading=16),
        "meta": ParagraphStyle("meta", parent=sample["Normal"], fontName=regular_font, fontSize=8, leading=10),
        "section": ParagraphStyle("section", parent=sample["Normal"], fontName=bold_font, fontSize=8, leading=9),
        "code": ParagraphStyle("code", parent=sample["Normal"], fontName=regular_font, fontSize=6.3, leading=7.2),
        "label": ParagraphStyle("label", parent=sample["Normal"], fontName=regular_font, fontSize=6.3, leading=7.2),
        "amount": ParagraphStyle("amount", parent=sample["Normal"], fontName=regular_font, fontSize=6.3, leading=7.2, alignment=TA_RIGHT),
        "amount_header": ParagraphStyle(
            "amount_header",
            parent=sample["Normal"],
            fontName=bold_font,
            fontSize=6.3,
            leading=7.2,
            alignment=TA_RIGHT,
        ),
    }

    current_label = f"31.12.{year}"
    previous_label = f"31.12.{year - 1}"
    story: list[object] = [
        Paragraph("BILANS", styles["title"]),
        Paragraph(company.upper(), styles["meta"]),
        Paragraph(f"Roboczy wydruk bilansu sporządzony na dzień {current_label}", styles["meta"]),
        Spacer(1, 5 * mm),
    ]

    left_rows = _build_section_rows(
        section="Aktywa",
        current_balance=current_balance,
        previous_balance=previous_balance,
        current_label=current_label,
        previous_label=previous_label,
        styles=styles,
    )
    right_rows = _build_section_rows(
        section="Pasywa",
        current_balance=current_balance,
        previous_balance=previous_balance,
        current_label=current_label,
        previous_label=previous_label,
        styles=styles,
    )
    full_width = [32 * mm, 153 * mm, 39 * mm, 39 * mm]
    left_table = Table(left_rows, colWidths=full_width, repeatRows=1)
    right_table = Table(right_rows, colWidths=full_width, repeatRows=1)
    table_style = TableStyle(
        [
            ("GRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
            ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 2),
            ("RIGHTPADDING", (0, 0), (-1, -1), 2),
            ("TOPPADDING", (0, 0), (-1, -1), 1.2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1.2),
        ]
    )
    left_table.setStyle(table_style)
    right_table.setStyle(table_style)

    story.append(left_table)
    story.append(Spacer(1, 3 * mm))
    story.append(right_table)
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("Dokument roboczy wygenerowany automatycznie z ZOiS i historii spółki.", styles["meta"]))

    doc.build(story)
    return target
