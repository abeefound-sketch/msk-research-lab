python3 -c "
import os, glob, subprocess

print('Virtualenvs:')
for p in glob.glob('/mnt/c/Users/tuanh/Downloads/msk-research-lab/**/activate', recursive=True):
    print(p)
for p in glob.glob('/home/tuan/**/activate', recursive=True):
    print(p)

print('\nTop-level dirs and files:')
for item in sorted(os.listdir('.')):
    print(item, '(dir)' if os.path.isdir(item) else '')

print('\nscripts/doctor.sh:')
if os.path.exists('scripts/doctor.sh'):
    with open('scripts/doctor.sh') as f:
        print(f.read())
"