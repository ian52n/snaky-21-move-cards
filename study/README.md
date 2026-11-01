# Cards 0–310, step by step

A bare-bones companion to the main viewer, for checking the start of the
21-move certificate by hand. It covers the six base cards (0–5) and certificate
lines 6–310. Card 311 is the first line with parentheses (an inline
expression), so it is left out.

## How to interpret the visualization

Look at the card diagram on the left- it represents valid claim (A,T,h). Cells in A, (the required set) are marked with an X. Maker already owns these. Cells with numbers, and the cell with a gray border, are in T (the envelope). Breaker doesn't own these.
It's maker's turn. He claims the pivot (the cell with a gray border) if it's available. If it isn't, he's already claimed it.

Now maker owns the X cells and the pivot. It's breaker's turn, and she claims a cell.

If she claims a cell marked with a "1" or a cell without a number, then the game proceeds to the Child 1 valid claim. Look at the Child diagram on the right. It shows A_j and T_j for child j on the left, and its placement within the parent card on the right. Click the pivot (the cell outlined in gray) on the right. It highlights the cell in all three diagrams. Look at the bottom of the child diagram to trace how the child cell was transformed to obtain the pivot. Transformations R_s and + (U,V) depend on s and UV in the child reference j:sUV.

If breaker claimed a cell marked with a "2" in the card diagram, then she has blocked continuation to child 1 but child 2 is still available. Click on the orange button for child 2 near the top of the screen. The child visualizations change to show A_j and T_j for child 2, and at the bottom of the Child diagrams the transformations change to reflect permutation R_s and translation UV in child 2's reference j:sUV.

In general, if breaker claimed a cell marked with "n" in the card diagram, she blocked continuation to children 1, 2, ..., n-1 but child n remains available.

This gives us a deterministic strategy for Maker, with explicit transitions from a card to one of its children based on breaker's reply.

## Files

| File | What it is | Do you need to read it? |
| --- | --- | --- |
| `cards.py` | All of the math: reading a line, placing children, rule (2), the cell traces, drawings | Yes. About 300 lines, standard library only; the math is in the first 160 lines. |
| `cards.js` | Data written by `python3 cards.py --web` | No. It is the Python's output. |
| `index.html` | Draws `cards.js` | No. It does no geometry or set operations, and every sentence about a cell is a line written by `trace` in `cards.py`. Its step 2 buttons only pick which of the Python's sets to draw, and which children's placed cells to color in. |
| `minimal/index.html` | A smaller page from the same `cards.js`: the certificate line picks one child, shown colored in on the card and as stored and placed. Numbers on the card show, for each cell Breaker could take after Maker takes p, the first child left clean. | No. It draws only, like `index.html`. |

## Running the Python

From this folder:

```sh
python3 cards.py          # compute cards 0-310 and run the checks
python3 cards.py 47       # every step of card 47, with text drawings
python3 cards.py --web    # rewrite cards.js after you change cards.py
```

In the drawings, `X` is a required cell (in A), `P` is the pivot, `o` is any
other envelope cell (in T), and `.` is outside the envelope. y grows upward.
Only the card being shown gets a `P`. Rule (2) never uses a child's pivot.
Every card's pivot is in its T and not in its A (Lemma 4 and rule (2) both
make it so), so children show it as `o`.

## Reading order for `cards.py`

1. **Placements**: `R` and `place`. `R` follows the bit rule of Section 3.1.
   `check` tests it against table (5) of the paper.
2. **Reading a line**: `point` and `read_line`. `4:714` is card 4 with s = 7,
   moved by (1, 4).
3. **The cards**: `base` is Lemma 4. `rule2` is Lemma 3, rule (2):
   T = {p} ∪ ⋃Tᵢ and A = (⋃Aᵢ ∪ ⋂Tᵢ) \ {p}. `combine` places the children,
   applies `rule2` and sets h = 1 + max hᵢ.
   `first_clean_child` shows why a card works: after Maker takes p, each cell
   Breaker could take in T (outside A and p) misses some child's envelope, so
   that child is still clean. It returns the first such child for each cell.
   `all_cards` reads certificate lines 6–310 in order.
4. **Checks**: table (5), cards 6 and 7, which Section 3.2 of the paper
   works out by hand, and `first_clean_child` on every card 6–310.
5. **Showing a card**: `picture` draws, `trace` follows one stored cell into
   place (`X  (3, 0) -> R_7 -> (0, -3) -> + (1, 4) -> (1, 1)`), and `show`
   prints a whole card.
6. **Data for the web page**: `write_web_data` saves each card's sets, each
   child's placed sets and its `trace` lines. For the step 2 buttons,
   `step2_sets` runs `rule2` on every nonempty choice of the card's children
   and saves each choice's T (the T board). It also saves A for all of the
   children, with and without each of A's last two terms (the A board).
   Choosing every child and every term gives back the card, and the code checks
   that. The card board colors in the placed sets of the children that are on.
   For the minimal page, `replies` holds `first_clean_child` for each card.

## What has been cross-checked

For every card 0–310, the A, T and h computed by `cards.py` match the paper's
own verifier (`verification/verify_certificate.py` in openai/math) and the
main viewer's `engine.js`.

In cards 0–310 the intersection term ⋂Tᵢ never adds a cell: every cell
common to all child envelopes is already required by some child. So for these
cards A is the union of the children's required sets, minus the pivot. The
code still applies the full rule.
