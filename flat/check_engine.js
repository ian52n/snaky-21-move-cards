// Second, independent check of the flat certificate, using ../engine.js
// (the viewer's parser and combination rule) instead of check_flat.py.
// ../test_engine.js compares engine.js with the paper's own reconstruction,
// inline expressions included.
//
// Usage, from this folder:  node check_engine.js
//
// For every flat card n with label L (from labels.txt), and the paper's
// card or inline expression L:
//   - same pivot, same A, same T, same h;
//   - same children in the same order: a placed reference j:sUV stays j:sUV
//     (with j renumbered), and an inline child L.i becomes a bare reference
//     to the flat card labeled L.i;
//   - same strategy (Section 4 of the paper): for every Breaker reply class,
//     the first child in printed order whose envelope avoids the reply is the
//     same child. The flat list has 37,042 reply classes, like the paper's.
const fs = require('fs');
const path = require('path');
const E = require('../engine.js');

const read = (f) => fs.readFileSync(path.join(__dirname, f), 'ascii');
const paper = E.build(read('../certificate.txt'));
const flat = E.build(read('certificate-flat.txt'));
const labels = read('labels.txt').trim().split('\n').map((l) => l.split(' ')[1]);

let fails = 0;
const fail = (msg) => { if (fails++ < 10) console.log('FAIL', msg); };
const sameSet = (S, U) => S.size === U.size && [...S].every((k) => U.has(k));

// Label every node of the paper's certificate: 357, 357.2, 357.2.2, ...
const paperNode = new Map();
function labelTree(id, label) {
  paperNode.set(label, paper.nodes[id]);
  paper.nodes[id].children.forEach((ch, i) => {
    if (ch.kind === 'inline') labelTree(ch.node, label + '.' + (i + 1));
  });
}
paper.cardRoot.forEach((id, j) => labelTree(id, String(j)));

// Reply classes of a node: each envelope cell Maker does not yet own, plus one
// class for every cell outside the envelope. For each class, the index of the
// first child (in printed order) whose placed envelope avoids it.
function strategy(model, id) {
  const n = model.nodes[id];
  const kids = E.placedChildren(model, id, E.ID);
  const owned = new Set(n.A); owned.add(E.key(...n.pivot));
  const pick = new Map();
  for (const k of n.T) if (!owned.has(k)) pick.set(k, kids.findIndex((c) => !c.T.has(k)));
  pick.set('outside', 0); // every child envelope lies inside the parent's
  return pick;
}

if (flat.nodes.some((n) => n.kind === 'comb' && n.parent !== null)) fail('flat file has inline nodes');
if (labels.length !== flat.cardRoot.length) fail('labels.txt length ' + labels.length);
if (new Set(labels).size !== labels.length || paperNode.size !== labels.length) fail('label count');

let replyClasses = 0;
flat.cardRoot.forEach((fid, n) => {
  const f = flat.nodes[fid], p = paperNode.get(labels[n]);
  if (!p) return fail('no paper node for label ' + labels[n]);
  if (f.kind !== p.kind) return fail('kind of ' + labels[n]);
  if (!sameSet(f.A, p.A) || !sameSet(f.T, p.T) || f.h !== p.h) fail('A, T or h of ' + labels[n]);
  if (f.kind === 'base') return;
  if (f.pivot[0] !== p.pivot[0] || f.pivot[1] !== p.pivot[1]) fail('pivot of ' + labels[n]);
  if (f.children.length !== p.children.length) return fail('child count of ' + labels[n]);
  f.children.forEach((fc, i) => {
    const pc = p.children[i];
    const want = pc.kind === 'inline'
      ? { label: labels[n] + '.' + (i + 1), s: 0, dx: 0, dy: 0 }
      : { label: String(pc.card), s: pc.s, dx: pc.dx, dy: pc.dy };
    if (labels[fc.card] !== want.label || fc.s !== want.s || fc.dx !== want.dx || fc.dy !== want.dy) {
      fail(`child ${i + 1} of ${labels[n]}: flat ${fc.token} is not ${want.label}:${want.s}${want.dx}${want.dy}`);
    }
  });
  const fs_ = strategy(flat, fid), ps = strategy(paper, p.id);
  replyClasses += fs_.size;
  if (fs_.size !== ps.size) return fail('reply classes of ' + labels[n]);
  for (const [k, i] of fs_) {
    if (i < 0) fail('a reply blocks every child of ' + labels[n]);
    if (ps.get(k) !== i) fail('strategy differs at ' + labels[n]);
  }
});

const last = flat.nodes[flat.cardRoot[flat.cardRoot.length - 1]];
const checks = {
  'flat cards': flat.cardRoot.length === 1626,
  'combination nodes': flat.postorder.length === 1620 && paper.postorder.length === 1620,
  // Each of the paper's 898 inline expressions becomes one bare reference.
  'references': paper.references === 4089 && flat.references === 4089 + 898,
  'reply classes': replyClasses === 37042,
  'last card': last.A.size === 0 && last.T.size === 251 && last.h === 21,
};
for (const [k, v] of Object.entries(checks)) if (!v) fail(k);

console.log(fails ? `${fails} failure(s)` :
  `PASS  all 1,626 flat cards match the paper's cards and inline expressions ` +
  `(pivot, A, T, h, children, and the child chosen for each of ${replyClasses} reply classes)`);
process.exit(fails ? 1 : 0);
