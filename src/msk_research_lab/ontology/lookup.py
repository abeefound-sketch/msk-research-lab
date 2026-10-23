"""Controlled Multilingual Ontology Loader and Lookup (G9 / R3-05).

Imports synthetic educational ontology seeds and executes deterministic
multilingual term lookups (e.g. GB21 -> Jianjing / Kiên tỉnh).
Aliases never imply physiological channel or nerve equivalence.
"""

from __future__ import annotations

import json
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional

from msk_research_lab.core.config import get_config
from msk_research_lab.core.db import get_db


def normalize_term(term: str) -> str:
    """Normalize Unicode string for case-folding and diacritic search."""
    normalized = unicodedata.normalize("NFKD", term.strip().lower())
    # Strip diacritics
    return "".join(c for c in normalized if not unicodedata.combining(c))


def load_ontology_seed(seed_path: Optional[Path] = None) -> Dict[str, Any]:
    """Import ontology concepts and aliases from config/ontology_seed.json."""
    cfg = get_config()
    path = seed_path or (cfg.root_dir / "config" / "ontology_seed.json")

    if not path.exists():
        raise FileNotFoundError(f"Ontology seed file not found at: {path}")

    data = json.loads(path.read_text(encoding="utf-8"))
    concepts = data.get("concepts", [])
    inserted_concepts = 0
    inserted_aliases = 0

    with get_db() as conn:
        for c in concepts:
            c_id = c["concept_id"]
            ns = c["namespace"]
            label = c["canonical_label"]
            rev_state = c.get("review_state", "UNREVIEWED")
            clin_status = c.get("clinical_status", "NOT_ASSESSED")
            def_sources = json.dumps(c.get("definition_source_ids", []))
            conflicts = c.get("source_conflict_notes")

            conn.execute(
                """
                INSERT INTO ontology_concepts (
                    concept_id, namespace, canonical_label, review_state,
                    clinical_status, definition_source_ids, source_conflict_notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(concept_id) DO UPDATE SET
                    namespace=excluded.namespace,
                    canonical_label=excluded.canonical_label,
                    review_state=excluded.review_state,
                    clinical_status=excluded.clinical_status,
                    definition_source_ids=excluded.definition_source_ids,
                    source_conflict_notes=excluded.source_conflict_notes;
                """,
                (c_id, ns, label, rev_state, clin_status, def_sources, conflicts)
            )
            inserted_concepts += 1

            for a in c.get("aliases", []):
                val = a["value"]
                norm = normalize_term(val)
                lang = a["language"]
                kind = a["kind"]
                a_rev = a.get("review_state", "UNREVIEWED")

                # Insert alias if not exists
                cur = conn.execute(
                    "SELECT alias_id FROM concept_aliases WHERE concept_id = ? AND value = ?;",
                    (c_id, val)
                )
                if not cur.fetchone():
                    conn.execute(
                        """
                        INSERT INTO concept_aliases (
                            concept_id, value, normalized_value, language, kind, review_state
                        ) VALUES (?, ?, ?, ?, ?, ?);
                        """,
                        (c_id, val, norm, lang, kind, a_rev)
                    )
                    inserted_aliases += 1

    return {
        "status": "SUCCESS",
        "concepts_loaded": inserted_concepts,
        "aliases_loaded": inserted_aliases,
        "is_synthetic": data.get("is_synthetic_illustrative_seed", False),
    }


def lookup_ontology(query: str) -> List[Dict[str, Any]]:
    """Lookup concept by canonical label or multilingual alias.

    Matches exact query first, then normalized Unicode.
    Guarantees:
      - Term aliases never assert anatomical identity or physiological channels.
      - Disclaimers attached to all results.
    """
    clean_q = query.strip()
    if not clean_q:
        return []

    norm_q = normalize_term(clean_q)

    with get_db() as conn:
        # Match canonical label
        cur = conn.execute(
            """
            SELECT c.*, 'CANONICAL' as match_type, c.canonical_label as matched_term
            FROM ontology_concepts c
            WHERE LOWER(c.canonical_label) = LOWER(?);
            """,
            (clean_q,)
        )
        rows = [dict(r) for r in cur.fetchall()]

        # Match exact alias
        if not rows:
            cur_al = conn.execute(
                """
                SELECT c.*, a.kind as match_type, a.value as matched_term, a.language
                FROM ontology_concepts c
                JOIN concept_aliases a ON c.concept_id = a.concept_id
                WHERE LOWER(a.value) = LOWER(?);
                """,
                (clean_q,)
            )
            rows = [dict(r) for r in cur_al.fetchall()]

        # Match normalized alias
        if not rows:
            cur_norm = conn.execute(
                """
                SELECT c.*, a.kind as match_type, a.value as matched_term, a.language
                FROM ontology_concepts c
                JOIN concept_aliases a ON c.concept_id = a.concept_id
                WHERE a.normalized_value = ?;
                """,
                (norm_q,)
            )
            rows = [dict(r) for r in cur_norm.fetchall()]

        results = []
        for r in rows:
            c_id = r["concept_id"]
            # Fetch all aliases for this concept
            cur_all_al = conn.execute(
                "SELECT value, language, kind, review_state FROM concept_aliases WHERE concept_id = ?;",
                (c_id,)
            )
            r["aliases"] = [dict(a) for a in cur_all_al.fetchall()]
            r["definition_source_ids"] = json.loads(r.get("definition_source_ids") or "[]")
            r["is_physiological_asserted"] = False
            r["disclaimer"] = "Term alias mapping only; does not imply physiological equivalence or clinical efficacy."
            results.append(r)

        return results
