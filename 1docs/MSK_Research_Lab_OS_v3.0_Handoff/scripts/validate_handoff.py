#!/usr/bin/env python3
"""Static design-handoff validation only. NEVER equates to future app/runtime/security PASS.

Usage: python scripts/validate_handoff.py
No external network access and no changes to host systems or user data.
"""
from __future__ import annotations
import hashlib, json, pathlib, re, sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
REQUIRED=[
 '00_START_HERE.md','SPEC/MASTER_SPEC_v3.0.md','SPEC/ROADMAP_R0_R6.md','SPEC/ACCEPTANCE_MATRIX.md',
 'SPEC/ARCHITECTURE.md','SPEC/DATA_MODEL.md','SPEC/ATLAS_GEOMETRY.md','SPEC/KNOWLEDGE_LIBRARY.md',
 'SPEC/KNOWLEDGE_INTEGRITY.md','SPEC/API_CONTRACT.md','SPEC/SECURITY_AND_RIGHTS.md',
 'SPEC/RESOURCE_BUDGET.md','SPEC/UI_JOURNEYS.md','AGENT/AGENTS.md','AGENT/SESSION_00_PROMPT.md',
 'AGENT/RELEASE_PROMPTS_R1_R6.md','AGENT/MILESTONE_REPORT_TEMPLATE.md','AGENT/SESSION_HANDOFF_TEMPLATE.md',
 'AGENT/RELEASE_CHECKLIST.md','CONFIG/repo_catalog.json','CONFIG/run_profiles.json',
 'CONFIG/release_gates.json','CONFIG/task_backlog.json','CONFIG/task_backlog.csv',
 'CONFIG/ontology_seed.json','SCHEMAS/openapi.yaml','TESTS/TEST_DATA_CONTRACT.md',
 'TESTS/BENCHMARK_SURFACE_REGISTRATION.md','TESTS/NEGATIVE_SECURITY_CASES.md',
 'TRACEABILITY/SOURCE_FILES_SHA256.txt','TRACEABILITY/SOURCE_RECONCILIATION.md',
 'TRACEABILITY/REQUIREMENT_TRACE_MATRIX.csv','TRACEABILITY/RISK_REGISTER.md',
 'REFERENCES/Atlas_Engineering_Spec_v1_English.md','REFERENCES/Repo_Research_Spec_v1_Vietnamese.md',
 'REFERENCES/Platform_MVP_v2.md','REFERENCES/Knowledge_Integrity_v2.1.md',
]
errors=[]
def check(condition,msg):
 if not condition:errors.append(msg)
for rel in REQUIRED:check((ROOT/rel).is_file(),f'Missing {rel}')
if errors: print('\n'.join(errors));sys.exit(1)
for f in list((ROOT/'CONFIG').glob('*.json'))+list((ROOT/'SCHEMAS').glob('*.json')):
 try:json.loads(f.read_text(encoding='utf8'))
 except Exception as e:errors.append(f'Invalid JSON {f.relative_to(ROOT)}: {e}')
G=json.loads((ROOT/'CONFIG/release_gates.json').read_text())
gates={x['id'] for x in G['gates']}
expected={f'G{i}' for i in range(1,11)}|{'SEC'}|{f'ATLAS-{i:02d}' for i in range(1,7)}|{f'BRIDGE-{i:02d}' for i in range(1,4)}
check(gates==expected, f'Gate mismatch missing={expected-gates}, extra={gates-expected}')
check(not G['whole_product_complete'] and all(x['state']=='NOT_TESTED' for x in G['gates']),'Unjustified PASS/completion status in seed gates')
CAT=json.loads((ROOT/'CONFIG/repo_catalog.json').read_text())
check(len(CAT['repositories'])==9,'Catalog must include nine core candidate repositories')
for entry in CAT['repositories']:
 check(entry['pinned_sha'] is None, 'Seed claims an unverified pinned SHA')
 for k in ['clone_allowed_by_default','install_allowed_by_default','run_allowed_by_default']:
  check(entry[k] is False,f'Unsafe default {entry["id"]} {k}')
