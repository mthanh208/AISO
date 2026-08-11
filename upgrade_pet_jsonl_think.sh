#!/usr/bin/env bash
set -e

# upgrade_pet_jsonl_think.sh
# - Adds a robust JSONL parser and an advanced reasoning engine wrapper
# - Patches core/pet_brain.py to use the advanced reasoning engine
# - Do not paste this script into chat; run inside repo root to apply upgrades

INFO(){ echo -e "\033[96m$1\033[0m"; }
OK(){ echo -e "\033[92m$1\033[0m"; }
WARN(){ echo -e "\033[93m$1\033[0m"; }

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
CORE_DIR="$REPO_ROOT/smart_pet_ai/core"
DATA_HOT_JSONL="$REPO_ROOT/smart_pet_ai/data_hot/kien_thuc_jsonl"

mkdir -p "$CORE_DIR"

# ---------- 1) jsonl_parser.py ----------
cat > "$CORE_DIR/jsonl_parser.py" << 'PYEOF'
# -*- coding: utf-8 -*-
"""
jsonl_parser.py — Robust, tolerant JSONL ingestion
- Recursively extracts human-readable text from arbitrary JSON objects
- Detects common keys (text, content, body, message, prompt, thought, think, thoughts)
- Preserves path/key metadata and tags (e.g., think/thoughts)
- Returns list of {text, path, tags, raw}
"""
from collections import deque

COMMON_TEXT_KEYS = {
    'text', 'content', 'body', 'message', 'prompt', 'note', 'description',
    'summary', 'utterance', 'reply', 'answer', 'thought', 'thoughts', 'think',
}

THINK_KEYS = {'think', 'thoughts', 'internal_thoughts', 'chain_of_thoughts'}


def _is_text_like(v):
    return isinstance(v, str) and len(v.strip()) > 2


def extract_texts_from_json(obj, path=''):
    """Recursively find string fields and return list of dicts
    Each entry: {'text':..., 'path': 'a.b[3].c', 'tags': set(), 'raw': original_value}
    """
    out = []
    q = deque()
    q.append((obj, path))
    while q:
        cur, p = q.popleft()
        if isinstance(cur, dict):
            for k, v in cur.items():
                kp = f"{p}.{k}" if p else k
                if k.lower() in COMMON_TEXT_KEYS and _is_text_like(v):
                    tags = set()
                    if k.lower() in THINK_KEYS:
                        tags.add('think')
                    out.append({'text': v.strip(), 'path': kp, 'tags': tags, 'raw': v})
                elif _is_text_like(v) and (len(k) <= 20):
                    # names often give hint, treat as text
                    out.append({'text': v.strip(), 'path': kp, 'tags': set(), 'raw': v})
                else:
                    q.append((v, kp))
        elif isinstance(cur, list):
            for i, item in enumerate(cur):
                ip = f"{p}[{i}]" if p else f"[{i}]"
                if _is_text_like(item):
                    out.append({'text': item.strip(), 'path': ip, 'tags': set(), 'raw': item})
                else:
                    q.append((item, ip))
        else:
            # primitives
            pass
    return out


def parse_jsonl_file(path):
    """Parse a .jsonl file and return entries as list of dicts with text+meta
    Handles tolerant JSON parsing per-line. For each object, extract all text-like
    fields and emit an entry with combined text + metadata and tags.
    """
    import json
    out = []
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        for lineno, line in enumerate(f, start=1):
            s = line.strip()
            if not s:
                continue
            try:
                obj = json.loads(s)
            except Exception:
                # try to salvage by trimming trailing commas or wrapping
                try:
                    obj = json.loads(s.rstrip(',\n '))
                except Exception:
                    continue
            texts = extract_texts_from_json(obj)
            if not texts:
                # fallback: stringify top-level
                txt = str(obj)[:200]
                out.append({'text': txt, 'path': '', 'tags': set(), 'raw': obj, 'lineno': lineno})
            else:
                for t in texts:
                    entry = dict(t)
                    entry['lineno'] = lineno
                    # include top-level metadata hints
                    if isinstance(obj, dict):
                        if 'id' in obj:
                            entry['id'] = obj.get('id')
                        if 'title' in obj:
                            entry['title'] = obj.get('title')
                        if 'source' in obj:
                            entry['source'] = obj.get('source')
                    out.append(entry)
    return out
PYEOF
OK "wrote core/jsonl_parser.py"

