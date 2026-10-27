"""Flatten the 21-move certificate: give every parenthesized expression its
own card number, so that no line contains parentheses.

Run it from this folder:

    python3 flatten.py

It reads ../certificate.txt and writes two files:

    certificate-flat.txt   the flat certificate, in the paper's grammar
    labels.txt             one line "n label" for every flat card n

A label names a card by its place in the paper's certificate:
    357        the paper's card 357
    357.2      the 2nd child of card 357, written in parentheses there
    357.2.2    the 2nd child of 357.2, and so on

Numbering: the cards are numbered in the order the paper evaluates them,
innermost expression first. So the inline children of a line come just
before the line itself, and every reference points to a smaller number.
A parenthesized child becomes a bare reference (identity placement), because
coordinates inside parentheses are already in the line's own frame
(Section 3.1 of the paper). Every other child word keeps its placement code.

Only the Python standard library is used. check_flat.py checks the output
without using this file.
"""
import hashlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
CERTIFICATE = HERE.parent / 'certificate.txt'
CERTIFICATE_SHA256 = '3fa12d36a6d4dbb185e3f2808c8dfde13d85ee309afbca030d6ad17ae9fe3d04'


def flatten(text):
    """Return (flat lines, labels), where labels[n] is the label of flat card n."""
    labels = [str(j) for j in range(6)]  # the six bases keep 0..5
    new_number = {str(j): j for j in range(6)}  # paper card number -> flat number
    flat = []

    for line in text.splitlines():
        words = line.replace('(', ' ( ').replace(')', ' ) ').split()
        pos = 1

        def expression(label):
            """Read 'pivot child child ...' up to ')' or the end of the line.
            Write out the inline children first, then this expression."""
            nonlocal pos
            pivot = words[pos]
            pos += 1
            children = []
            while pos < len(words) and words[pos] != ')':
                if words[pos] == '(':
                    pos += 1
                    child = expression(f'{label}.{len(children) + 1}')
                    assert words[pos] == ')'
                    pos += 1
                    children.append(str(child))  # bare reference: identity placement
                else:
                    card, colon, code = words[pos].partition(':')
                    children.append(f'{new_number[card]}{colon}{code}')
                    pos += 1
            n = len(labels)
            flat.append(f'{n} {pivot} ' + ' '.join(children))
            labels.append(label)
            return n

        card = words[0]
        new_number[card] = expression(card)
        assert pos == len(words), line
    return flat, labels


def main():
    data = CERTIFICATE.read_bytes()
    if hashlib.sha256(data).hexdigest() != CERTIFICATE_SHA256:
        raise SystemExit('certificate.txt is not the file from the paper')
    flat, labels = flatten(data.decode('ascii'))
    (HERE / 'certificate-flat.txt').write_text('\n'.join(flat) + '\n')
    (HERE / 'labels.txt').write_text(''.join(f'{n} {lab}\n' for n, lab in enumerate(labels)))
    print(f'wrote {len(flat)} flat lines (cards 6..{len(labels) - 1}) and {len(labels)} labels')


if __name__ == '__main__':
    main()
