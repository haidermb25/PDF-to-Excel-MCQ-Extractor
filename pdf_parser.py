"""PDF extraction and MCQ parsing — optimized for speed."""

from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path
from typing import Callable, Optional

import fitz

from mcq_models import MCQ, parse_question_block, split_into_question_blocks


def _extract_text_from_pdf(pdf_path: str) -> str:
    """Fast single-pass text extraction via PyMuPDF."""
    doc = fitz.open(pdf_path)
    try:
        return "\n\n".join(page.get_text("text") or "" for page in doc)
    finally:
        doc.close()


def _extract_images_from_pdf(pdf_path: str, output_dir: str) -> dict[int, list[tuple[str, str]]]:
    """Extract images only from pages that contain embedded images."""
    os.makedirs(output_dir, exist_ok=True)
    question_images: dict[int, list[tuple[str, str]]] = {}

    doc = fitz.open(pdf_path)
    try:
        current_question: Optional[int] = None
        image_counter = 0

        for page in doc:
            text = page.get_text("text") or ""
            for match in re.finditer(r"QUESTION\s+(\d+)", text, re.IGNORECASE):
                current_question = int(match.group(1))

            images = page.get_images(full=True)
            if not images or current_question is None:
                continue

            for img_index, img in enumerate(images):
                try:
                    base_image = doc.extract_image(img[0])
                except Exception:
                    continue

                image_counter += 1
                label = chr(ord("A") + min(img_index, 25))
                ext = base_image.get("ext", "png")
                filename = f"q{current_question}_{label}_{image_counter}.{ext}"
                image_path = os.path.join(output_dir, filename)

                with open(image_path, "wb") as handle:
                    handle.write(base_image["image"])

                question_images.setdefault(current_question, []).append((label, image_path))
    finally:
        doc.close()

    return question_images


def parse_pdf(
    pdf_path: str,
    *,
    progress_callback: Optional[Callable[[float, str], None]] = None,
    extract_images: bool = False,
) -> list[MCQ]:
    """Parse a PDF file and return structured MCQ objects."""
    pdf_path = str(Path(pdf_path).resolve())

    if progress_callback:
        progress_callback(0.1, "Reading PDF…")

    full_text = _extract_text_from_pdf(pdf_path)
    blocks = split_into_question_blocks(full_text)

    if not blocks:
        return []

    if progress_callback:
        progress_callback(0.35, f"Parsing {len(blocks)} questions…")

    mcqs: list[MCQ] = []
    total = len(blocks)
    for index, (number, block) in enumerate(blocks):
        result = parse_question_block(block, number)
        if result:
            mcqs.append(result)
        if progress_callback and index % 25 == 0:
            progress_callback(0.35 + 0.45 * (index / total), f"Parsing {index + 1}/{total}…")

    mcqs.sort(key=lambda item: item.question_number)

    if extract_images and mcqs:
        if progress_callback:
            progress_callback(0.85, "Extracting images…")
        image_dir = tempfile.mkdtemp(prefix="mcq_images_")
        image_map = _extract_images_from_pdf(pdf_path, image_dir)
        for mcq in mcqs:
            for label, path in image_map.get(mcq.question_number, []):
                mcq.images[label] = path

    if progress_callback:
        progress_callback(1.0, f"Done — {len(mcqs)} questions extracted.")

    return mcqs
