import os
import json
import re
import subprocess

os.makedirs('docs/videos', exist_ok=True)

with open('docs/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

m = re.search(r'const DEFAULT_PRODUCTS\s*=\s*(\[.*?\]);', html, re.DOTALL)
if not m:
    print("Could not find DEFAULT_PRODUCTS")
    exit(1)

prods = json.loads(m.group(1))

# Process each product
updated_count = 0
for p in prods:
    img = p.get('image', '')
    hash_name = os.path.splitext(os.path.basename(img))[0]
    gen_dir = os.path.join('generated', 'whatsapp', hash_name)
    
    video_source = None
    if os.path.isdir(gen_dir):
        for pref in ['luxury_gold_black.mp4', 'elegant_white_gold.mp4', 'minimal_premium.mp4']:
            vpath = os.path.join(gen_dir, pref)
            if os.path.isfile(vpath):
                video_source = vpath
                break
    
    if video_source:
        dest_filename = f"reel_{p['id']}.mp4"
        dest_path = os.path.join('docs', 'videos', dest_filename)
        
        # Check if already compressed, else compress with ffmpeg
        if not os.path.isfile(dest_path):
            print(f"Compressing video for Product {p['id']} ({p['title'][:30]})...")
            cmd = [
                'ffmpeg', '-y', '-i', video_source,
                '-vf', 'scale=540:-2',
                '-c:v', 'libx264', '-crf', '26', '-preset', 'fast',
                '-c:a', 'aac', '-b:a', '96k',
                '-movflags', '+faststart',
                dest_path
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        if os.path.isfile(dest_path):
            size_kb = os.path.getsize(dest_path) / 1024
            p['video'] = f"videos/{dest_filename}"
            updated_count += 1
            print(f" -> Product {p['id']}: LINKED {p['video']} ({size_kb:.1f} KB)")
        else:
            p['video'] = None
    else:
        p['video'] = None

print(f"\nDone! Linked {updated_count} products with matching video reels. Remaining have video: null.")

# Save updated DEFAULT_PRODUCTS into docs/index.html
new_json = json.dumps(prods, indent=2)
# Replace in html
new_html = html[:m.start(1)] + new_json + html[m.end(1):]

with open('docs/index.html', 'w', encoding='utf-8') as f:
    f.write(new_html)

print("Successfully updated DEFAULT_PRODUCTS in docs/index.html")