# ---------- 2) reasoning_engine_adv.py ----------
cat > "$CORE_DIR/reasoning_engine_adv.py" << 'PYEOF'
# -*- coding: utf-8 -*-
"""
reasoning_engine_adv.py — Advanced reasoning wrapper
- Wraps existing ReasoningEngine and adds:
  • forward chaining (data-driven rule application)
  • backward chaining (goal-driven search)
  • probabilistic scoring / inference aggregation
  • simple online learning: learn_from_feedback adjusts document/edge weights
"""
import math, random

try:
    from core.reasoning_engine import ReasoningEngine as BaseReasoner
except Exception:
    BaseReasoner = None

class AdvancedReasoningEngine:
    def __init__(self, graph_engine, learner=None):
        self.graph = graph_engine
        self.base = BaseReasoner(graph_engine) if BaseReasoner else None

    # keep compatibility
    def causal_chain(self, start, end, max_depth=4):
        if self.base:
            return self.base.causal_chain(start, end, max_depth)
        return [], 'unknown'

    def analogical_reasoning(self, concept):
        if self.base:
            return self.base.analogical_reasoning(concept)
        return []

    def abductive_explain(self, observation):
        if self.base:
            return self.base.abductive_explain(observation)
        return []

    def multi_hop_reasoning(self, query_entities, depth=3):
        if self.base:
            return self.base.multi_hop_reasoning(query_entities, depth)
        return []

    # New: forward chaining using simple rule templates on graph edges
    def forward_chain(self, seeds, max_steps=6, threshold=0.5):
        # Seeds: list of concepts
        visited = set(seeds)
        frontier = list(seeds)
        inferred = {}
        steps = 0
        while frontier and steps < max_steps:
            next_frontier = []
            for n in frontier:
                if n not in self.graph.graph:
                    continue
                for nbr in self.graph.graph.successors(n):
                    edge = self.graph.graph[n][nbr]
                    weight = edge.get('causal_weight', edge.get('weight', 1))
                    score = weight / (1 + self.graph.graph.nodes[n].get('count', 0))
                    if score >= threshold and nbr not in visited:
                        inferred[nbr] = inferred.get(nbr, 0) + score
                        next_frontier.append(nbr)
                        visited.add(nbr)
            frontier = next_frontier
            steps += 1
        # sort by aggregated score
        return sorted(inferred.items(), key=lambda x: -x[1])

    # New: backward chaining goal-driven search (DFS with heuristic)
    def backward_chain(self, goal, hypotheses=None, max_depth=5):
        if hypotheses is None:
            hypotheses = list(self.graph.graph.nodes)
        best_paths = []
        def dfs(node, path, depth):
            if depth > max_depth:
                return
            if node == goal:
                best_paths.append(list(path))
                return
            for pred in self.graph.graph.predecessors(node):
                if pred in path:
                    continue
                path.append(pred)
                dfs(pred, path, depth+1)
                path.pop()
        dfs(goal, [goal], 0)
        best_paths.sort(key=lambda p: -len(p))
        return best_paths[:6]

    # New: score aggregation for multiple evidences
    def infer_score(self, candidate, evidences):
        # evidences: list of concepts
        score = 0.0
        for e in evidences:
            if e in self.graph.graph and candidate in self.graph.graph[e]:
                score += self.graph.graph[e][candidate].get('weight', 1)
            elif candidate in self.graph.graph and e in self.graph.graph[candidate]:
                score += 0.5 * self.graph.graph[candidate][e].get('weight', 1)
        # normalize
        return score / (1 + math.log(1 + len(evidences)))

    # Simple online learning hook: adjust node counts / edge weights
    def learn_from_feedback(self, doc_ids, sentiment, pet):
        # doc_ids: list of document ids that contributed; pet: UltimateCognitivePetPro instance
        if not doc_ids or not hasattr(pet, 'documents'):
            return
        for d in pet.documents:
            if d['id'] in doc_ids:
                # update weight using sentiment
                w = d.get('weight', 1.0)
                if sentiment > 0:
                    d['weight'] = min(5.0, w * (1 + 0.08 * sentiment))
                elif sentiment < 0:
                    d['weight'] = max(0.01, w * (1 + 0.06 * sentiment))
        # nudge graph edges: boost edges seen in docs positively or decay negatively
        for doc in pet.documents:
            if doc['id'] in doc_ids:
                text = doc.get('text','')
                ents = pet.graph_engine.extract_entities(text)
                for a in ents:
                    for b in ents:
                        if a==b: continue
                        if pet.graph_engine.graph.has_edge(a,b):
                            edge = pet.graph_engine.graph[a][b]
                            change = 0.2 if sentiment>0 else -0.15
                            edge['weight'] = max(0.01, edge.get('weight',1.0) * (1+change))
        pet.save_all()

    # Expose a unified reason() method used by orchestrator
    def reason(self, query_entities, evidences=None):
        evidences = evidences or []
        candidates = self.multi_hop_reasoning(query_entities, depth=3)
        scored = [(c, self.infer_score(c, evidences or query_entities)) for c in candidates]
        scored.sort(key=lambda x: -x[1])
        return [s[0] for s in scored]

