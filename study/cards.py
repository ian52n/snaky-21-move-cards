"""Cards 0-310 of the 21-move Snaky certificate, one step at a time.

Run it from this folder:

    python3 cards.py           compute cards 0-310 and run the checks
    python3 cards.py 47        show every step of card 47, with drawings
    python3 cards.py --web     also write cards.js, the data that index.html draws

The names follow "Snaky in 21 Maker moves" (OpenAI, 2026):
a card is a triple (A, T, h): the required set A, the envelope T, the height h.
A cell is a pair (x, y). A set of cells is a Python set of pairs.
Only the Python standard library is used.
"""
import hashlib
import json
import sys
from pathlib import Path

CERTIFICATE = Path(__file__).resolve().parent.parent / 'certificate.txt'
CERTIFICATE_SHA256 = '3fa12d36a6d4dbb185e3f2808c8dfde13d85ee309afbca030d6ad17ae9fe3d04'
LAST_CARD = 310  # card 311 is the first line with parentheses (an inline expression)

SYMBOLS = '0123456789ABCDEFG'  # a coordinate digit means its position in this string
SNAKE = [(0, 0), (1, 0), (2, 0), (3, 0), (3, 1), (4, 1)]  # the target S, equation (1): s_0 ... s_5

# Table (5) of the paper, used only for printing.
R_TABLE = ['(x, y)', '(y, x)', '(-x, y)', '(y, -x)', '(x, -y)', '(-y, x)', '(-x, -y)', '(-y, -x)']


# ---------------------------------------------------------------- 1. Placements

def R(s, cell):
    """R_s from Section 3.1: negate x if s has the bit 2,
    negate y if s has the bit 4, and then swap x and y if s has the bit 1."""
    x, y = cell
    if s & 2:
        x = -x
    if s & 4:
        y = -y
    if s & 1:
        x, y = y, x
    return (x, y)


def place(cell, s, dx, dy):
    """The placement F(cell) = R_s(cell) + (dx, dy)."""
    x, y = R(s, cell)
    return (x + dx, y + dy)


# ---------------------------------------------------------------- 2. Reading a line

def point(word):
    """'14' -> (1, 4).  '7A' -> (7, 10)."""
    return (SYMBOLS.index(word[0]), SYMBOLS.index(word[1]))


def read_line(line):
    """'6 14 4:100 5:101' -> pivot (1, 4) and two children.

    A child word 'j:sUV' means card j, placed by R_s and then moved by the point UV.
    A bare child word 'j' means card j, not moved (s = 0, UV = 00)."""
    words = line.split()
    pivot = point(words[1])
    children = []
    for word in words[2:]:
        if ':' in word:
            j, code = word.split(':')
            s = int(code[0])
            dx, dy = point(code[1:])
        else:
            j, s, dx, dy = word, 0, 0, 0
        children.append({'word': word, 'card': int(j), 's': s, 'dx': dx, 'dy': dy})
    return pivot, children


# ---------------------------------------------------------------- 3. The cards

def base(j):
    """Lemma 4: base card j has A = S minus s_j, T = S, h = 1.
    We store s_j as its 'pivot': the cell Maker claims to complete the target."""
    return {'number': j, 'line': None, 'pivot': SNAKE[j], 'children': [],
            'A': set(SNAKE) - {SNAKE[j]}, 'T': set(SNAKE), 'h': 1}


def combine(number, line, cards):
    """Lemma 3, rule (2): place every child, then combine the children at the pivot."""
    pivot, children = read_line(line)
    for c in children:
        old = cards[c['card']]  # an earlier card, in its own coordinates
        c['A'] = {place(cell, c['s'], c['dx'], c['dy']) for cell in old['A']}
        c['T'] = {place(cell, c['s'], c['dx'], c['dy']) for cell in old['T']}
        c['pivot'] = place(old['pivot'], c['s'], c['dx'], c['dy'])  # only for drawing
        c['h'] = old['h']

    union_A = set()  # cells that some child requires
    for c in children:
        union_A = union_A | c['A']

    common_T = set(children[0]['T'])  # cells in every child's envelope
    for c in children[1:]:
        common_T = common_T & c['T']

    T = {pivot}
    for c in children:
        T = T | c['T']

    A = (union_A | common_T) - {pivot}
    h = 1 + max(c['h'] for c in children)
    assert A <= T
    return {'number': number, 'line': line, 'pivot': pivot, 'children': children,
            'common_T': common_T, 'A': A, 'T': T, 'h': h}


def all_cards():
    """Cards 0, 1, ..., LAST_CARD, in order. Each card uses only earlier cards."""
    data = CERTIFICATE.read_bytes()
    if hashlib.sha256(data).hexdigest() != CERTIFICATE_SHA256:
        sys.exit('certificate.txt is not the file from the paper')
    cards = [base(j) for j in range(6)]
    for line in data.decode('ascii').splitlines():
        number = int(line.split()[0])
        if number > LAST_CARD:
            break
        assert number == len(cards)  # the lines are cards 6, 7, 8, ... in order
        assert '(' not in line
        cards.append(combine(number, line, cards))
        assert all(c['card'] < number for c in cards[number]['children'])
    return cards


# ---------------------------------------------------------------- 4. Checks

