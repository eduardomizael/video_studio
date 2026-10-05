"""Download the original Stitch references, without changing the remote project."""
import json
import pathlib
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
screens = json.loads((ROOT / 'docs/stitch/screens.json').read_text(encoding='utf-8'))
for screen in screens:
    key = screen['name'].split('/')[-1]
    for field, suffix in [('htmlCode', '.svg' if screen.get('htmlCode', {}).get('mimeType') == 'image/svg+xml' else '.html'), ('screenshot', '.png')]:
        url = screen.get(field, {}).get('downloadUrl')
        if url:
            target = ROOT / 'docs/stitch' / (key + suffix)
            if field == 'screenshot':
                url += '=s0'
            with urllib.request.urlopen(url, timeout=60) as response:
                payload = response.read()
                if field == 'htmlCode' and b'accounts.google.com/v3/signin' in payload[:1000]:
                    if target.exists():
                        target.unlink()
                    print(key, 'HTML requires a Google session; screenshot retained as reference.')
                    continue
                target.write_bytes(payload)
            print(target.name, target.stat().st_size)
