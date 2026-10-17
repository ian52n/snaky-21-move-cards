"""Build the Snaky 21-move card viewer as one self-contained HTML file.

    python3 build.py              -> index.html  (standalone page for any web host, or open it locally)
    python3 build.py --artifact   -> snaky-21-move-cards.html  (body-only variant for a Claude artifact)

Inputs, all in this folder: template.html, engine.js, certificate.txt, LICENSE.
The certificate must be byte-identical to the paper's (SHA-256 checked below).
LICENSE must hold the Apache License 2.0 text, which the page displays for the certificate.
"""
import hashlib
import html
import json
import re
import sys
import urllib.parse
from pathlib import Path

CERT_SHA256 = '3fa12d36a6d4dbb185e3f2808c8dfde13d85ee309afbca030d6ad17ae9fe3d04'
DESCRIPTION = ('Browse all 728 cards of the 21-move Snaky certificate: required cells, pivot and envelope '
               'of each card beside its child conditions, with a Breaker-reply simulator.')
FAVICON_SVG = (
    "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'>"
    "<rect width='32' height='32' rx='6' fill='#edf1ee'/>"
    "<rect x='3.5' y='9.5' width='12.5' height='12.5' fill='#fff' stroke='#3a423d' stroke-width='1.5'/>"
    "<path d='M6.6 12.6l6.3 6.3M12.9 12.6l-6.3 6.3' stroke='#131615' stroke-width='2.2' stroke-linecap='round'/>"
    "<rect x='16' y='9.5' width='12.5' height='12.5' fill='#a3a8a5' stroke='#3a423d' stroke-width='1.5'/>"
    "</svg>"
)


def assemble(here: Path) -> str:
    cert = (here / 'certificate.txt').read_bytes()
    if hashlib.sha256(cert).hexdigest() != CERT_SHA256:
        sys.exit('certificate.txt does not match the paper (SHA-256 mismatch)')
    engine = (here / 'engine.js').read_text()
    page = (here / 'template.html').read_text()
    license_text = (here / 'LICENSE').read_text()
    if 'Apache License' not in license_text or 'Version 2.0' not in license_text:
        sys.exit('LICENSE must hold the Apache License 2.0 text, which the page shows for the certificate data')
    cert_json = json.dumps(cert.decode('ascii'))
    assert '</script' not in cert_json and '</script' not in engine
    page = page.replace('__LICENSE_TEXT__', html.escape(license_text.strip('\n'), quote=False))
    return page.replace('__CERT_JSON__', cert_json).replace('__ENGINE_JS__', engine)


def artifact(page: str) -> str:
    page = page.replace('<!--claude-only-->', '').replace('<!--/claude-only-->', '')
    return re.sub(r'[ \t]*/\*/?claude-only\*/\n', '', page)


def standalone(page: str) -> str:
    page = re.sub(r'<!--claude-only-->.*?<!--/claude-only-->\n?', '', page, flags=re.S)
    page = re.sub(r'[ \t]*/\*claude-only\*/.*?/\*/claude-only\*/\n', '', page, flags=re.S)
    cut = page.index('</style>') + len('</style>\n')
    head, body = page[:cut], page[cut:]
    favicon = 'data:image/svg+xml,' + urllib.parse.quote(FAVICON_SVG)
    return (
        '<!doctype html>\n<html lang="en">\n<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        f'<meta name="description" content="{DESCRIPTION}">\n'
        '<meta property="og:type" content="website">\n'
        '<meta property="og:title" content="Snaky 21-Move Cards">\n'
        f'<meta property="og:description" content="{DESCRIPTION}">\n'
        f'<link rel="icon" href="{favicon}">\n'
        '<style>\n'
        ':root { color-scheme: light; padding-top: env(safe-area-inset-top, 0px); '
        'padding-bottom: env(safe-area-inset-bottom, 0px); }\n'
        'body { margin: 0; }\n'
        '[hidden] { display: none !important; }\n'
        '</style>\n'
        + head + '</head>\n<body>\n' + body.rstrip('\n') + '\n</body>\n</html>\n'
    )


if __name__ == '__main__':
    here = Path(__file__).resolve().parent
    page = assemble(here)
    if '--artifact' in sys.argv[1:]:
        out, text = here / 'snaky-21-move-cards.html', artifact(page)
    else:
        out, text = here / 'index.html', standalone(page)
    out.write_text(text)
    print(out, len(text.encode()), 'bytes')
