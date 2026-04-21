"""
Builds a formatted Word document from AI-generated Q&A pairs.
"""
import os
import logging
from datetime import date
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

logger = logging.getLogger(__name__)


def build_answer_doc(
    subject_name: str,
    student_info: dict,
    qa_pairs: dict,
    output_dir: str,
) -> str:
    """
    Build a formatted .docx answer document.

    Args:
        subject_name:  e.g. "Data Structures and Algorithms"
        student_info:  {"name": "...", "enrollment": "..."}
        qa_pairs:      {question_str: answer_str, ...}
        output_dir:    Directory to save the file in.

    Returns:
        Absolute path to the saved .docx file.
    """
    os.makedirs(output_dir, exist_ok=True)

    doc = Document()

    # ── Page margins ──────────────────────────────────────────────────────────
    for section in doc.sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1.25)
        section.right_margin = Inches(1.25)

    # ── Header ────────────────────────────────────────────────────────────────
    _add_header(doc)

    title = doc.add_heading(f"Assignment — {subject_name}", level=1)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _set_heading_color(title, RGBColor(0x1A, 0x56, 0xDB))  # Blue

    info_para = doc.add_paragraph()
    info_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = info_para.add_run(
        f"Name: {student_info.get('name', 'N/A')}    |    "
        f"Enrollment: {student_info.get('enrollment', 'N/A')}    |    "
        f"Date: {date.today().strftime('%d %B %Y')}"
    )
    run.font.size = Pt(10)
    run.font.color.rgb = RGBColor(0x6B, 0x72, 0x80)

    _add_divider(doc)

    # ── Q&A Body ──────────────────────────────────────────────────────────────
    for i, (question, answer) in enumerate(qa_pairs.items(), 1):
        # Question heading
        q_heading = doc.add_heading(f"Q{i}. {question}", level=2)
        _set_heading_color(q_heading, RGBColor(0x11, 0x18, 0x27))

        # Answer paragraphs
        for para_text in answer.split("\n"):
            para_text = para_text.strip()
            if para_text:
                p = doc.add_paragraph(para_text)
                p.paragraph_format.space_after = Pt(4)

        doc.add_paragraph()  # Spacer

    # ── Footer ────────────────────────────────────────────────────────────────
    _add_footer(doc, student_info.get("full_name") or student_info.get("name", "N/A"))

    # ── Save ──────────────────────────────────────────────────────────────────
    safe_subject = subject_name.replace(" ", "_").replace("/", "-").replace("\\", "-")
    filename = f"{safe_subject}_{date.today().isoformat()}.docx"
    filepath = os.path.join(output_dir, filename)
    doc.save(filepath)

    logger.info(f"[doc_builder] Saved answer doc: {filepath}")
    return filepath


# ── Helpers ───────────────────────────────────────────────────────────────────

def _add_header(doc: Document):
    """Add institute name to the document header."""
    section = doc.sections[0]
    header = section.header
    para = header.paragraphs[0] if header.paragraphs else header.add_paragraph()
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = para.add_run("Prestige Institute of Engineering Management and Research (PIEMR)")
    run.font.size = Pt(9)
    run.font.color.rgb = RGBColor(0x6B, 0x72, 0x80)


def _add_divider(doc: Document):
    p = doc.add_paragraph()
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "6")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), "D1D5DB")
    pBdr.append(bottom)
    pPr.append(pBdr)


def _set_heading_color(heading, color: RGBColor):
    for run in heading.runs:
        run.font.color.rgb = color


def _add_footer(doc: Document, full_name: str):
    """Add student's name to the document footer."""
    section = doc.sections[0]
    footer = section.footer
    para = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = para.add_run(f"Generated for: {full_name}")
    run.font.size = Pt(8)
    run.font.color.rgb = RGBColor(0x9C, 0xA3, 0xAF)
