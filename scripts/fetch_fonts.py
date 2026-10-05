"""Vendor the two reference fonts from Google Fonts for an offline interface."""
from pathlib import Path
import re
import urllib.request

root = Path(__file__).resolve().parents[1] / 'static/fonts'
root.mkdir(parents=True, exist_ok=True)
for family, filename, weights in [('Inter', 'inter-latin.woff2', '100..900'), ('JetBrains+Mono', 'jetbrains-mono-latin.woff2', '100..800')]:
    request = urllib.request.Request(
        f'https://fonts.googleapis.com/css2?family={family}:wght@{weights}&display=swap',
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'},
    )
    css = urllib.request.urlopen(request, timeout=30).read().decode('utf-8')
    block = css.split('/* latin */')[-1]
    url = re.search(r'url\((https://fonts.gstatic.com/[^)]+)\)', block)
    if not url:
        raise RuntimeError(f'No font URL returned for {family}')
    font = urllib.request.urlopen(url.group(1), timeout=30).read()
    if font[:4] != b'wOF2':
        raise RuntimeError('Expected a WOFF2 font; the previous file was left unchanged.')
    (root / filename).write_bytes(font)
    print(filename, len(font))
    slug = family.replace('+', '').lower()
    license_url = f'https://raw.githubusercontent.com/google/fonts/main/ofl/{slug}/OFL.txt'
    (root / f'{slug}-OFL.txt').write_bytes(urllib.request.urlopen(license_url, timeout=30).read())
