import math
import os
from PIL import Image, ImageDraw, ImageFont

def create_srr_logo():
    size = 512
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Outer gold glow/gradient rings
    center = size / 2
    r_outer = 246
    
    # Draw luxury gradient circular background
    # Colors: Gold border (#d4af37 -> #f3e5ab), Maroon base (#4a0404 -> #2a0000)
    for r in range(int(r_outer), 0, -1):
        ratio = r / r_outer
        if r > r_outer - 16:
            # Gold gradient rim
            gold_val = int(212 + (1 - ratio) * 40)
            draw.ellipse((center - r, center - r, center + r, center + r), fill=(212, 175, 55, 255))
        elif r > r_outer - 22:
            # Dark separator rim
            draw.ellipse((center - r, center - r, center + r, center + r), fill=(26, 0, 5, 255))
        elif r > r_outer - 28:
            # Inner thin gold accent
            draw.ellipse((center - r, center - r, center + r, center + r), fill=(245, 218, 122, 255))
        else:
            # Rich Royal Maroon gradient core
            red = int(74 * ratio + 35 * (1 - ratio))
            draw.ellipse((center - r, center - r, center + r, center + r), fill=(red, 4, 15, 255))
            
    # Draw Stars / Decorative Dots around rim
    num_dots = 16
    dot_radius = 232
    for i in range(num_dots):
        angle = i * (2 * math.pi / num_dots)
        dx = center + dot_radius * math.cos(angle)
        dy = center + dot_radius * math.sin(angle)
        draw.ellipse((dx - 3, dy - 3, dx + 3, dy + 3), fill=(255, 235, 160, 255))

    # Add Text: "SR" Monogram in Center, "SRR BAZAAR" below
    # Try serif fonts, fallback to default if not installed
    font_large = None
    font_small = None
    font_paths = [
        "C:/Windows/Fonts/georgiab.ttf",
        "C:/Windows/Fonts/timesbd.ttf",
        "C:/Windows/Fonts/arialbd.ttf"
    ]
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                font_large = ImageFont.truetype(fp, 170)
                font_small = ImageFont.truetype(fp, 38)
                break
            except Exception:
                pass
                
    if not font_large:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Draw Monogram "SR"
    text_sr = "SR"
    bbox_sr = draw.textbbox((0, 0), text_sr, font=font_large)
    w_sr = bbox_sr[2] - bbox_sr[0]
    h_sr = bbox_sr[3] - bbox_sr[1]
    
    # Shadow for 3D gold effect
    draw.text((center - w_sr / 2 + 3, center - h_sr / 2 - 25 + 3), text_sr, font=font_large, fill=(20, 0, 5, 200))
    # Rich Gold text
    draw.text((center - w_sr / 2, center - h_sr / 2 - 25), text_sr, font=font_large, fill=(245, 218, 122, 255))

    # Banner / Subtext "SRR BAZAAR"
    text_sub = "SRR BAZAAR"
    bbox_sub = draw.textbbox((0, 0), text_sub, font=font_small)
    w_sub = bbox_sub[2] - bbox_sub[0]
    
    # Gold divider bar
    draw.line((center - 110, center + 75, center + 110, center + 75), fill=(212, 175, 55, 255), width=2)
    # Text
    draw.text((center - w_sub / 2 + 1, center + 90 + 1), text_sub, font=font_small, fill=(20, 0, 5, 180))
    draw.text((center - w_sub / 2, center + 90), text_sub, font=font_small, fill=(255, 240, 180, 255))
    
    # Save in various sizes required by Google Favicon Guidelines
    os.makedirs("docs/images", exist_ok=True)
    
    # 512x512
    img.save("docs/icon-512.png")
    img.save("docs/images/srr_bazaar_logo.png")
    print("Saved docs/icon-512.png and docs/images/srr_bazaar_logo.png")
    
    # 192x192
    img_192 = img.resize((192, 192), Image.Resampling.LANCZOS)
    img_192.save("docs/icon-192.png")
    print("Saved docs/icon-192.png")
    
    # 180x180 (Apple touch icon)
    img_180 = img.resize((180, 180), Image.Resampling.LANCZOS)
    img_180.save("docs/apple-touch-icon.png")
    print("Saved docs/apple-touch-icon.png")
    
    # 48x48 (Google Favicon minimum multiple of 48)
    img_48 = img.resize((48, 48), Image.Resampling.LANCZOS)
    img_48.save("docs/favicon-48x48.png")
    print("Saved docs/favicon-48x48.png")
    
    # 32x32
    img_32 = img.resize((32, 32), Image.Resampling.LANCZOS)
    img_32.save("docs/favicon-32x32.png")
    print("Saved docs/favicon-32x32.png")
    
    # .ico (multi-size: 16, 32, 48)
    img_48.save("docs/favicon.ico", format="ICO", sizes=[(48, 48), (32, 32), (16, 16)])
    print("Saved docs/favicon.ico")

if __name__ == "__main__":
    create_srr_logo()
