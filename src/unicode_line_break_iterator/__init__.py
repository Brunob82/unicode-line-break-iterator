"""Unicode Line Break Iterator.

Segments text into lines at valid UAX #14 line break opportunities for
text layout engines.

Exported names:
  - LineBreaker: class implementing UAX #14 line breaking
  - line_break_opportunities: convenience function returning break offsets
  - BreakClass: enumeration of Unicode line break categories
"""

from .core import LineBreaker, BreakClass, line_break_opportunities

__all__ = ["LineBreaker", "BreakClass", "line_break_opportunities"]
