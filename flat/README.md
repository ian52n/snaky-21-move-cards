# The certificate without parentheses

The paper's certificate has 722 numbered lines and 898 expressions written in
parentheses. Each parenthesized expression is one more application of Lemma 3,
used once, in the coordinate frame of its line. Here every one of them gets its
own card number, so each line is a pivot followed by a plain list of children.
The result has 1,626 cards (6 bases and 1,620 lines) and no parentheses.

## Files

| File | What it is |
| --- | --- |
| `flatten.py` | Writes the two files below from `../certificate.txt` |
| `certificate-flat.txt` | The flat certificate, in the paper's grammar (Section 3.1), lines 6–1625 |
| `labels.txt` | For every flat card number, its name in the paper (see below) |
| `check_flat.py` | Checks that the flat files say exactly what the paper's certificate says. Does not use `flatten.py`. |
| `check_engine.js` | A second check, with the viewer's `../engine.js` instead of Python |

## Running

From this folder:

```sh
python3 flatten.py                  # rewrite certificate-flat.txt and labels.txt
python3 check_flat.py               # checks 0-4 below
python3 check_flat.py --tamper-test # damage the files in small ways; every change must be caught
node check_engine.js                # the second check
```

`certificate-flat.txt` has SHA-256
`b07943a68577cd8fb4736e7d335bad515c5c1e10fbc69f3d93694fabd84242d7`.

## Numbers and labels

A label names a card by where it sits in the paper's certificate:

| Label | Meaning |
| --- | --- |
| `357` | the paper's card 357 |
| `357.2` | the 2nd child of card 357, written in parentheses there |
| `357.2.2` | the 2nd child of `357.2`, and so on |

Flat cards are numbered in the order the paper evaluates them, innermost
expression first. Inline children therefore come just before the line that
contains them, and every reference still points to a smaller number. Cards
0–310 keep their numbers. From 311 on they shift: the paper's 311 is flat card
312, and its inline child `311.2` is flat card 311. The paper's 727 is flat
card 1625.

A parenthesized child becomes a bare reference (identity placement). Every other
child keeps its placement code, with its card number translated.

## The checks

`check_flat.py` runs five checks:

0. `../certificate.txt` has the SHA-256 printed in Section 6.2 of the paper.
1. The flat files are well formed: lines 6, 7, 8, … in order, no
   parentheses, every reference to a smaller number, one label per card.
2. **Round trip.** Every card whose label has a dot (like `357.2`) is used
   exactly once in the flat list: by a bare reference, as the stated child of
   the card its label names. Putting each such card back in parentheses at that
   spot, and turning flat numbers back into labels, gives `../certificate.txt`
   byte for byte.
3. **The flat list stands on its own.** Rule (2) applied line by line, starting
   from the six bases of Lemma 4, ends with a card that has A = ∅, |T| = 251,
   T ⊆ {0, …, 16}² and height 21. These are the conditions of Proposition 5.
4. **Same values.** Evaluating the paper's certificate the paper's way, with
   each parenthesized expression evaluated in place and innermost first, gives
   the same A, T and h at all 1,626 cards and expressions as the flat list.

`check_engine.js` repeats 2 and 4 with a different parser and evaluator, and
also compares the strategy of Section 4: at every node, for each of the 37,042
Breaker reply classes, the first surviving child in printed order is the same.

## Why the round trip proves equivalence

Check 2 says that flat card n and the paper's node with the same label have the
same pivot and the same children, in the same order. For each child, one of two
things holds:

- **A reference.** The paper's `j:sUV` became `k:sUV`, where flat card k has
  label j.
- **A parenthesized expression.** The paper's `(… )` at position i became a
  bare reference to the flat card labeled `L.i`.

Now induct on n. A bare reference brings in card `L.i` with the identity
placement. That is exactly how the paper brings in an inline expression: its
coordinates are already in the line's frame, not offsets from the enclosing
pivot (Section 3.1). So rule (2) gets the same inputs on both sides and gives
the same A, T and h.

The strategy is also unchanged. Section 4 moves from placement F to F∘G for a
referenced card with placement G, and keeps F for an inline expression. With
G the identity, these agree. The strategy picks the first surviving child in
printed order, so the order of children matters. Check 4 alone can't see order,
because unions and intersections don't depend on it. The round trip can.

Check 3 needs none of this. The flat list is a valid certificate by Lemmas 3
and 4 whether or not it matches the paper. The other checks show that it is the
paper's proof, step for step, under new names.

## What the tamper test changes

| Change | Checks that fail |
| --- | --- |
| A placement code in card 6 | 2, 3, 4 |
| The order of card 6's two children | 2 |
| The pivot of flat card 311 (`311.2`) | 2, 3, 4 |
| Card 312 points at card 310 instead of its inline child 311 | 2, 3, 4 |
| `311` written as `311:000` (the same placement, written out) | 2 |
| The last card deleted | 2, 3, 4 |
| The labels of flat cards 311 and 312 swapped | 2, 4 |

The round trip is strict: `311:000` means the same as `311`, but it is not what
the flattening rule writes, so check 2 rejects it.
