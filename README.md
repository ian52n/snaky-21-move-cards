# Snaky 21-Move Cards

An interactive viewer for the 728 cards of the 21-move Snaky certificate from
“Snaky in 21 Maker moves” (OpenAI, 2026), Appendix D. The live page is linked
in this repository's About panel.

Each card is drawn on square cells: X marks a required cell, gray is the
pivot, and white is the rest of the envelope. The card's child conditions are
drawn in the same coordinates. Hover a cell to place a Breaker reply and see
which children survive; click a child to follow it down the proof.

Link to a specific card with `#c<number>`, for example `#c727`.

## How the page checks itself

On every load the page recomputes all 728 cards from the combination rule
(Lemma 3, equation (2)), checks that each of the 37,042 Breaker reply classes
leaves a child alive, and compares the certificate's SHA-256 with the value
printed in the paper.

## Rebuild

`index.html` is generated. Edit `template.html` or `engine.js`, then run:

```sh
python3 build.py              # writes index.html
python3 build.py --artifact   # writes the variant used as a Claude artifact
```

`build.py` stops if `certificate.txt` differs from the paper's file.

## Cross-check against the paper's own reconstruction

In a clone of https://github.com/openai/math, from the folder
`preprints/Snaky-in-21-Maker-moves-September-25-2026`:

```sh
python3 verification/supporting/route21/primary.py --output reference.json
```

Then, in this repository:

```sh
node test_engine.js certificate.txt path/to/reference.json
```

This compares all 728 cards and all 1,620 combination nodes, inline ones
included, and checks the counts in Section 6 of the paper.

## Files

| File | Contents |
| --- | --- |
| `index.html` | The page that GitHub Pages serves (generated) |
| `template.html` | Layout, styles and interaction |
| `engine.js` | Certificate parser and combination rule; runs in the browser and in Node |
| `certificate.txt` | Appendix D, byte-identical to the paper's `verification/certificate.txt` |
| `build.py` | Inlines the engine, certificate and license text into `index.html` |
| `test_engine.js` | Cross-check against the paper's reconstruction |

## License and credits

This project is licensed under the Apache License 2.0; see `LICENSE`.

`certificate.txt` is the certificate from “Snaky in 21 Maker moves” (OpenAI,
2026), copied unchanged from
https://github.com/openai/math/tree/main/preprints/Snaky-in-21-Maker-moves-September-25-2026,
where it is distributed under the Apache License 2.0. See `NOTICE`.

This project is independent and is not affiliated with or endorsed by OpenAI.

To cite the paper, its repository gives:

```bibtex
@misc{OAI:Snaky-in-21-Maker-moves-September-25-2026,
  author = {{OpenAI}},
  title = {{Snaky in 21 Maker moves}},
  howpublished = {OpenAI Math Release preprint
                  \href{https://github.com/openai/math/blob/main/preprints/Snaky-in-21-Maker-moves-September-25-2026/article.pdf}{OAI:Snaky-in-21-Maker-moves-September-25-2026}},
  year = {2026}
}
```
