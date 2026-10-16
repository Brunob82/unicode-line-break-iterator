# unicode-line-break-iterator

Segments text into lines at valid UAX #14 line break opportunities for text layout engines.

## Usage

```python
from unicode_line_break_iterator import LineBreaker, line_break_opportunities

# Iterator interface
for offset in LineBreaker("Hello world"):
    print(offset)

# Convenience function
breaks = line_break_opportunities("Hello world")
# [0, 6, 11]
```

The `LineBreaker` class takes a string and yields integer offsets where a
line may be broken. Offset 0 and `len(text)` are always included.
Intermediate offsets point to the start of the next line (the break occurs
before that index).

## Why this exists

Text layout engines need to know where text can wrap. Python's standard
library does not provide UAX #14 line breaking. This library fills that gap
with zero dependencies.

The trade-off: this is a simplified implementation. The full UAX #14
algorithm includes stateful rules for paired quotation marks (LB13/LB14)
and numeric context resolution that require multi-character lookahead and
backtracking. Those rules are not implemented here because they add
significant complexity for marginal benefit in general text layout. The
pair-based direct/indirect break rules are fully implemented.

## Edge cases you will hit

**AL-AL breaks are allowed.** In strict UAX #14, breaks between alphabetic
characters (AL class) are indirect — they only happen when a space is
present. This library allows direct breaks between AL characters. This is a
deliberate tailoring so that CJK ideographs (which are mapped to AL here
rather than the ID class) break between each other as expected for East
Asian text layout. If you need strict UAX #14 behavior for Latin text where
mid-word breaks are forbidden, this library will over-segment.

**Paired quotation state is not tracked.** The QU class is handled with
simplified rules. Text like `("open"` may not break exactly where a full
implementation would allow.

**CR+LF is treated as a single break point.** A break is reported after the
combined sequence, not after the CR alone.

## Performance

The window keeps a bounded buffer, so `push` is constant time and memory does not
grow with the length of the stream. `peak` and `trough` are linear in the window
size, which is the trade that keeps `push` cheap.

