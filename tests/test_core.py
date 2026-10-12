"""Tests for the unicode_line_break_iterator package.

All tests run under `python -m unittest discover -s tests` with
PYTHONPATH=src.
"""

import unittest

from unicode_line_break_iterator import LineBreaker, BreakClass, line_break_opportunities
from unicode_line_break_iterator.core import _classify_char, _can_break


class TestClassification(unittest.TestCase):

    def test_space_is_sp(self):
        self.assertEqual(_classify_char(" "), BreakClass.SP)

    def test_newline_classes(self):
        self.assertEqual(_classify_char("\n"), BreakClass.LF)
        self.assertEqual(_classify_char("\r"), BreakClass.CR)
        self.assertEqual(_classify_char("\x85"), BreakClass.NL)

    def test_word_joiner(self):
        self.assertEqual(_classify_char("\u2060"), BreakClass.WJ)

    def test_zero_width_space(self):
        self.assertEqual(_classify_char("\u200B"), BreakClass.ZW)

    def test_no_break_space_is_gl(self):
        self.assertEqual(_classify_char("\u00A0"), BreakClass.GL)

    def test_hyphen_minus_is_hy(self):
        self.assertEqual(_classify_char("-"), BreakClass.HY)

    def test_em_dash_is_b2(self):
        self.assertEqual(_classify_char("\u2014"), BreakClass.B2)

    def test_opening_paren_is_op(self):
        self.assertEqual(_classify_char("("), BreakClass.OP)

    def test_closing_paren_is_cp(self):
        self.assertEqual(_classify_char(")"), BreakClass.CP)

    def test_digits_are_nu(self):
        self.assertEqual(_classify_char("5"), BreakClass.NU)

    def test_letters_are_al(self):
        self.assertEqual(_classify_char("A"), BreakClass.AL)
        self.assertEqual(_classify_char("x"), BreakClass.AL)

    def test_cjk_ideograph_is_al(self):
        # Simplification documented in README: CJK mapped to AL
        self.assertEqual(_classify_char("\u4E00"), BreakClass.AL)


class TestCanBreak(unittest.TestCase):

    def test_wj_blocks_break(self):
        self.assertFalse(_can_break(BreakClass.AL, BreakClass.WJ))
        self.assertFalse(_can_break(BreakClass.WJ, BreakClass.AL))

    def test_gl_blocks_break(self):
        self.assertFalse(_can_break(BreakClass.AL, BreakClass.GL))
        self.assertFalse(_can_break(BreakClass.GL, BreakClass.AL))

    def test_zwj_blocks_break_from_before(self):
        self.assertFalse(_can_break(BreakClass.AL, BreakClass.ZWJ))

    def test_zw_allows_break(self):
        self.assertTrue(_can_break(BreakClass.ZW, BreakClass.AL))

    def test_no_break_before_closing_paren(self):
        self.assertFalse(_can_break(BreakClass.AL, BreakClass.CP))

    def test_no_break_after_opening_paren(self):
        self.assertFalse(_can_break(BreakClass.OP, BreakClass.AL))

    def test_break_after_hyphen(self):
        self.assertTrue(_can_break(BreakClass.HY, BreakClass.AL))

    def test_b2_no_break_between_two_b2(self):
        self.assertFalse(_can_break(BreakClass.B2, BreakClass.B2))

    def test_no_break_before_nonstarter(self):
        self.assertFalse(_can_break(BreakClass.AL, BreakClass.NS))


