/* Snaky 21-move certificate engine.
 * Parses the literal certificate (Appendix D of "Snaky in 21 Maker moves"),
 * applies placements, and evaluates the combination rule (Lemma 3, eq. (2))
 * at every numbered card and every inline (parenthesized) node.
 * Runs unchanged in the browser and in Node (for cross-checking).
 */
(function (root) {
  'use strict';

  const SYMBOLS = '0123456789ABCDEFG';
  const SNAKE = [[0, 0], [1, 0], [2, 0], [3, 0], [3, 1], [4, 1]];

  // Integer keys for cells: coordinates stay well inside (-512, 512).
  const OFF = 512, K = 1024;
  const key = (x, y) => (x + OFF) * K + (y + OFF);
  const unkey = (k) => [Math.floor(k / K) - OFF, (k % K) - OFF];

  // Signed coordinate permutation R_s from Section 3.1:
  // negate x if bit 2, negate y if bit 4, then swap if bit 1.
  function rot(s, x, y) {
    if (s & 2) x = -x;
    if (s & 4) y = -y;
    if (s & 1) { const t = x; x = y; y = t; }
    return [x, y];
  }
  const ID = Object.freeze({ a: 1, b: 0, c: 0, d: 1, tx: 0, ty: 0 });
  function placement(s, dx, dy) {
    const [a, c] = rot(s, 1, 0);
    const [b, d] = rot(s, 0, 1);
    return { a, b, c, d, tx: dx, ty: dy };
  }
  function apply(P, x, y) {
    return [P.a * x + P.b * y + P.tx, P.c * x + P.d * y + P.ty];
  }
  // (F o G)(v) = F(G(v))
  function compose(F, G) {
    return {
      a: F.a * G.a + F.b * G.c, b: F.a * G.b + F.b * G.d,
      c: F.c * G.a + F.d * G.c, d: F.c * G.b + F.d * G.d,
      tx: F.a * G.tx + F.b * G.ty + F.tx,
      ty: F.c * G.tx + F.d * G.ty + F.ty,
    };
  }
  function isIdentity(P) {
    return P.a === 1 && P.b === 0 && P.c === 0 && P.d === 1 && P.tx === 0 && P.ty === 0;
  }
  function mapSet(P, S) {
    if (isIdentity(P)) return S;
    const out = new Set();
    for (const k of S) { const [x, y] = unkey(k); const [u, v] = apply(P, x, y); out.add(key(u, v)); }
    return out;
  }
  function mapPoint(P, pt) { return pt ? apply(P, pt[0], pt[1]) : null; }

  function point(word) {
    if (word.length !== 2) throw new Error('invalid point: ' + word);
    const x = SYMBOLS.indexOf(word[0]), y = SYMBOLS.indexOf(word[1]);
    if (x < 0 || y < 0) throw new Error('invalid point: ' + word);
    return [x, y];
  }

  // Plain-language description of R_s, as in table (5).
  const R_TEXT = ['(x, y)', '(y, x)', '(−x, y)', '(y, −x)', '(x, −y)', '(−y, x)', '(−x, −y)', '(−y, −x)'];
  function describeRef(s, dx, dy) {
    const r = R_TEXT[s];
    if (s === 0 && dx === 0 && dy === 0) return 'identity placement';
    let txt = '(x, y) ↦ ' + r;
    if (dx || dy) txt = '(x, y) ↦ ' + r + ' + (' + dx + ', ' + dy + ')';
    return txt;
  }

  function build(text) {
    const nodes = [];      // every node: 6 bases, 722 line roots, 898 inline nodes
    const cardRoot = [];   // card index -> node id
    const postorder = [];  // combination nodes in evaluation order (inner first)
    let references = 0;

    // Bases (Lemma 4): A = S \ {s_j}, T = S, h = 1.
    SNAKE.forEach((p, j) => {
      const T = new Set(SNAKE.map(([x, y]) => key(x, y)));
      const A = new Set(T); A.delete(key(p[0], p[1]));
      const node = {
        id: nodes.length, kind: 'base', card: j, line: j, parent: null, depth: 0,
        pivot: null, missing: p.slice(), children: [], A, T, I: null, h: 1,
        text: 'base ' + j,
      };
      nodes.push(node); cardRoot.push(node.id);
    });

    // Placed copy of a child, in the coordinate frame of the line that contains it.
    function childSets(ch) {
      if (ch.kind === 'ref') {
        const n = nodes[cardRoot[ch.card]];
        return { A: mapSet(ch.P, n.A), T: mapSet(ch.P, n.T), h: n.h };
      }
      const n = nodes[ch.node];
      return { A: n.A, T: n.T, h: n.h };
    }

    const lines = text.replace(/\r/g, '').split('\n').filter((l) => l.trim().length);
    for (const line of lines) {
      const tokens = line.replace(/\(/g, ' ( ').replace(/\)/g, ' ) ').trim().split(/\s+/);
      const j = cardRoot.length;
      if (tokens[0] !== String(j)) throw new Error('expected card ' + j + ', got ' + tokens[0]);
      let pos = 1;

      function expression(parentId, depth, nested) {
        if (pos >= tokens.length) throw new Error('missing pivot in card ' + j);
        const pivot = point(tokens[pos++]);
        const node = {
          id: nodes.length, kind: 'comb', card: nested ? null : j, line: j,
          parent: parentId, depth, pivot, missing: null, children: [],
          A: null, T: null, I: null, h: 0, text: '',
        };
        nodes.push(node);
        const startTok = pos - 2; // index of '(' (nested) or of the card number
        while (pos < tokens.length && tokens[pos] !== ')') {
          if (tokens[pos] === '(') {
            pos++;
            const child = expression(node.id, depth + 1, true);
            node.children.push({ kind: 'inline', node: child.id });
          } else {
            const tok = tokens[pos++];
            const m = /^(0|[1-9][0-9]*)(?::([0-7])([0-9A-G])([0-9A-G]))?$/.exec(tok);
            if (!m) throw new Error('invalid reference ' + tok + ' in card ' + j);
            const card = +m[1];
            if (card >= j) throw new Error('reference not backward in card ' + j);
            const s = m[2] ? +m[2] : 0;
            const dx = m[3] ? SYMBOLS.indexOf(m[3]) : 0;
            const dy = m[4] ? SYMBOLS.indexOf(m[4]) : 0;
            node.children.push({ kind: 'ref', card, s, dx, dy, token: tok, P: placement(s, dx, dy) });
            references++;
          }
        }
        if (nested) {
          if (tokens[pos] !== ')') throw new Error('unclosed inline expression in card ' + j);
          pos++;
        } else if (pos !== tokens.length) {
          throw new Error('unmatched closing parenthesis in card ' + j);
        }
        if (!node.children.length) throw new Error('empty child list in card ' + j);
        node.text = tokens.slice(nested ? startTok + 1 : 0, pos).join(' ')
          .replace(/\( /g, '(').replace(/ \)/g, ')');
        if (nested) node.text = '(' + node.text;

        // Combination rule (2).
        const kids = node.children.map(childSets);
        const pk = key(pivot[0], pivot[1]);
        const union = new Set();
        for (const c of kids) for (const k of c.A) union.add(k);
        let inter = null;
        for (const c of kids) {
          if (inter === null) inter = new Set(c.T);
          else for (const k of inter) if (!c.T.has(k)) inter.delete(k);
        }
        const A = new Set(union); for (const k of inter) A.add(k); A.delete(pk);
        const T = new Set([pk]); for (const c of kids) for (const k of c.T) T.add(k);
        node.A = A; node.T = T; node.I = inter;
        node.h = 1 + Math.max(...kids.map((c) => c.h));
        for (const k of A) if (!T.has(k)) throw new Error('A not inside T at card ' + j);
        postorder.push(node.id);
        return node;
      }

      const rootNode = expression(null, 0, false);
      cardRoot.push(rootNode.id);
    }

    // Reverse references and reachability from the final card.
    const usedBy = cardRoot.map(() => new Set());
    for (const n of nodes) for (const ch of n.children) if (ch.kind === 'ref') usedBy[ch.card].add(n.line);
    const reachable = new Set();
    const stack = [cardRoot.length - 1];
    while (stack.length) {
      const c = stack.pop();
      if (reachable.has(c)) continue;
      reachable.add(c);
      const visit = (id) => {
        for (const ch of nodes[id].children) {
          if (ch.kind === 'ref') stack.push(ch.card); else visit(ch.node);
        }
      };
      visit(cardRoot[c]);
    }

    return {
      nodes, cardRoot, postorder, references, usedBy, reachable,
      lineCount: lines.length,
    };
  }

  // Children of a node, placed in the node's own frame, then mapped by F.
  function placedChildren(model, nodeId, F) {
    const n = model.nodes[nodeId];
    return n.children.map((ch, idx) => {
      let target, P;
      if (ch.kind === 'ref') { target = model.nodes[model.cardRoot[ch.card]]; P = compose(F, ch.P); }
      else { target = model.nodes[ch.node]; P = F; }
      return {
        idx, ch, target, P,
        A: mapSet(P, target.A), T: mapSet(P, target.T), h: target.h,
        pivot: mapPoint(P, target.pivot), missing: mapPoint(P, target.missing),
      };
    });
  }

  const api = {
    SYMBOLS, SNAKE, key, unkey, rot, placement, apply, compose, isIdentity,
    mapSet, mapPoint, describeRef, build, placedChildren, ID, R_TEXT,
  };
  root.SnakyEngine = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
