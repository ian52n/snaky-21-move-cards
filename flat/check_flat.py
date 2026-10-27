"""Check that certificate-flat.txt is the paper's certificate with each
parenthesized expression given its own number, and nothing else changed.

Run it from this folder:

    python3 check_flat.py                 run the checks
    python3 check_flat.py --tamper-test   damage the flat files in small ways
                                          and confirm that the checks notice

This file does not use flatten.py. It reads only ../certificate.txt,
certificate-flat.txt and labels.txt. Only the Python standard library is used.

The checks:

  0. certificate.txt is the paper's file (its SHA-256 is printed in Section 6.2).
  1. The flat files are well formed: lines 6, 7, 8, ... in order, no
     parentheses, every reference to a smaller number, one label per card.
  2. Round trip. Each card whose label has a dot (like 357.2) is used exactly
     once, by a bare reference, as the stated child of its parent. Putting
     each such card back in parentheses at that spot, and turning flat
     numbers back into the paper's numbers, gives certificate.txt byte for byte.
  3. The flat list is a certificate on its own: rule (2) of Lemma 3 applied
     line by line gives a last card with A empty, |T| = 251, T inside
     {0..16}^2 and height 21, as in Proposition 5.
  4. Same values: evaluating the paper's certificate the paper's way
     (parentheses evaluated in place, innermost first) gives the same
     A, T and h at all 1,626 cards and inline expressions as the flat list.

Check 2 is the one that proves equivalence. Check 4 confirms it by computing.
Check 3 does not depend on the other checks.
"""
import hashlib
import re
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
CERTIFICATE_SHA256 = '3fa12d36a6d4dbb185e3f2808c8dfde13d85ee309afbca030d6ad17ae9fe3d04'
SYMBOLS = '0123456789ABCDEFG'
SNAKE = [(0, 0), (1, 0), (2, 0), (3, 0), (3, 1), (4, 1)]

CHILD = re.compile(r'(0|[1-9][0-9]*)(:[0-7][0-9A-G][0-9A-G])?$')
POINT = re.compile(r'[0-9A-G][0-9A-G]$')
LABEL = re.compile(r'(0|[1-9][0-9]*)(\.[1-9][0-9]*)*$')


class Fail(Exception):
    pass


def need(condition, message):
    if not condition:
        raise Fail(message)


# ---------------------------------------------------------------- Rule (2)

def point(word):
    return (SYMBOLS.index(word[0]), SYMBOLS.index(word[1]))


def placed(word, card):
    """The child word 'k' or 'k:sUV', with card(k) = (A, T, h) of card k."""
    k, _, code = word.partition(':')
    A, T, h = card(int(k))
    if not code:
        return A, T, h
    s, dx, dy = int(code[0]), SYMBOLS.index(code[1]), SYMBOLS.index(code[2])

    def put(cells):
        out = set()
        for x, y in cells:
            if s & 2:
                x = -x
            if s & 4:
                y = -y
            if s & 1:
                x, y = y, x
            out.add((x + dx, y + dy))
        return frozenset(out)

    return put(A), put(T), h


def rule2(pivot, children):
    """Lemma 3: T = {p} u U T_i,  A = (U A_i u n T_i) - {p},  h = 1 + max h_i."""
    p = point(pivot)
    A = (frozenset().union(*(a for a, _, _ in children))
         | frozenset.intersection(*(t for _, t, _ in children))) - {p}
    T = frozenset({p}).union(*(t for _, t, _ in children))
    h = 1 + max(h for _, _, h in children)
    need(A <= T, 'A is not inside T')
    return A, T, h


BASES = [(frozenset(SNAKE) - {s}, frozenset(SNAKE), 1) for s in SNAKE]  # Lemma 4


# ---------------------------------------------------------------- Reading

def read_flat(text):
    """Flat certificate -> cards[n] = (pivot word, [child words]); bases are None."""
    need(text.endswith('\n') and '\r' not in text, 'flat file must end with a newline, no CR')
    need('(' not in text and ')' not in text, 'flat file contains parentheses')
    cards = [None] * 6
    for line in text[:-1].split('\n'):
        words = line.split(' ')
        need(len(words) >= 3, f'line too short: {line!r}')
        need(words[0] == str(len(cards)), f'expected line {len(cards)}, got {words[0]!r}')
        need(POINT.match(words[1]), f'bad pivot in line {words[0]}')
        for w in words[2:]:
            m = CHILD.match(w)
            need(m, f'bad child word {w!r} in line {words[0]}')
            need(int(m.group(1)) < len(cards), f'reference {w} is not backward in line {words[0]}')
        cards.append((words[1], words[2:]))
    return cards