class TestLineBreaker(unittest.TestCase):

    def test_empty_string(self):
        self.assertEqual(line_break_opportunities(""), [0])

    def test_single_char(self):
        self.assertEqual(line_break_opportunities("A"), [0, 1])

    def test_simple_word_no_spaces(self):
        # AL-AL allows break in our implementation (CJK tailoring)
        self.assertEqual(line_break_opportunities("Hello"), [0, 1, 2, 3, 4, 5])

    def test_space_creates_break(self):
        # Break after the space, not before
        result = line_break_opportunities("hello world")
        self.assertIn(6, result)
        self.assertNotIn(5, result)
        self.assertEqual(result[0], 0)
        self.assertEqual(result[-1], 11)

    def test_multiple_spaces(self):
        # Consecutive spaces produce one break after the group
        result = line_break_opportunities("a  b")
        self.assertIn(3, result)  # after the two spaces
        self.assertEqual(result[-1], 4)

    def test_newline_breaks_after(self):
        result = line_break_opportunities("abc\ndef")
        self.assertIn(4, result)
        self.assertEqual(result[-1], 7)

    def test_cr_lf_treated_as_single_break(self):
        result = line_break_opportunities("abc\r\ndef")
        # Break should be at offset 5 (after CR+LF), not at 4
        self.assertIn(5, result)
        self.assertNotIn(4, result)

    def test_zero_width_space_breaks(self):
        result = line_break_opportunities("abc\u200Bdef")
        self.assertIn(4, result)

    def test_word_joiner_prevents_break(self):
        result = line_break_opportunities("abc\u2060def")
        # No break at position 4 (the WJ itself)
        self.assertNotIn(4, result)

    def test_opening_paren_no_break_after(self):
        result = line_break_opportunities("(abc")
        # No break between ( and a
        self.assertNotIn(1, result)

    def test_closing_paren_no_break_before(self):
        result = line_break_opportunities("abc)")
        # No break between c and )
        self.assertNotIn(3, result)

    def test_hyphen_allows_break_after(self):
        result = line_break_opportunities("well-known")
        self.assertIn(5, result)  # after the hyphen

    def test_em_dash_breaks_on_both_sides(self):
        result = line_break_opportunities("a\u2014b")
        # Break before and after em dash, but not between two em dashes
        self.assertIn(1, result)
        self.assertIn(2, result)

    def test_no_break_space_does_not_break(self):
        result = line_break_opportunities("a\u00A0b")
        # GL prevents break
        self.assertNotIn(1, result)
        self.assertNotIn(2, result)

    def test_always_starts_with_zero(self):
        for text in ["", "a", "hello world", "\n", "  "]:
            result = line_break_opportunities(text)
            self.assertEqual(result[0], 0)

    def test_always_ends_with_len(self):
        for text in ["", "a", "hello world", "\n", "  "]:
            result = line_break_opportunities(text)
            self.assertEqual(result[-1], len(text))

    def test_breaks_are_strictly_increasing(self):
        for text in ["Hello, world!", "a-b-c", "foo bar baz", "\u4E00\u4E01\u4E02"]:
            result = line_break_opportunities(text)
            for a, b in zip(result, result[1:]):
                self.assertLess(a, b)

    def test_cjk_ideographs_break_between_each(self):
        # Documented tailoring: AL-AL breaks are allowed, so CJK breaks
        result = line_break_opportunities("\u4E00\u4E01")
        self.assertIn(1, result)

    def test_iterator_protocol(self):
        breaker = LineBreaker("ab cd")
        offsets = list(breaker)
        self.assertEqual(offsets[0], 0)
        self.assertEqual(offsets[-1], 5)
        self.assertIn(3, offsets)  # after the space

    def test_digits_no_break_between(self):
        # NU-NU does not break
        result = line_break_opportunities("12345")
        self.assertEqual(result, [0, 5])

    def test_slash_breaks_after(self):
        result = line_break_opportunities("a/b")
        self.assertIn(2, result)  # after the slash

    def test_multiple_newlines(self):
        result = line_break_opportunities("a\nb\nc")
        self.assertIn(2, result)
        self.assertIn(4, result)

    def test_text_with_only_spaces(self):
        result = line_break_opportunities("   ")
        self.assertEqual(result[0], 0)
        self.assertEqual(result[-1], 3)

    def test_trailing_space(self):
        result = line_break_opportunities("abc ")
        self.assertEqual(result[-1], 4)


class TestBreakClassEnum(unittest.TestCase):

    def test_enum_values_are_strings(self):
        self.assertEqual(BreakClass.AL.value, "AL")
        self.assertEqual(BreakClass.SP.value, "SP")

    def test_enum_unique(self):
        # Ensure no duplicate values
        values = [c.value for c in BreakClass]
        self.assertEqual(len(values), len(set(values)))


if __name__ == "__main__":
    unittest.main()
