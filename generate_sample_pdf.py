"""Generate a sample MCQ PDF for integration testing."""

from __future__ import annotations

import tempfile
from pathlib import Path

import fitz


def build_sample_pdf(path: str, num_questions: int = 5) -> str:
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    y = 50
    line_height = 16

    def write_line(text: str, size: int = 11) -> None:
        nonlocal y, page
        if y > 780:
            page = doc.new_page(width=595, height=842)
            y = 50
        page.insert_text((50, y), text, fontsize=size, fontname="helv")
        y += line_height

    for q in range(1, num_questions + 1):
        write_line(f"QUESTION {q}", 12)
        write_line(f"This is sample question number {q}. Which options apply?")
        write_line("A. First option")
        write_line("B. Second option")
        write_line("C. Third option")
        write_line("D. Fourth option")
        if q % 3 == 0:
            write_line("Answer: A, C")
        else:
            write_line(f"Answer: {chr(ord('A') + (q % 4))}")
        write_line("Explanation: This explanatory text should be ignored.")
        write_line("Reference: Sample reference note — also ignored.")
        y += 8

    doc.save(path)
    doc.close()
    return path


if __name__ == "__main__":
    out = Path(tempfile.gettempdir()) / "sample_mcqs.pdf"
    build_sample_pdf(str(out))
    print(f"Created: {out}")