def read_labels(text, count):
    labels = []
    for line in text.splitlines():
        n, _, lab = line.partition(' ')
        need(n == str(len(labels)), f'labels.txt: expected {len(labels)}, got {n!r}')
        need(LABEL.match(lab), f'labels.txt: bad label {lab!r}')
        labels.append(lab)
    need(len(labels) == count, f'labels.txt has {len(labels)} lines, flat list has {count} cards')
    need(len(set(labels)) == count, 'labels.txt repeats a label')
    need(labels[:6] == [str(j) for j in range(6)], 'bases must keep labels 0..5')
    return labels


# ---------------------------------------------------------------- The checks

def check_round_trip(original, cards, labels):
    number = {lab: n for n, lab in enumerate(labels)}
    uses = defaultdict(list)  # k -> [(n, i, word)]: card n uses k as its child i
    for n in range(6, len(cards)):
        for i, w in enumerate(cards[n][1], 1):
            uses[int(w.partition(':')[0])].append((n, i, w))
    for n, lab in enumerate(labels):
        if '.' in lab:
            parent, _, i = lab.rpartition('.')
            need(parent in number, f'card {n} ({lab}): no card is labeled {parent}')
            need(uses[n] == [(number[parent], int(i), str(n))],
                 f'card {n} ({lab}) must be used once, bare, as child {i} of {parent}; '
                 f'found {uses[n]}')

    def write(n):
        pivot, children = cards[n]
        out = [pivot]
        for w in children:
            k, colon, code = w.partition(':')
            k = int(k)
            out.append('(' + write(k) + ')' if '.' in labels[k] else labels[k] + colon + code)
        return ' '.join(out)

    rebuilt = ''.join(f'{labels[n]} {write(n)}\n'
                      for n in range(6, len(cards)) if '.' not in labels[n])
    if rebuilt.encode('ascii') != original:
        a, b = rebuilt.splitlines(), original.decode('ascii').splitlines()
        first = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
        need(False, f'round trip differs from certificate.txt at its line {first + 1}')


def evaluate_flat(cards):
    values = list(BASES)
    for n in range(6, len(cards)):
        pivot, children = cards[n]
        values.append(rule2(pivot, [placed(w, values.__getitem__) for w in children]))
    return values


def check_theorem(values):
    A, T, h = values[-1]
    need(A == frozenset(), f'last card has {len(A)} required cells, not 0')
    need(len(T) == 251, f'last card envelope has {len(T)} cells, not 251')
    need(all(0 <= x <= 16 and 0 <= y <= 16 for x, y in T), 'envelope leaves {0..16}^2')
    need(h == 21 and max(v[2] for v in values) == 21, 'height is not 21')


def evaluate_original(text):
    """The paper's own way: parentheses evaluated in place, in the line's frame.
    Returns label -> (A, T, h) for every numbered card and inline expression."""
    values = {str(j): v for j, v in enumerate(BASES)}
    for line in text.splitlines():
        words = line.replace('(', ' ( ').replace(')', ' ) ').split()
        it = iter(words[1:] + [')'])

        def expression(label):
            pivot = next(it)
            children = []
            for w in iter(lambda: next(it), ')'):
                if w == '(':
                    children.append(expression(f'{label}.{len(children) + 1}'))
                else:
                    children.append(placed(w, lambda k: values[str(k)]))
            values[label] = rule2(pivot, children)
            return values[label]

        expression(words[0])
        need(next(it, None) is None, f'unbalanced parentheses in line {words[0]}')
    return values


def check_same_values(original, flat_values, labels):
    paper = evaluate_original(original.decode('ascii'))
    need(set(paper) == set(labels),
         f'labels differ from the paper\'s cards and expressions: '
         f'{sorted(set(paper) ^ set(labels))[:5]}')
    for n, lab in enumerate(labels):
        need(paper[lab] == flat_values[n], f'card {n} ({lab}) differs from the paper\'s {lab}')


