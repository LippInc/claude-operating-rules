#!/usr/bin/env python3
"""The four-token contract from MECHANISMS.md, in about 80 lines. Standard library, any OS, Python 3 (3.8+ syntax; CI runs 3.x).

    python examples/example_suite.py            # normal run: every known-bad must go RED, exit 0
    python examples/example_suite.py --break    # sabotage the mechanism: the known-bads it guarded go GREEN, exit 2
    python examples/example_suite.py --vacuous  # drop every known-bad: a run that proves nothing must not exit 0, exit 3
    python examples/example_suite.py --typo     # any unknown flag: refuse to run, exit 1 (a typo must not hand you a green)

The mechanism under test is deliberately trivial - a check that a string is an acceptable answer of at most N
words - so that nothing here distracts from the shape. What matters is that the suite can PROVE it catches
things, and that running it with --break or --vacuous shows you what a broken or empty suite looks like.
A suite you have never seen fail is not evidence.
"""
import sys

FLAGS = {"--break", "--vacuous"}
unknown = [a for a in sys.argv[1:] if a not in FLAGS]
if unknown:
    sys.exit("unknown argument(s): %s (known: %s)" % (" ".join(unknown), " ".join(sorted(FLAGS))))
BROKEN = "--break" in sys.argv
VACUOUS = "--vacuous" in sys.argv


def within_word_limit(text, limit):
    """The mechanism. An acceptable answer has at least two words, ends a sentence, and has at most `limit` words."""
    words = text.split()
    if not BROKEN:
        # The degenerate-input guard from MECHANISMS.md: without this, a one-word answer, or an empty one,
        # sails through a "40 words or less" gate. Counting is not judging.
        if len(words) < 2:
            return False
        # And a count-valid answer that stops mid-thought is not a complete answer: check the LAST unit.
        if not text.rstrip().endswith((".", "!", "?")):
            return False
    return len(words) <= limit


CASES = [
    # (label, text, limit, expect_ok, is_known_bad)   known-bad rows always expect_ok=False
    ("ordinary answer inside the limit",      "The driver is the bigger bill.",        40, True,  False),
    ("ordinary answer at exactly the limit",  "One two three four five six.",           6, True,  False),
    ("short but complete answer is fine",     "It works.",                             40, True,  False),
    ("over the limit is rejected",            "word " * 50 + ".",                      40, False, True),
    ("one word over the limit is rejected",   "One two three four five six seven.",     6, False, True),
    ("a 3-character answer is not an answer", "yes",                                   40, False, True),
    ("an empty answer is not an answer",      "",                                      40, False, True),
    ("count-valid but cut off mid-thought",   "This sentence just stops and",          40, False, True),
]
if VACUOUS:
    CASES = [c for c in CASES if not c[4]]

red = green = passed = failed = 0
for label, text, limit, expect_ok, known_bad in CASES:
    if known_bad and expect_ok is not False:
        sys.exit("a known-bad row must expect rejection: %s" % label)   # not an assert: -O would strip it
    ok = within_word_limit(text, limit)
    if known_bad:
        if not ok:
            print("KNOWN-BAD-RED   %s" % label); red += 1
        else:
            print("KNOWN-BAD-GREEN %s  <- the mechanism did NOT catch this" % label); green += 1
    else:
        if ok is expect_ok:
            print("PASS            %s" % label); passed += 1
        else:
            print("FAIL            %s" % label); failed += 1

print("\n%d PASS / %d FAIL / %d KNOWN-BAD-RED / %d KNOWN-BAD-GREEN" % (passed, failed, red, green))

# Order matters: a green or a failed control is rung 2 and must be reported as such even when no red was seen.
if green or failed:
    print("EXIT 2 - a known-bad went green, or a positive control failed"); sys.exit(2)
# Rung 4 of the exit-code ladder, about the suite itself: a run that demonstrated no red must never look like success.
if red == 0:
    print("EXIT 3 - no known-bad was demonstrated, so this run proves nothing"); sys.exit(3)
print("EXIT 0 - instrument proved: every known-bad went red, every control passed")
sys.exit(0)
