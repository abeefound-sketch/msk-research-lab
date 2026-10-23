python3 -c "
import os, subprocess

print('Checking Desktop paths:')
candidates = [
    os.path.expanduser('~/Desktop'),
    '/mnt/c/Users/tuanh/Desktop',
    '/Users/giangmetta/Desktop'
]
for c in candidates:
    print(f'{c}: exists={os.path.exists(c)}')

print('\nChecking test suite:')
res = subprocess.run(['pytest', '-q'], capture_output=True, text=True)
print(f'pytest exit: {res.returncode}')
print(res.stdout[-300:] if res.stdout else '')
print(res.stderr[-300:] if res.stderr else '')
"