def check(cards):
    # Table (5) of the paper, tried on the cell (1, 2).
    assert [R(s, (1, 2)) for s in range(8)] == [
        (1, 2), (2, 1), (-1, 2), (2, -1), (1, -2), (-2, 1), (-1, -2), (-2, -1)]
    # The two cards that Section 3.2 of the paper works out by hand.
    assert cards[6]['A'] == {(0, y) for y in range(5)}
    assert cards[6]['T'] == cards[6]['A'] | {(1, 3), (1, 4), (1, 5)}
    assert cards[6]['h'] == 2
    assert cards[7]['A'] == {(0, y) for y in range(1, 5)}
    assert cards[7]['T'] == {(0, y) for y in range(1, 6)} | {(1, y) for y in (0, 1, 2, 4, 5, 6)}
    assert cards[7]['h'] == 3


# ---------------------------------------------------------------- 5. Showing a card

def mark(cell, A, T, pivot=None):
    """P pivot, X required, o other envelope cell, . outside the envelope."""
    if cell == pivot:
        return 'P'
    if cell in A:
        return 'X'
    if cell in T:
        return 'o'
    return '.'


def box_of(cells):
    xs = [x for x, y in cells]
    ys = [y for x, y in cells]
    return min(xs), max(xs), min(ys), max(ys)


def picture(A, T, pivot, box=None):
    """A text drawing. y grows upward, as in the paper's figures."""
    x0, x1, y0, y1 = box or box_of(T | {pivot})
    rows = []
    for y in range(y1, y0 - 1, -1):
        rows.append(f'{y:>4} ' + ''.join(f'{mark((x, y), A, T, pivot):>3}' for x in range(x0, x1 + 1)))
    rows.append('     ' + ''.join(f'{x:>3}' for x in range(x0, x1 + 1)))
    return '\n'.join(rows)


def trace(c, old, cell):
    """One cell of the stored card old, followed into place by child c.
    'X  (3, 0) -> R_7 -> (0, -3) -> + (1, 4) -> (1, 1)': the letter is the cell's mark in old."""
    s, dx, dy = c['s'], c['dx'], c['dy']
    return (f"{mark(cell, old['A'], old['T'], old['pivot'])}  {cell} -> R_{s} -> {R(s, cell)}"
            f" -> + ({dx}, {dy}) -> {place(cell, s, dx, dy)}")


def show(cards, n):
    card = cards[n]
    print(f'Card {n}')
    if card['line'] is None:
        print(f'Base card (Lemma 4): T = S, A = S minus s_{n} = S minus {SNAKE[n]}, h = 1\n')
        print(picture(card['A'], card['T'], card['pivot']))
        return
    print('certificate line:', card['line'])
    print('pivot p =', card['pivot'])
    box = box_of(card['T'])
    for i, c in enumerate(card['children']):
        old = cards[c['card']]
        print(f"\n--- child {i + 1}: {c['word']} = card {c['card']}, s = {c['s']}, moved by ({c['dx']}, {c['dy']})")
        print(f"    (x, y) -> {R_TABLE[c['s']]} + ({c['dx']}, {c['dy']})\n")
        print(f"card {c['card']} as stored:")
        print(picture(old['A'], old['T'], old['pivot']))
        print(f"\nplaced in card {n}'s coordinates:")
        print(picture(c['A'], c['T'], c['pivot'], box))
        print('\ncell by cell:')
        for cell in sorted(old['T']):
            print('  ' + trace(c, old, cell))
    heights = ', '.join(str(c['h']) for c in card['children'])
    print(f"\n--- rule (2)\nh = 1 + max({heights}) = {card['h']}\n")
    print(f'card {n}:')
    print(picture(card['A'], card['T'], card['pivot']))


# ---------------------------------------------------------------- 6. Data for the web page

def write_web_data(cards, path):
    """cards.js holds everything index.html shows. The page draws it and computes nothing."""
    out = []
    for card in cards:
        entry = {'n': card['number'], 'line': card['line'], 'pivot': card['pivot'], 'h': card['h'],
                 'A': sorted(card['A']), 'T': sorted(card['T'])}
        if card['line'] is not None:
            entry['common_T'] = sorted(card['common_T'])
            entry['children'] = []
            for c in card['children']:
                old = cards[c['card']]
                entry['children'].append({
                    'word': c['word'], 'card': c['card'], 's': c['s'], 'h': c['h'],
                    'rule': f"(x, y) -> {R_TABLE[c['s']]} + ({c['dx']}, {c['dy']})",
                    'A': sorted(c['A']), 'T': sorted(c['T']), 'pivot': c['pivot'],
                    # one line per stored cell: where it starts, where it lands, and trace()'s text
                    'lines': [[cell, place(cell, c['s'], c['dx'], c['dy']), trace(c, old, cell)]
                              for cell in sorted(old['T'])]})
        out.append(entry)
    path.write_text('const CARDS = ' + json.dumps(out, separators=(',', ':')) + ';\n')


if __name__ == '__main__':
    cards = all_cards()
    check(cards)
    args = sys.argv[1:]
    if '--web' in args:
        write_web_data(cards, Path(__file__).resolve().parent / 'cards.js')
        print('wrote cards.js')
    numbers = [a for a in args if a.isdigit()]
    for a in numbers:
        show(cards, int(a))
    if not numbers:
        print(f'cards 0-{LAST_CARD} computed, all checks passed')
