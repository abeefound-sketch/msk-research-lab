python3 -c "
import os, glob

files = sorted(glob.glob('2data/evidence/*'))
print(f'Total evidence files: {len(files)}')
for f in files:
    size = os.path.getsize(f)
    print(f'{f} ({size} bytes)')
"