PRO=json.loads((ROOT/'CONFIG/run_profiles.json').read_text())
check(PRO['default_execution_policy']=='DENY' and not PRO['profiles'],'Unexpected preapproved runtime profile')
check(PRO['example_proposed_profile_NOT_APPROVED']['enabled'] is False,'Example run profile must stay disabled')
TASKS=json.loads((ROOT/'CONFIG/task_backlog.json').read_text())['tasks']
ids=[t['id'] for t in TASKS]
check(len(TASKS)>=40 and len(ids)==len(set(ids)),'Missing or duplicate implementation tasks')
check(all(t['status']=='NOT_STARTED' for t in TASKS),'Unexpected precompleted task')
roadmap=(ROOT/'SPEC/ROADMAP_R0_R6.md').read_text(encoding='utf8')
for tid in ids:check(tid in roadmap,f'Task not found in roadmap: {tid}')
accept=(ROOT/'SPEC/ACCEPTANCE_MATRIX.md').read_text(encoding='utf8')
for g in sorted(gates):check(re.search(r'\b'+re.escape(g)+r'\b',accept)!=None,f'Gate absent from acceptance: {g}')
lines=(ROOT/'TRACEABILITY/SOURCE_FILES_SHA256.txt').read_text().splitlines()
check(len(lines)==4,'Expected SHA fingerprints for four original source specs')
for line in lines:
 m=re.match(r'^([0-9a-f]{64})  (.+)$',line)
 if not m:errors.append(f'Bad source hash line: {line}');continue
 sha,fn=m.groups(); path=pathlib.Path(fn)
 if not path.is_absolute():path=ROOT/path
 check(path.is_file(),f'Hash target missing: {path}')
 if path.is_file():check(hashlib.sha256(path.read_bytes()).hexdigest()==sha,f'Source file hash mismatch: {path}')
if (ROOT/'TRACEABILITY/PACKAGE_MANIFEST.sha256').exists():
 for line in (ROOT/'TRACEABILITY/PACKAGE_MANIFEST.sha256').read_text().splitlines():
  m=re.match(r'^([0-9a-f]{64})  (.+)$',line)
  if not m:errors.append('Bad package hash manifest line');continue
  sha,rel=m.groups(); file=ROOT/rel
  check(file.is_file(),f'Manifest missing {rel}')
  if file.is_file():check(hashlib.sha256(file.read_bytes()).hexdigest()==sha,f'Package tampered: {rel}')
try:
 import yaml
 doc=yaml.safe_load((ROOT/'SCHEMAS/openapi.yaml').read_text(encoding='utf8'))
 check(doc['openapi']=='3.1.0' and len(doc['paths'])>=15,'OpenAPI seed missing expected paths')
except ImportError:print('NOTICE: PyYAML unavailable; skipped semantic OpenAPI parse')
except Exception as e:errors.append(f'Invalid OpenAPI YAML: {e}')
try:
 from jsonschema.validators import validator_for
 for f in (ROOT/'SCHEMAS').glob('*.json'):
  s=json.loads(f.read_text()); validator_for(s).check_schema(s)
except ImportError:print('NOTICE: jsonschema unavailable; skipped schema meta-validation')
except Exception as e:errors.append(f'Invalid JSON Schema: {e}')
if errors:
 print(f'HANDOFF STATIC VALIDATION: FAIL ({len(errors)} issues)')
 for issue in errors: print(' -',issue)
 sys.exit(1)
print(f'HANDOFF STATIC VALIDATION: PASS; {len(REQUIRED)} required files; {len(TASKS)} tasks; {len(gates)} gates; 9 candidate repos; 4 hashed original source specs')
print('NOTE: This validates design-package consistency ONLY. Application, sandbox, medical, UI and hardware releases are all NOT_TESTED.')
