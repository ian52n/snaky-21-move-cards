# Snaky 21-Move Cards

A single-page viewer for the 728 cards of the 21-move Snaky certificate from
“Snaky in 21 Maker moves” (OpenAI, 2026), Appendix D. Each card shows its
required cells (X), pivot (gray) and envelope (white) beside its child
conditions, with a simulator for Breaker's reply.

## Use it or host it

`index.html` is self-contained: the certificate and all code are inline. Only
the Google Fonts stylesheet loads from the web, and the page falls back to
system fonts without it.

- Open `index.html` directly in a browser, or
- upload it to any static host (GitHub Pages, Netlify, Vercel, Cloudflare Pages, a university web space).

Link to a specific card with `#c<number>`, for example `index.html#c727`.

On load the page recomputes every card from the combination rule (Lemma 3,
equation (2)), checks that each of the 37,042 Breaker reply classes leaves a
child alive, and compares the certificate's SHA-256 with the value printed in
the paper. The SHA-256 check needs HTTPS, `localhost` or a local file.

## Rebuild

```sh
python3 build.py              # writes index.html
python3 build.py --artifact   # writes the variant used as a Claude artifact
```

`build.py` refuses to build if `certificate.txt` differs from the paper's file.

## Cross-check the engine against the paper

From the paper's folder in https://github.com/openai/math, write the paper's own
reconstruction of every card:

```sh
python3 verification/supporting/route21/primary.py --output reference.json
```

Then, from this folder:

```sh
node test_engine.js certificate.txt path/to/reference.json
```

It compares all 728 cards and all 1,620 combination nodes (inline ones
included) and checks the counts in Section 6 of the paper.

## Files

| File | Contents |
| --- | --- |
| `index.html` | The built page |
| `template.html` | Layout, styles and interaction |
| `engine.js` | Certificate parser and combination rule; runs in the browser and in Node |
| `certificate.txt` | Appendix D, byte-identical to `verification/certificate.txt` (SHA-256 `3fa12d36…3d04`) |
| `build.py` | Inlines the engine and certificate into `index.html` |
| `test_engine.js` | Cross-check against the paper's reconstruction |
| `certificate-LICENSE.txt` | Apache License 2.0, which covers `certificate.txt` |

## Attribution

`certificate.txt` is copied unchanged from
https://github.com/openai/math/blob/main/preprints/Snaky-in-21-Maker-moves-September-25-2026/verification/certificate.txt
and is licensed under the Apache License, Version 2.0 (`certificate-LICENSE.txt`).
