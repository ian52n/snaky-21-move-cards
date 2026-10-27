# Cards 0–310, step by step

A bare-bones companion to the main viewer, for checking the start of the
21-move certificate by hand. It covers the six base cards (0–5) and certificate
lines 6–310. Card 311 is the first line with parentheses (an inline
expression), so it is left out.

## Files

| File | What it is | Do you need to read it? |
| --- | --- | --- |
| `cards.py` | All of the math: reading a line, placing children, rule (2), the cell traces, drawings | Yes. Under 250 lines, standard library only; the math is in the first 150 lines. |
| `cards.js` | Data written by `python3 cards.py --web` | No. It is the Python's output. |
| `index.html` | Draws `cards.js` | No. It does no geometry or set operations, and every sentence about a cell is a line written by `trace` in `cards.py`. |

## Running the Python

From this folder:

```sh
python3 cards.py          # compute cards 0-310 and run the checks
python3 cards.py 47       # every step of card 47, with text drawings
python3 cards.py --web    # rewrite cards.js after you change cards.py
```

In the drawings, `X` is a required cell (in A), `P` is the pivot, `o` is any
other envelope cell (in T), and `.` is outside the envelope. y grows upward.

## Reading order for `cards.py`

1. **Placements**: `R` and `place`. `R` follows the bit rule of Section 3.1.
   `check` tests it against table (5) of the paper.
2. **Reading a line**: `point` and `read_line`. `4:714` is card 4 with s = 7,
   moved by (1, 4).
3. **The cards**: `base` is Lemma 4. `combine` is Lemma 3, rule (2):
   T = {p} ∪ ⋃Tᵢ and A = (⋃Aᵢ ∪ ⋂Tᵢ) \ {p}, h = 1 + max hᵢ.
   `all_cards` reads certificate lines 6–310 in order.
4. **Checks**: table (5), and cards 6 and 7, which Section 3.2 of the paper
   works out by hand.
5. **Showing a card**: `picture` draws, `trace` follows one stored cell into
   place (`X  (3, 0) -> R_7 -> (0, -3) -> + (1, 4) -> (1, 1)`), and `show`
   prints a whole card.
6. **Data for the web page**: `write_web_data` saves each card's sets, each
   child's placed sets and its `trace` lines. It computes nothing new.

## What has been cross-checked

For every card 0–310, the A, T and h computed by `cards.py` match the paper's
own verifier (`verification/verify_certificate.py` in openai/math) and the
main viewer's `engine.js`.

In cards 0–310 the intersection term ⋂Tᵢ never adds a cell: every cell
common to all child envelopes is already required by some child. So for these
cards A is the union of the children's required sets, minus the pivot. The
code still applies the full rule.
