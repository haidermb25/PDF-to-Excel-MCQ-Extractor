"""MCQ data models and parsing utilities."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional


OPTION_LABEL = re.compile(r"^([A-Z])\.\s*", re.MULTILINE)
QUESTION_HEADER = re.compile(r"^QUESTION\s+\d+\s*$", re.MULTILINE | re.IGNORECASE)
ANSWER_PATTERN = re.compile(
    r"^Answer\s*:\s*([A-Z](?:\s*,\s*[A-Z])*)",
    re.MULTILINE | re.IGNORECASE,
)
EXPLANATION_PATTERN = re.compile(r"^Explanation\s*:", re.MULTILINE | re.IGNORECASE)
REFERENCE_PATTERN = re.compile(r"^Reference\s*:", re.MULTILINE | re.IGNORECASE)


@dataclass
class MCQ:
    """A single multiple-choice question."""

    question_number: int
    question_text: str
    options: dict[str, str] = field(default_factory=dict)
    correct_answers: list[str] = field(default_factory=list)
    explanation: str = ""
    images: dict[str, str] = field(default_factory=dict)

    @property
    def answer_type(self) -> int:
        """0 = single-select (radio), 1 = multi-select (checkbox)."""
        return 1 if len(self.correct_answers) > 1 else 0

    @property
    def answer_display(self) -> str:
        return ", ".join(self.correct_answers)

    @property
    def image_display(self) -> str:
        if not self.images:
            return ""
        parts = [f"{label}: {path}" for label, path in sorted(self.images.items())]
        return "; ".join(parts)


def _normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _extract_explanation(block: str) -> str:
    """Extract explanation text; stops before Reference section."""
    match = EXPLANATION_PATTERN.search(block)
    if not match:
        return ""
    rest = block[match.end() :]
    ref_match = REFERENCE_PATTERN.search(rest)
    if ref_match:
        rest = rest[: ref_match.start()]
    return re.sub(r"\s+", " ", rest).strip()


def _strip_trailing_sections(block: str) -> str:
    """Remove explanation, reference, and content after the answer line."""
    for pattern in (EXPLANATION_PATTERN, REFERENCE_PATTERN):
        match = pattern.search(block)
        if match:
            block = block[: match.start()]
    return block.strip()


def _parse_answer_letters(raw: str) -> list[str]:
    letters = re.findall(r"[A-Z]", raw.upper())
    seen: set[str] = set()
    ordered: list[str] = []
    for letter in letters:
        if letter not in seen:
            seen.add(letter)
            ordered.append(letter)
    return ordered


def parse_question_block(block: str, question_number: int) -> Optional[MCQ]:
    """Parse a single question text block into an MCQ."""
    block = _normalize_text(block)
    if not block:
        return None

    block = QUESTION_HEADER.sub("", block, count=1).strip()
    explanation = _extract_explanation(block)
    block = _strip_trailing_sections(block)

    answer_match = ANSWER_PATTERN.search(block)
    if not answer_match:
        return None

    correct_answers = _parse_answer_letters(answer_match.group(1))
    content_before_answer = block[: answer_match.start()].strip()

    option_matches = list(OPTION_LABEL.finditer(content_before_answer))
    if not option_matches:
        return None

    first_option_start = option_matches[0].start()
    question_text = content_before_answer[:first_option_start].strip()
    question_text = re.sub(r"\s+", " ", question_text)

    options: dict[str, str] = {}
    for idx, match in enumerate(option_matches):
        label = match.group(1)
        start = match.end()
        end = (
            option_matches[idx + 1].start()
            if idx + 1 < len(option_matches)
            else len(content_before_answer)
        )
        option_text = content_before_answer[start:end].strip()
        option_text = re.sub(r"\s+", " ", option_text)
        options[label] = option_text

    if not question_text or not options or not correct_answers:
        return None

    return MCQ(
        question_number=question_number,
        question_text=question_text,
        options=options,
        correct_answers=correct_answers,
        explanation=explanation,
    )


def split_into_question_blocks(full_text: str) -> list[tuple[int, str]]:
    """Split PDF text into numbered question blocks."""
    full_text = _normalize_text(full_text)
    parts = QUESTION_HEADER.split(full_text)
    headers = QUESTION_HEADER.findall(full_text)

    blocks: list[tuple[int, str]] = []
    for header, body in zip(headers, parts[1:], strict=False):
        number_match = re.search(r"\d+", header)
        if not number_match:
            continue
        number = int(number_match.group())
        blocks.append((number, f"{header.strip()}\n{body.strip()}"))

    return blocks
