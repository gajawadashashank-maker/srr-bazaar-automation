import os
import json
import re

# 1. Update docs/products.json
with open('docs/products.json', 'r', encoding='utf-8') as f:
    products = json.load(f)

linked_count = 0
for p in products:
    pid = p.get('id')
    v_path = f"docs/videos/reel_{pid}.mp4"
    if os.path.isfile(v_path):
        p['video'] = f"videos/reel_{pid}.mp4"
        linked_count += 1
    else:
        p['video'] = None

with open('docs/products.json', 'w', encoding='utf-8') as f:
    json.dump(products, f, indent=2, ensure_ascii=False)

print(f"docs/products.json: Linked {linked_count} products with their matching video reels.")

# 2. Update docs/index.html DEFAULT_PRODUCTS
with open('docs/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

m = re.search(r'const DEFAULT_PRODUCTS\s*=\s*(\[.*?\]);', html, re.DOTALL)
if m:
    def_prods = json.loads(m.group(1))
    def_linked = 0
    for p in def_prods:
        pid = p.get('id')
        v_path = f"docs/videos/reel_{pid}.mp4"
        if os.path.isfile(v_path):
            p['video'] = f"videos/reel_{pid}.mp4"
            def_linked += 1
        else:
            p['video'] = None
    
    new_json = json.dumps(def_prods, indent=2, ensure_ascii=False)
    new_html = html[:m.start(1)] + new_json + html[m.end(1):]
    with open('docs/index.html', 'w', encoding='utf-8') as f:
        f.write(new_html)
    print(f"docs/index.html: Linked {def_linked} DEFAULT_PRODUCTS with matching video reels.")

print("All synced successfully!")
