import json
import re

with open('docs/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

m = re.search(r'const DEFAULT_PRODUCTS\s*=\s*(\[.*?\]);', html, re.DOTALL)
default_prods = json.loads(m.group(1))
prod_map = {p['id']: p for p in default_prods}

with open('docs/products.json', 'r', encoding='utf-8') as f:
    products_json = json.load(f)

updated = 0
for p in products_json:
    pid = p.get('id')
    if pid in prod_map and prod_map[pid].get('video'):
        p['video'] = prod_map[pid]['video']
        updated += 1
    else:
        p['video'] = None

with open('docs/products.json', 'w', encoding='utf-8') as f:
    json.dump(products_json, f, indent=2, ensure_ascii=False)

print(f"Updated docs/products.json: {updated} products now have their matching dedicated video reel linked!")
