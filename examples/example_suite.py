#!/usr/bin/env python3
"""The four-token contract from MECHANISMS.md, in about 50 lines. Standard library, any OS, any Python 3.8+.

    python examples/example_suite.py          # normal run: every known-bad must go RED
    python examples/example_suite.py --break  # sabotage the mechanism: known-bads go GREEN, exit 2

The mechanism under test is deliberately trivial - a check that a string is at most N words - so that nothing
here distracts from the shape. What matters is that the suite can PROVE it catches things, and that running it
with --break shows you what a broken mechanism looks like. A suite you have never seen fail is not evidence.
"""
import sys

BROKEN = "--break" in sys.argv


def within_word_limit(text, limit):
    """The mechanism. Returns True if `text` is an acceptable answer of at most `limit` words."""
    words = text.split()
    if not BROKEN:
        # Rung 4 of the exit-code ladder: guard the degenerate input explicitly. Without this, a 3-character
        # answer - or an empty one - sails through a "40 words or less" gate. Counting is not judging.
        if len(words) < 3:
            return False
        # And a count-valid answer that stops mid-thought is not a complete answer: check the LAST unit.
        if not text.rstrip().endswith((".", "!", "?")):
            return False
    return len(words) <= limit


CASES = [
    # (label, text, limit, expect_ok, is_known_bad)
    ("ordinary answer inside the limit",      "The driver is the bigger bill.", 40, True,  False),
    ("ordinary answer at exactly the limit",  "One two three four five six.",    6, True,  False),
    ("over the limit is rejected",            "word " * 50 + ".",               40, False, True),
    ("a 3-character answer is not an answer", "ok",                             40, False, True),
    ("an empty answer is not an answer",      "",                               40, False, True),
    ("count-valid but cut off mid-thought",   "This sentence just stops and",   40, False, True),
]

red = green = passed = failed = 0
for label, text, limit, expect_ok, known_bad in CASES:
    ok = within_word_limit(text, limit)
    if known_bad:
        if ok is False:
            print("KNOWN-BAD-RED   %s" % label); red += 1
        else:
            print("KNOWN-BAD-GREEN %s  <- the mechanism did NOT catch this" % label); green += 1
    else:
        if ok is expect_ok:
            print("PASS            %s" % label); passed += 1
        else:
            print("FAIL            %s" % label); failed += 1

print("\n%d PASS / %d FAIL / %d KNOWN-BAD-RED / %d KNOWN-BAD-GREEN" % (passed, failed, red, green))

# Rung 4 again, this time about the suite itself: a run that asserted nothing must never look like success.
if red == 0:
    print("EXIT 3 - no known-bad was demonstrated, so this run proves nothing"); sys.exit(3)
if green or failed:
    print("EXIT 2 - a known-bad went green, or a positive control failed"); sys.exit(2)
print("EXIT 0 - instrument proved: every known-bad went red, every control passed")
sys.exit(0)
