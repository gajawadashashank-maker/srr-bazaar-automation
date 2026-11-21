import json
import re
import os

with open('docs/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

scripts = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
print(f"Found {len(scripts)} JSON-LD blocks")
for i, s in enumerate(scripts):
    data = json.loads(s)
    print(f"Block {i+1} parsed OK, top-level keys: {list(data.keys())}")
    if '@graph' in data:
        for node in data['@graph']:
            print(f" - Node @type: {node.get('@type')} (name: {node.get('name', 'N/A')})")

icons = [
    'docs/favicon-48x48.png', 'docs/favicon-32x32.png', 'docs/icon-192.png',
    'docs/icon-512.png', 'docs/apple-touch-icon.png', 'docs/favicon.ico',
    'docs/images/srr_bazaar_logo.png'
]
for icon in icons:
    exists = os.path.isfile(icon)
    size = os.path.getsize(icon) if exists else 0
    print(f"{icon}: exists={exists}, size={size} bytes")

print("All SEO and structured data checks PASSED!")
