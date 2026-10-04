"""Copy unchanged frontend files into Vercel's public CDN directory."""
from pathlib import Path
import shutil
root = Path(__file__).resolve().parent
source = root / 'assets'
public = root / 'public'
public.mkdir(exist_ok=True)
for item in source.iterdir():
    if item.is_file() and item.name not in ('CNAME', 'README.md'):
        for destination in (public / item.name, public / 'assets' / item.name):
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(item, destination)
print('Static frontend prepared.')