def run(original, flat_text, labels_text, quiet=False):
    """Run checks 0-4. Return {check name: None if passed, else the failure message}."""
    results = {}

    def attempt(name, f):
        try:
            out = f()
            results[name] = None
            return out
        except (Fail, KeyError, IndexError, ValueError, StopIteration) as e:
            results[name] = f'{type(e).__name__}: {e}' if not isinstance(e, Fail) else str(e)
            return None

    attempt('0 certificate.txt is the paper\'s file',
            lambda: need(hashlib.sha256(original).hexdigest() == CERTIFICATE_SHA256,
                         'SHA-256 does not match the paper'))
    parsed = attempt('1 flat files are well formed',
                     lambda: (lambda c: (c, read_labels(labels_text, len(c))))(read_flat(flat_text)))
    if parsed:
        cards, labels = parsed
        attempt('2 round trip gives certificate.txt', lambda: check_round_trip(original, cards, labels))
        computed = {}

        def theorem():
            computed['values'] = evaluate_flat(cards)
            check_theorem(computed['values'])

        attempt('3 flat list proves 21 moves alone', theorem)
        if 'values' in computed:
            attempt('4 same A, T, h at every node',
                    lambda: check_same_values(original, computed['values'], labels))
        else:
            results['4 same A, T, h at every node'] = 'skipped (flat values could not be computed)'
    else:
        for name in ('2 round trip gives certificate.txt', '3 flat list proves 21 moves alone',
                     '4 same A, T, h at every node'):
            results[name] = 'skipped (check 1 failed)'
    if not quiet:
        for name, err in results.items():
            print(('PASS  ' if err is None else 'FAIL  ') + name + ('' if err is None else f'\n      {err}'))
    return results


# ---------------------------------------------------------------- Tamper test

def tamper_test(original, flat_text, labels_text):
    """Each change below breaks the correspondence with the paper.
    The test passes if every change makes at least one check fail."""
    lines = flat_text.split('\n')
    lab = labels_text.split('\n')

    def edit(i, old, new, rows=None):
        rows = list(lines if rows is None else rows)
        assert old in rows[i], (i, old, rows[i])
        rows[i] = rows[i].replace(old, new, 1)
        return rows

    cases = [
        ('change a placement code in card 6',
         '\n'.join(edit(0, '4:100', '4:300')), labels_text),
        ('swap the two children of card 6',
         '\n'.join(edit(0, '4:100 5:101', '5:101 4:100')), labels_text),
        ('move the pivot of flat card 311 (the paper\'s 311.2)',
         '\n'.join(edit(305, '311 41', '311 42')), labels_text),
        ('point card 312 at card 310 instead of its inline child 311',
         '\n'.join(edit(306, '4:401 311', '4:401 310')), labels_text),
        ('give the inline child a placement: 311 -> 311:000 in card 312',
         '\n'.join(edit(306, '4:401 311', '4:401 311:000')), labels_text),
        ('delete the last card',
         '\n'.join(lines[:-2] + ['']), '\n'.join(lab[:-2] + [''])),
        ('swap the labels of flat cards 311 and 312',
         flat_text, '\n'.join(edit(312, '312 311', '312 311.2',
                                   edit(311, '311 311.2', '311 311', lab)))),
    ]
    all_caught = True
    for name, flat, labels in cases:
        results = run(original, flat, labels, quiet=True)
        failed = [k.split()[0] for k, v in results.items() if v is not None and not v.startswith('skipped')]
        caught = bool(failed)
        all_caught &= caught
        print(f'{"caught" if caught else "MISSED"}  {name}: checks failing = {", ".join(failed) or "none"}')
    return all_caught


def main():
    original = (HERE.parent / 'certificate.txt').read_bytes()
    flat_text = (HERE / 'certificate-flat.txt').read_text('ascii')
    labels_text = (HERE / 'labels.txt').read_text('ascii')
    if '--tamper-test' in sys.argv[1:]:
        ok = tamper_test(original, flat_text, labels_text)
        sys.exit(0 if ok else 1)
    results = run(original, flat_text, labels_text)
    print('certificate-flat.txt SHA-256:',
          hashlib.sha256(flat_text.encode('ascii')).hexdigest())
    sys.exit(0 if all(v is None for v in results.values()) else 1)


if __name__ == '__main__':
    main()
