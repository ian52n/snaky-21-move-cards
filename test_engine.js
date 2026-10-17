// Cross-check engine.js against the paper's route-21 reconstruction (primary.py --output).
// Usage: node test_engine.js certificate.txt reference.json
const fs = require('fs');
const E = require('./engine.js');

const [certPath, refPath] = process.argv.slice(2);
const text = fs.readFileSync(certPath, 'ascii');
const ref = JSON.parse(fs.readFileSync(refPath, 'utf8'));
const model = E.build(text);
const { nodes, cardRoot, postorder } = model;

const enc = (S) => [...S].map(E.unkey).sort((p, q) => p[0] - q[0] || p[1] - q[1]);
const same = (S, list) => JSON.stringify(enc(S)) === JSON.stringify(list);

let fails = 0;
const fail = (msg) => { if (fails++ < 10) console.log('FAIL', msg); };

// Every numbered card.
if (cardRoot.length !== ref.cards.length) fail('card count ' + cardRoot.length);
cardRoot.forEach((id, j) => {
  const n = nodes[id], r = ref.cards[j];
  if (!same(n.A, r.A)) fail('A of card ' + j);
  if (!same(n.T, r.T)) fail('T of card ' + j);
  if (n.h !== r.height) fail('h of card ' + j);
});
// Every combination node, inline ones included, in the same evaluation order.
if (postorder.length !== ref.postorder.length) fail('postorder length ' + postorder.length);
postorder.forEach((id, i) => {
  const n = nodes[id], r = ref.postorder[i];
  if (!same(n.A, r.A) || !same(n.T, r.T) || n.h !== r.height) fail('postorder node ' + i);
});

// Counts from the paper (Section 6 / primary.py).
const inline = nodes.filter((n) => n.kind === 'comb' && n.parent !== null).length;
let replies = 0;
for (const id of postorder) {
  const kids = E.placedChildren(model, id, E.ID);
  const n = nodes[id];
  const owned = new Set(n.A); owned.add(E.key(...n.pivot));
  for (const k of n.T) {
    if (owned.has(k)) continue;
    if (!kids.some((c) => !c.T.has(k))) fail('uncovered reply at node ' + id);
    replies++;
  }
  replies++; // the exterior class
  for (const c of kids) {
    for (const k of c.A) if (!owned.has(k)) fail('child requirement not owned at node ' + id);
    for (const k of c.T) if (!n.T.has(k)) fail('child envelope escapes parent at node ' + id);
  }
}
const checks = {
  lines: model.lineCount === 722, combination_nodes: postorder.length === 1620,
  inline_nodes: inline === 898, references: model.references === 4089, reply_classes: replies === 37042,
  final_card: nodes[cardRoot[727]].A.size === 0 && nodes[cardRoot[727]].T.size === 251 && nodes[cardRoot[727]].h === 21,
};
for (const [k, v] of Object.entries(checks)) if (!v) fail(k);

// Layout statistics.
const kidsCount = postorder.map((id) => nodes[id].children.length);
const maxDepth = Math.max(...nodes.map((n) => n.depth));
let maxW = 0, maxH = 0, maxT = 0, argW = -1;
for (const n of nodes) {
  const pts = enc(n.T);
  const xs = pts.map((p) => p[0]), ys = pts.map((p) => p[1]);
  const w = Math.max(...xs) - Math.min(...xs) + 1, h = Math.max(...ys) - Math.min(...ys) + 1;
  if (Math.max(w, h) > Math.max(maxW, maxH)) argW = n.id;
  maxW = Math.max(maxW, w); maxH = Math.max(maxH, h); maxT = Math.max(maxT, n.T.size);
}
let interOnlyNodes = 0, interOnlyCells = 0;
for (const id of postorder) {
  const n = nodes[id];
  const kids = E.placedChildren(model, id, E.ID);
  const union = new Set(); kids.forEach((c) => c.A.forEach((k) => union.add(k)));
  let c = 0; for (const k of n.A) if (!union.has(k)) c++;
  if (c) { interOnlyNodes++; interOnlyCells += c; }
}
const hist = {}; kidsCount.forEach((c) => { hist[c] = (hist[c] || 0) + 1; });
console.log(JSON.stringify({
  fails, checks, maxChildren: Math.max(...kidsCount), childrenHistogram: hist, maxInlineDepth: maxDepth,
  maxBBox: [maxW, maxH], maxBBoxNode: argW, maxEnvelope: maxT,
  reachableCards: model.reachable.size,
  unreachable: [...Array(728).keys()].filter((j) => !model.reachable.has(j)).length,
  nodesWithIntersectionOnlyRequired: interOnlyNodes, intersectionOnlyCells: interOnlyCells,
}, null, 1));
process.exit(fails ? 1 : 0);
