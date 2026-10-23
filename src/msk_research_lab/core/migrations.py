"""Transactional migration runner for MSK Research Lab OS SQLite database."""

import datetime
from pathlib import Path
from typing import List, Tuple, Optional
from msk_research_lab.core.db import get_db

MIGRATIONS: List[Tuple[int, str, str]] = [
    (
        1,
        "0001_initial_r0_baseline",
        """
        -- Audit Events Ledger
        CREATE TABLE IF NOT EXISTS audit_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            actor TEXT NOT NULL,
            payload_json TEXT NOT NULL DEFAULT '{}',
            status TEXT NOT NULL DEFAULT 'LOGGED',
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
        );

        -- System State Key-Value Table
        CREATE TABLE IF NOT EXISTS system_state (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
        );

        -- Repositories (Metadata & Inspection Registry)
        CREATE TABLE IF NOT EXISTS repositories (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            upstream_url TEXT NOT NULL,
            license TEXT NOT NULL DEFAULT 'UNKNOWN',
            status TEXT NOT NULL DEFAULT 'REGISTERED_UNINSPECTED',
            target_kind TEXT NOT NULL DEFAULT 'GENERAL_RESEARCH',
            pinned_commit_sha TEXT,
            catalog_metadata_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
            updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
        );

        -- Repository Run Profiles (Explicit, disabled-by-default execution profiles)
        CREATE TABLE IF NOT EXISTS repo_run_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            sandbox_type TEXT NOT NULL DEFAULT 'SUBPROCESS_ISOLATED',
            max_memory_mb INTEGER NOT NULL DEFAULT 512,
            max_cpu_percent INTEGER NOT NULL DEFAULT 50,
            timeout_seconds INTEGER NOT NULL DEFAULT 300,
            allowed_ports_json TEXT NOT NULL DEFAULT '[]',
            status TEXT NOT NULL DEFAULT 'DISABLED',
            is_approved INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
        );

        -- Explicit Human Approvals
        CREATE TABLE IF NOT EXISTS execution_approvals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repo_id TEXT NOT NULL,
            profile_id TEXT NOT NULL,
            commit_sha TEXT NOT NULL,
            approved_by TEXT NOT NULL,
            approved_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
            approval_token TEXT UNIQUE NOT NULL,
            status TEXT NOT NULL DEFAULT 'ACTIVE',
            FOREIGN KEY(repo_id) REFERENCES repositories(id) ON DELETE RESTRICT
        );

        CREATE INDEX IF NOT EXISTS idx_audit_events_created ON audit_events(created_at);
        CREATE INDEX IF NOT EXISTS idx_repos_status ON repositories(status);
        CREATE INDEX IF NOT EXISTS idx_approvals_repo ON execution_approvals(repo_id);
        """
    ),
    (
        2,
        "0002_r1_repo_inspections_and_benchmarks",
        """
        -- R1 Static Inspection Results
        CREATE TABLE IF NOT EXISTS repo_inspections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repo_id TEXT NOT NULL,
            inspected_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
            commit_sha TEXT,
            code_license TEXT,
            asset_license TEXT,
            data_license TEXT,
            dependencies_json TEXT NOT NULL DEFAULT '[]',
            risk_flags_json TEXT NOT NULL DEFAULT '[]',
            summary TEXT,
            FOREIGN KEY(repo_id) REFERENCES repositories(id) ON DELETE CASCADE
        );

        -- R1 Surface Registration v1 Benchmark Runs
        CREATE TABLE IF NOT EXISTS benchmark_runs (
            id TEXT PRIMARY KEY,
            benchmark_suite TEXT NOT NULL,
            suite_version TEXT NOT NULL DEFAULT 'v1.0',
            executed_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
            total_cases INTEGER NOT NULL DEFAULT 0,
            passed_cases INTEGER NOT NULL DEFAULT 0,
            failed_cases INTEGER NOT NULL DEFAULT 0,
            unsupported_cases INTEGER NOT NULL DEFAULT 0,
            overall_status TEXT NOT NULL DEFAULT 'RUNNING',
            manifest_sha256 TEXT,
            hardware_fingerprint_json TEXT NOT NULL DEFAULT '{}'
        );

        -- R1 Benchmark Individual Test Cases
        CREATE TABLE IF NOT EXISTS benchmark_cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            case_id TEXT NOT NULL,
            method_id TEXT NOT NULL,
            status TEXT NOT NULL,
            comparability TEXT NOT NULL DEFAULT 'COMPARABLE',
            error_metric REAL,
            unit TEXT,
            details_json TEXT NOT NULL DEFAULT '{}',
            FOREIGN KEY(run_id) REFERENCES benchmark_runs(id) ON DELETE CASCADE
        );

        -- R1 Evidence Bundles
        CREATE TABLE IF NOT EXISTS evidence_bundles (
            id TEXT PRIMARY KEY,
            release_id TEXT NOT NULL,
            bundle_path TEXT NOT NULL,
            artifact_count INTEGER NOT NULL DEFAULT 0,
            manifest_sha256 TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
            is_valid INTEGER NOT NULL DEFAULT 1
        );

        CREATE INDEX IF NOT EXISTS idx_repo_inspections_repo ON repo_inspections(repo_id);
        CREATE INDEX IF NOT EXISTS idx_benchmark_cases_run ON benchmark_cases(run_id);
        CREATE INDEX IF NOT EXISTS idx_evidence_bundles_release ON evidence_bundles(release_id);
        """
    ),
    (
        3,
        "0003_r2_document_library_and_notes",
        """
        -- R2 Documents Registry
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            sha256 TEXT UNIQUE NOT NULL,
            original_filename TEXT NOT NULL,
            file_type TEXT NOT NULL,
            byte_size INTEGER NOT NULL,
            page_or_section_count INTEGER NOT NULL DEFAULT 0,
            rights_status TEXT NOT NULL DEFAULT 'RESTRICTED_LOCAL',
            storage_path TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
        );

        -- R2 Document Locations (Exact, resolvable locators)
        CREATE TABLE IF NOT EXISTS document_locations (
            id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL,
            location_type TEXT NOT NULL,
            page_number INTEGER,
            spine_href TEXT,
            block_index INTEGER,
            heading_path TEXT,
            normalized_region TEXT,
            text_content TEXT,
            has_images INTEGER NOT NULL DEFAULT 0,
            ocr_status TEXT NOT NULL DEFAULT 'NATIVE_TEXT',
            FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
        );

        -- R2 FTS5 Full Text Search Index
        CREATE VIRTUAL TABLE IF NOT EXISTS fts_document_locations USING fts5(
            document_id UNINDEXED,
            location_id UNINDEXED,
            heading,
            body,
            tokenize = 'unicode61'
        );

        -- R2 Research Notes
        CREATE TABLE IF NOT EXISTS research_notes (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            content_markdown TEXT NOT NULL,
            author TEXT NOT NULL DEFAULT 'RESEARCHER',
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
            updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
        );

        -- R2 Research Citations (Linked to documents or git commits)
        CREATE TABLE IF NOT EXISTS research_citations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            note_id TEXT NOT NULL,
            target_kind TEXT NOT NULL,
            document_id TEXT,
            location_id TEXT,
            git_repo_id TEXT,
            git_commit_sha TEXT,
            excerpt TEXT,
            comment TEXT,
            FOREIGN KEY(note_id) REFERENCES research_notes(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_doc_locations_doc ON document_locations(document_id);
        CREATE INDEX IF NOT EXISTS idx_doc_locations_page ON document_locations(page_number);
        CREATE INDEX IF NOT EXISTS idx_citations_note ON research_citations(note_id);
        """
    ),
    (
        4,
        "0004_r3_tri_ledger_provenance_ontology_graph_publication",
        """
        -- R3 G8: Sources Provenance Registry
        CREATE TABLE IF NOT EXISTS sources (
            source_id TEXT PRIMARY KEY,
            kind TEXT NOT NULL,
            canonical_uri TEXT NOT NULL,
            title TEXT NOT NULL,
            author TEXT,
            translator TEXT,
            publisher TEXT,
            language TEXT,
            edition_id TEXT,
            acquisition_time TEXT NOT NULL,
            source_version TEXT,
            git_commit_sha TEXT,
            sha256 TEXT,
            rights_status TEXT NOT NULL DEFAULT 'REVIEW_REQUIRED',
            declared_license TEXT,
            asset_license TEXT,
            origin_id TEXT,
            independence_group_id TEXT,
            authenticity_state TEXT NOT NULL DEFAULT 'UNVERIFIED',
            notes TEXT,
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
        );

        -- R3 G8: Source Locations (Specific extract locators)
        CREATE TABLE IF NOT EXISTS source_locations (
            locator_id TEXT PRIMARY KEY,
            source_id TEXT NOT NULL,
            locator_type TEXT NOT NULL,
            locator_json TEXT NOT NULL,
            preview_text_hash TEXT,
            extract_method TEXT NOT NULL DEFAULT 'MANUAL',
            visibility_status TEXT NOT NULL DEFAULT 'ALLOWED',
            source_resolver_version TEXT NOT NULL DEFAULT '1.0',
            FOREIGN KEY(source_id) REFERENCES sources(source_id) ON DELETE RESTRICT
        );

        -- R3 G8: Source Relations (Lineage, derivation, translations)
        CREATE TABLE IF NOT EXISTS source_relations (
            relation_id TEXT PRIMARY KEY,
            source_a_id TEXT NOT NULL,
            source_b_id TEXT NOT NULL,
            kind TEXT NOT NULL,
            rationale TEXT,
            review_state TEXT NOT NULL DEFAULT 'UNREVIEWED',
            FOREIGN KEY(source_a_id) REFERENCES sources(source_id) ON DELETE CASCADE,
            FOREIGN KEY(source_b_id) REFERENCES sources(source_id) ON DELETE CASCADE
        );

        -- R3 G7: Claims Ledger
        CREATE TABLE IF NOT EXISTS claims (
            claim_id TEXT PRIMARY KEY,
            statement TEXT NOT NULL,
            knowledge_namespace TEXT NOT NULL,
            claim_kind TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'DRAFT',
            author_kind TEXT NOT NULL DEFAULT 'RESEARCHER',
            review_state TEXT NOT NULL DEFAULT 'UNREVIEWED',
            clinical_evidence_assessment TEXT,
            supersedes_claim_id TEXT,
            reviewer_id TEXT,
            review_rationale TEXT,
            uncertainty_text TEXT,
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
            revised_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
            FOREIGN KEY(supersedes_claim_id) REFERENCES claims(claim_id)
        );

        -- R3 G7: Evidence Ledger
        CREATE TABLE IF NOT EXISTS evidence (
            evidence_id TEXT PRIMARY KEY,
            source_id TEXT NOT NULL,
            locator_id TEXT NOT NULL,
            source_kind TEXT NOT NULL,
            excerpt_or_observation TEXT NOT NULL,
            extraction_method TEXT NOT NULL DEFAULT 'MANUAL',
            review_state TEXT NOT NULL DEFAULT 'UNREVIEWED',
            provenance_hash TEXT NOT NULL,
            original_language TEXT,
            edition_id TEXT,
            author_kind TEXT NOT NULL DEFAULT 'RESEARCHER',
            independence_group_id TEXT,
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
            FOREIGN KEY(source_id) REFERENCES sources(source_id),
            FOREIGN KEY(locator_id) REFERENCES source_locations(locator_id)
        );

        -- R3 G7: Claim-Evidence Junction
        CREATE TABLE IF NOT EXISTS claim_evidence_links (
            claim_id TEXT NOT NULL,
            evidence_id TEXT NOT NULL,
            relation TEXT NOT NULL,
            reviewer_rationale TEXT,
            PRIMARY KEY(claim_id, evidence_id, relation),
            FOREIGN KEY(claim_id) REFERENCES claims(claim_id) ON DELETE CASCADE,
            FOREIGN KEY(evidence_id) REFERENCES evidence(evidence_id) ON DELETE RESTRICT
        );

        -- R3 G7: Contradictions & Disagreements Ledger
        CREATE TABLE IF NOT EXISTS contradictions (
            contradiction_id TEXT PRIMARY KEY,
            claim_a_id TEXT NOT NULL,
            claim_b_id TEXT,
            counter_evidence_id TEXT,
            conflict_kind TEXT NOT NULL,
            state TEXT NOT NULL DEFAULT 'OPEN',
            rationale TEXT,
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
            updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
            FOREIGN KEY(claim_a_id) REFERENCES claims(claim_id),
            FOREIGN KEY(claim_b_id) REFERENCES claims(claim_id),
            FOREIGN KEY(counter_evidence_id) REFERENCES evidence(evidence_id)
        );

        -- R3 G7: Claim Revision Audit Trail
        CREATE TABLE IF NOT EXISTS claim_revision_events (
            event_id TEXT PRIMARY KEY,
            prior_claim_id TEXT NOT NULL,
            next_claim_id TEXT NOT NULL,
            reason TEXT NOT NULL,
            author_kind TEXT NOT NULL DEFAULT 'RESEARCHER',
            content_hash TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
            FOREIGN KEY(prior_claim_id) REFERENCES claims(claim_id),
            FOREIGN KEY(next_claim_id) REFERENCES claims(claim_id)
        );

        -- R3 G7: Human Review Audit Log
        CREATE TABLE IF NOT EXISTS review_events (
            review_id TEXT PRIMARY KEY,
            record_type TEXT NOT NULL,
            record_id TEXT NOT NULL,
            previous_state TEXT NOT NULL,
            next_state TEXT NOT NULL,
            reviewer_id TEXT NOT NULL,
            justification TEXT NOT NULL,
            evidence_snapshot_hash TEXT,
            timestamp TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
        );

        -- R3 G8: Parallel Source Comparisons
        CREATE TABLE IF NOT EXISTS comparisons (
            comparison_id TEXT PRIMARY KEY,
            source_a_id TEXT NOT NULL,
            locator_a_id TEXT,
            source_b_id TEXT NOT NULL,
            locator_b_id TEXT,
            classification TEXT NOT NULL,
            operator_notes TEXT,
            geometric_comparability_state TEXT NOT NULL DEFAULT 'UNREGISTERED; NUMERIC DISTANCE NOT MEANINGFUL',
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
            FOREIGN KEY(source_a_id) REFERENCES sources(source_id),
            FOREIGN KEY(source_b_id) REFERENCES sources(source_id)
        );

        -- R3 G9: Controlled Multilingual Ontology
        CREATE TABLE IF NOT EXISTS ontology_concepts (
            concept_id TEXT PRIMARY KEY,
            namespace TEXT NOT NULL,
            canonical_label TEXT NOT NULL,
            review_state TEXT NOT NULL DEFAULT 'UNREVIEWED',
            clinical_status TEXT NOT NULL DEFAULT 'NOT_ASSESSED',
            definition_source_ids TEXT,
            source_conflict_notes TEXT,
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
        );

        CREATE TABLE IF NOT EXISTS concept_aliases (
            alias_id INTEGER PRIMARY KEY AUTOINCREMENT,
            concept_id TEXT NOT NULL,
            value TEXT NOT NULL,
            normalized_value TEXT NOT NULL,
            language TEXT NOT NULL,
            kind TEXT NOT NULL,
            review_state TEXT NOT NULL DEFAULT 'UNREVIEWED',
            FOREIGN KEY(concept_id) REFERENCES ontology_concepts(concept_id) ON DELETE CASCADE
        );

        -- R3 G9: Typed Knowledge Graph
        CREATE TABLE IF NOT EXISTS graph_nodes (
            node_id TEXT PRIMARY KEY,
            node_type TEXT NOT NULL,
            namespace TEXT NOT NULL,
            label TEXT NOT NULL,
            stable_ref TEXT,
            review_state TEXT NOT NULL DEFAULT 'UNREVIEWED',
            source_id TEXT,
            properties_json TEXT,
            version TEXT NOT NULL DEFAULT '1.0',
            FOREIGN KEY(source_id) REFERENCES sources(source_id)
        );

        CREATE TABLE IF NOT EXISTS graph_edges (
            edge_id TEXT PRIMARY KEY,
            source_node_id TEXT NOT NULL,
            target_node_id TEXT NOT NULL,
            relation_type TEXT NOT NULL,
            assertion_kind TEXT NOT NULL DEFAULT 'EDUCATIONAL_PROPOSITION',
            provenance_evidence_id TEXT,
            review_state TEXT NOT NULL DEFAULT 'UNREVIEWED',
            confidence_text TEXT,
            valid_from TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
            supersedes_edge_id TEXT,
            FOREIGN KEY(source_node_id) REFERENCES graph_nodes(node_id) ON DELETE CASCADE,
            FOREIGN KEY(target_node_id) REFERENCES graph_nodes(node_id) ON DELETE CASCADE,
            FOREIGN KEY(provenance_evidence_id) REFERENCES evidence(evidence_id),
            FOREIGN KEY(supersedes_edge_id) REFERENCES graph_edges(edge_id)
        );

        -- R3 G10: Published Releases Registry
        CREATE TABLE IF NOT EXISTS published_releases (
            release_id TEXT PRIMARY KEY,
            build_id TEXT NOT NULL,
            manifest_hash TEXT NOT NULL,
            published_at TEXT NOT NULL,
            published_by TEXT NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 0,
            qa_report_json TEXT NOT NULL,
            manifest_json TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_source_locations_src ON source_locations(source_id);
        CREATE INDEX IF NOT EXISTS idx_claims_status ON claims(status);
        CREATE INDEX IF NOT EXISTS idx_claims_namespace ON claims(knowledge_namespace);
        CREATE INDEX IF NOT EXISTS idx_evidence_source ON evidence(source_id);
        CREATE INDEX IF NOT EXISTS idx_claim_evidence_claim ON claim_evidence_links(claim_id);
        CREATE INDEX IF NOT EXISTS idx_claim_evidence_evid ON claim_evidence_links(evidence_id);
        CREATE INDEX IF NOT EXISTS idx_contradictions_a ON contradictions(claim_a_id);
        CREATE INDEX IF NOT EXISTS idx_contradictions_b ON contradictions(claim_b_id);
        CREATE INDEX IF NOT EXISTS idx_aliases_concept ON concept_aliases(concept_id);
        CREATE INDEX IF NOT EXISTS idx_aliases_normalized ON concept_aliases(normalized_value);
        CREATE INDEX IF NOT EXISTS idx_graph_edges_src ON graph_edges(source_node_id);
        CREATE INDEX IF NOT EXISTS idx_graph_edges_tgt ON graph_edges(target_node_id);
        """
    ),
    (
        5,
        "0005_r4_atlas_3d_models_and_anchors",
        """
        -- R4 ATLAS-01..03: 3D Model Registry
        CREATE TABLE IF NOT EXISTS models_3d (
            model_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            mesh_id TEXT NOT NULL,
            sha256 TEXT NOT NULL,
            units TEXT NOT NULL DEFAULT 'mm',
            coordinate_frame TEXT NOT NULL DEFAULT 'mesh_local_xyz',
            reference_pose TEXT NOT NULL DEFAULT 'standing_anatomical',
            handedness TEXT NOT NULL DEFAULT 'right_handed',
            landmarks_json TEXT NOT NULL DEFAULT '{}',
            skin_mesh_id TEXT NOT NULL,
            license TEXT NOT NULL,
            rights_status TEXT NOT NULL DEFAULT 'ALLOWED',
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
        );

        -- R4 ATLAS-02: Barycentric Surface Anchors on Declared Skin Mesh
        CREATE TABLE IF NOT EXISTS skin_anchors (
            anchor_id TEXT PRIMARY KEY,
            model_id TEXT NOT NULL,
            mesh_sha256 TEXT NOT NULL,
            face_index INTEGER NOT NULL,
            barycentric_u REAL NOT NULL,
            barycentric_v REAL NOT NULL,
            barycentric_w REAL NOT NULL,
            surface_x REAL NOT NULL,
            surface_y REAL NOT NULL,
            surface_z REAL NOT NULL,
            normal_x REAL NOT NULL,
            normal_y REAL NOT NULL,
            normal_z REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'VALID',
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
            FOREIGN KEY(model_id) REFERENCES models_3d(model_id) ON DELETE CASCADE
        );

        -- R4 ATLAS-02, 03: 3D Point Placements
        CREATE TABLE IF NOT EXISTS point_placements_3d (
            placement_id TEXT PRIMARY KEY,
            concept_id TEXT NOT NULL,
            canonical_label TEXT NOT NULL,
            source_id TEXT NOT NULL,
            model_id TEXT NOT NULL,
            anchor_id TEXT,
            side TEXT NOT NULL DEFAULT 'bilateral',
            raw_x REAL NOT NULL,
            raw_y REAL NOT NULL,
            raw_z REAL NOT NULL,
            frame_registered INTEGER NOT NULL DEFAULT 0,
            registration_method TEXT NOT NULL DEFAULT 'NONE',
            registration_status TEXT NOT NULL DEFAULT 'UNREGISTERED',
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
            FOREIGN KEY(model_id) REFERENCES models_3d(model_id) ON DELETE CASCADE,
            FOREIGN KEY(anchor_id) REFERENCES skin_anchors(anchor_id)
        );

        -- R4 ATLAS-02: Baked Meridian Paths on Skin Surface
        CREATE TABLE IF NOT EXISTS meridian_paths_3d (
            path_id TEXT PRIMARY KEY,
            meridian_code TEXT NOT NULL,
            source_id TEXT NOT NULL,
            model_id TEXT NOT NULL,
            ordered_points_json TEXT NOT NULL,
            baked_segments_json TEXT NOT NULL,
            has_penetration_gap INTEGER NOT NULL DEFAULT 0,
            gap_warnings_json TEXT,
            review_state TEXT NOT NULL DEFAULT 'UNREVIEWED',
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
            FOREIGN KEY(model_id) REFERENCES models_3d(model_id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_skin_anchors_model ON skin_anchors(model_id);
        CREATE INDEX IF NOT EXISTS idx_skin_anchors_face ON skin_anchors(face_index);
        CREATE INDEX IF NOT EXISTS idx_placements_concept ON point_placements_3d(concept_id);
        CREATE INDEX IF NOT EXISTS idx_placements_label ON point_placements_3d(canonical_label);
        CREATE INDEX IF NOT EXISTS idx_meridian_paths_code ON meridian_paths_3d(meridian_code);
        """
    ),
    (
        6,
        "0006_r5_studio_private_projects_and_dien_chan_2d",
        """
        -- R5 ATLAS-05: Private Atlas Projects
        CREATE TABLE IF NOT EXISTS private_atlas_projects (
            project_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            namespace TEXT NOT NULL,
            description TEXT,
            base_model_id TEXT,
            base_image_sha256 TEXT,
            license TEXT NOT NULL DEFAULT 'PROPRIETARY_DRAFT',
            version INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
            updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
        );

        -- R5 ATLAS-05, ATLAS-06: Studio Points (3D Surface or 2D Image Pixel)
        CREATE TABLE IF NOT EXISTS studio_points (
            point_id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            code TEXT NOT NULL,
            canonical_label TEXT NOT NULL,
            namespace TEXT NOT NULL,
            point_kind TEXT NOT NULL DEFAULT 'FIXED_EDUCATIONAL',
            session_id TEXT,
            session_timestamp TEXT,
            dimensionality TEXT NOT NULL DEFAULT '3D_SURFACE',
            image_sha256 TEXT,
            image_view TEXT,
            x_px REAL,
            y_px REAL,
            model_id TEXT,
            mesh_sha256 TEXT,
            surface_x REAL,
            surface_y REAL,
            surface_z REAL,
            face_index INTEGER,
            barycentric_u REAL,
            barycentric_v REAL,
            barycentric_w REAL,
            notes TEXT,
            is_deleted INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
            updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
            FOREIGN KEY(project_id) REFERENCES private_atlas_projects(project_id) ON DELETE CASCADE
        );

        -- R5 ATLAS-05: Studio Edit History (Undo/Redo & Lineage)
        CREATE TABLE IF NOT EXISTS studio_edit_history (
            history_id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id TEXT NOT NULL,
            action_type TEXT NOT NULL,
            point_id TEXT NOT NULL,
            before_state_json TEXT,
            after_state_json TEXT,
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
            FOREIGN KEY(project_id) REFERENCES private_atlas_projects(project_id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_studio_pts_proj ON studio_points(project_id);
        CREATE INDEX IF NOT EXISTS idx_studio_pts_code ON studio_points(code);
        CREATE INDEX IF NOT EXISTS idx_studio_pts_ns ON studio_points(namespace);
        CREATE INDEX IF NOT EXISTS idx_studio_pts_kind ON studio_points(point_kind);
        CREATE INDEX IF NOT EXISTS idx_studio_hist_proj ON studio_edit_history(project_id);
        """
    )
]


def init_migration_table(conn) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            applied_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
        );
    """)


def get_applied_migrations(conn) -> List[int]:
    init_migration_table(conn)
    cur = conn.execute("SELECT version FROM schema_migrations ORDER BY version ASC;")
    return [row[0] for row in cur.fetchall()]


def run_migrations(custom_path: Optional[Path] = None) -> List[str]:
    """Run pending migrations in sequence within individual transactions."""
    applied_names = []
    with get_db(custom_path) as conn:
        init_migration_table(conn)
        applied = set(get_applied_migrations(conn))

        for version, name, sql in MIGRATIONS:
            if version not in applied:
                # Execute migration within transaction
                conn.executescript(sql)
                conn.execute(
                    "INSERT INTO schema_migrations (version, name, applied_at) VALUES (?, ?, ?);",
                    (version, name, datetime.datetime.utcnow().isoformat() + "Z")
                )
                # Record audit event
                conn.execute(
                    "INSERT INTO audit_events (event_type, actor, payload_json) VALUES (?, ?, ?);",
                    ("MIGRATION_APPLIED", "SYSTEM", f'{{"version": {version}, "name": "{name}"}}')
                )
                applied_names.append(name)

    return applied_names
