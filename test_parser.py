"""Unit tests for MCQ parsing logic."""

import unittest

from mcq_models import parse_question_block, split_into_question_blocks


SAMPLE_BLOCK = """QUESTION 1
Which of the following threat actors is most likely to be hired by a foreign
government to attack critical systems located in other countries?
A. Hacktivist
B. Whistleblower
C. Organized crime
D. Unskilled attacker
Answer: C
Explanation: Organized crime groups are often hired by nation-states.
Reference: SY0-701, Objective 1.2
"""

MULTI_ANSWER_BLOCK = """QUESTION 42
Select TWO security controls that protect data at rest.
A. Full-disk encryption
B. TLS 1.3
C. Database encryption
D. VPN tunneling
Answer: A, C
Explanation: TLS and VPN protect data in transit.
"""

SAMPLE_FULL_TEXT = SAMPLE_BLOCK + "\n\n" + MULTI_ANSWER_BLOCK


class TestMCQParsing(unittest.TestCase):
    def test_single_answer_question(self) -> None:
        mcq = parse_question_block(SAMPLE_BLOCK, 1)
        assert mcq is not None
        self.assertEqual(mcq.question_number, 1)
        self.assertIn("threat actors", mcq.question_text)
        self.assertEqual(mcq.options["C"], "Organized crime")
        self.assertEqual(mcq.correct_answers, ["C"])
        self.assertEqual(mcq.answer_type, 0)
        self.assertIn("Organized crime groups", mcq.explanation)

    def test_multi_answer_question(self) -> None:
        mcq = parse_question_block(MULTI_ANSWER_BLOCK, 42)
        assert mcq is not None
        self.assertEqual(mcq.correct_answers, ["A", "C"])
        self.assertEqual(mcq.answer_type, 1)
        self.assertIn("TLS and VPN", mcq.explanation)

    def test_explanation_not_in_options(self) -> None:
        mcq = parse_question_block(SAMPLE_BLOCK, 1)
        assert mcq is not None
        for option in mcq.options.values():
            self.assertNotIn("Explanation", option)
            self.assertNotIn("Reference", option)

    def test_split_into_blocks(self) -> None:
        blocks = split_into_question_blocks(SAMPLE_FULL_TEXT)
        self.assertEqual(len(blocks), 2)
        self.assertEqual(blocks[0][0], 1)
        self.assertEqual(blocks[1][0], 42)


if __name__ == "__main__":
    unittest.main()