PYEOF
OK "wrote core/reasoning_engine_adv.py"

# ---------- 3) Patch pet_brain.py to use AdvancedReasoningEngine and JSONL parser ----------
if [ ! -f "$CORE_DIR/pet_brain.py" ]; then
    WARN "core/pet_brain.py not found — aborting patch."
    exit 1
fi

cp "$CORE_DIR/pet_brain.py" "$CORE_DIR/pet_brain.py.bak"

# Replace import of ReasoningEngine with AdvancedReasoningEngine
python3 - << 'PY'
import io,sys
p='''$CORE_DIR/pet_brain.py'''
with open(p,'r',encoding='utf-8') as f:
    s=f.read()
if 'from core.reasoning_engine import ReasoningEngine' in s:
    s=s.replace('from core.reasoning_engine import ReasoningEngine', 'from core.reasoning_engine_adv import AdvancedReasoningEngine')
    # instantiate
    s=s.replace('self.reasoning = ReasoningEngine(self.graph_engine)', 'self.reasoning = AdvancedReasoningEngine(self.graph_engine)')
    with open(p,'w',encoding='utf-8') as f:
        f.write(s)
    print('patched import -> AdvancedReasoningEngine')
else:
    print('no import pattern found; manual review recommended')
PY

# Insert JSONL parsing into digest_hot_folder: create a small helper patch if not present
python3 - << 'PY'
from pathlib import Path
p=Path('$CORE_DIR/pet_brain.py')
s=p.read_text(encoding='utf-8')
if 'import jsonl_parser' not in s and 'core.jsonl_parser' not in s:
    # add import after other imports
    s=s.replace("from core.abstraction_engine import AbstractionEngine\nfrom core.narrative_identity import NarrativeIdentity",
                "from core.abstraction_engine import AbstractionEngine\nfrom core.narrative_identity import NarrativeIdentity\nfrom core.jsonl_parser import parse_jsonl_file")
    p.write_text(s,encoding='utf-8')
    print('inserted parse_jsonl_file import')
else:
    print('jsonl import likely present')

# Now patch digest_hot_folder to call parse_jsonl_file when encountering .jsonl
s=p.read_text(encoding='utf-8')
old='for fp in glob.glob(os.path.join(DATA_HOT_JSONL, "*.jsonl")):'
if old in s and 'parse_jsonl_file' not in s:
    new = old + "\n                try:\n                    entries = parse_jsonl_file(fp)\n                    for e in entries:\n                        text = e.get('text') or e.get('content') or ''\n                        if text:\n                            self._add_document(text, source=f\"hot_jsonl_parsed:{Path(fp).name}:L{e.get('lineno','?')}\")\n                            new_count += 1\n                    os.remove(fp)\n                except Exception as e:\n                    print(f'⚠️  Lỗi tiêu hóa JSONL {fp}: {e}')\n                continue\n"
    s=s.replace(old,new)
    p.write_text(s,encoding='utf-8')
    print('patched digest_hot_folder to use parse_jsonl_file')
else:
    print('digest_hot_folder patch not applied (pattern mismatch or already patched)')
PY

OK "patched pet_brain.py (backup at core/pet_brain.py.bak)"

# ---------- 4) Make script executable ----------
chmod +x "$CORE_DIR/jsonl_parser.py"
chmod +x "$CORE_DIR/reasoning_engine_adv.py"

OK "Upgrade script prepared. Run: bash upgrade_pet_jsonl_think.sh from repo root to apply locally."

echo ""
OK "DONE — created smart_pet_ai/core/jsonl_parser.py and core/reasoning_engine_adv.py and patched pet_brain.py (backup created)."

WARN "Note: This script edits files in-place; review core/pet_brain.py.bak if you need to revert."
