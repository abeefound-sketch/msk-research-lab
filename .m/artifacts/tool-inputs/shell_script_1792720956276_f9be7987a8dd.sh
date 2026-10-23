python3 -c "
import os, zipfile, shutil

slug = 'msk-research-lab-audit'
stage_dir = f'/tmp/{slug}'
if os.path.exists(stage_dir):
    shutil.rmtree(stage_dir)
os.makedirs(stage_dir, exist_ok=True)

# Files and directories to include
includes = [
    'src',
    'tests',
    'schemas',
    'config',
    'scripts',
    '1docs',
    '2data/evidence',
    'README.md',
    'pyproject.toml'
]

# Copy files
for item in includes:
    dest = os.path.join(stage_dir, item)
    if os.path.isdir(item):
        shutil.copytree(item, dest, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.pytest_cache', '*.zip'))
    elif os.path.isfile(item):
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copy2(item, dest)

# Create zip file
zip_path = f'/mnt/c/Users/tuanh/Desktop/{slug}-source.zip'
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk(stage_dir):
        for file in files:
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, stage_dir)
            zipf.write(full_path, rel_path)

# Also copy to /home/tuan/Desktop for convenience
shutil.copy2(zip_path, f'/home/tuan/Desktop/{slug}-source.zip')

print(f'Zip created at {zip_path}')
print(f'Size: {os.path.getsize(zip_path) / 1024:.1f} KB')

# Check file count in zip
with zipfile.ZipFile(zip_path, 'r') as z:
    names = z.namelist()
    print(f'Total files in zip: {len(names)}')
    print('Sample files in zip:')
    for n in names[:10]:
        print('  -', n)
"