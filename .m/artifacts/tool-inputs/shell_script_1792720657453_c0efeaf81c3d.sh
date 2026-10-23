python3 -c "
import json, os, subprocess

print('=== GIT STATUS ===')
subprocess.run(['git', 'status', '--short'])

print('\n=== HANDOFF DOC ===')
if os.path.exists('1docs/NEXT_SESSION_HANDOFF.md'):
    with open('1docs/NEXT_SESSION_HANDOFF.md') as f:
        print(f.read()[:2000])

print('\n=== TASK BACKLOG SUMMARY ===')
if os.path.exists('config/task_backlog.json'):
    with open('config/task_backlog.json') as f:
        data = json.load(f)
        tasks = data if isinstance(data, list) else data.get('tasks', [])
        status_counts = {}
        for t in tasks:
            s = t.get('status', 'unknown')
            status_counts[s] = status_counts.get(s, 0) + 1
        print(f'Total tasks: {len(tasks)}, Status counts: {status_counts}')
        print('Sample tasks:')
        for t in tasks[:5]:
            print(f\"- [{t.get('status')}] {t.get('id', '')}: {t.get('title', t.get('name', ''))}\")
"