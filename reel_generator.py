from pathlib import Path
import subprocess

from PIL import Image, ImageDraw, ImageFont

WIDTH = 1080
HEIGHT = 1920
DURATION = 8
FPS = 30
MUSIC = Path("music/hitslab-luxury-jewellery-jewelry-music-489239.mp3")
OUTPUT_DIR = Path("generated")
OUTPUT_DIR.mkdir(exist_ok=True)
FONT_DIR = Path("C:/Windows/Fonts")

# Existing four designs are intentionally preserved.
THEMES = {
    "luxury_gold_black": {
        "background": (10, 9, 8), "gold": (218, 181, 105), "accent": (245, 220, 160),
        "text": (255, 255, 255), "photo_background": (22, 19, 15), "border": (218, 181, 105),
        "header": "EXCLUSIVE COLLECTION",
    },
    "elegant_white_gold": {
        "background": (250, 247, 239), "gold": (173, 132, 65), "accent": (125, 91, 39),
        "text": (48, 43, 35), "photo_background": (255, 255, 255), "border": (196, 161, 102),
        "header": "ELEGANT COLLECTION",
    },
    "pink_modern": {
        "background": (255, 231, 239), "gold": (174, 93, 119), "accent": (130, 49, 85),
        "text": (75, 35, 54), "photo_background": (255, 247, 249), "border": (218, 143, 166),
        "header": "NEW ARRIVALS",
    },
    "minimal_premium": {
        "background": (241, 237, 227), "gold": (139, 119, 86), "accent": (94, 79, 58),
        "text": (47, 44, 38), "photo_background": (250, 248, 242), "border": (183, 169, 142),
        "header": "THE SIGNATURE EDIT",
    },
}


def load_font(name, size):
    font_path = FONT_DIR / name
    if not font_path.exists():
        raise FileNotFoundError(f"Font missing: {font_path}")
    return ImageFont.truetype(str(font_path), size)


def centered_text(draw, text, y, font, color):
    box = draw.textbbox((0, 0), text, font=font)
    x = (WIDTH - (box[2] - box[0])) // 2
    draw.text((x, y), text, font=font, fill=color)


def wrap_text(draw, text, font, max_width):
    words, lines, current = text.split(), [], ""
    for word in words:
        candidate = f"{current} {word}".strip()
        box = draw.textbbox((0, 0), candidate, font=font)
        if box[2] - box[0] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def create_poster(image_path, product_name, price, output_path, theme_name):
    theme = THEMES[theme_name]
    canvas = Image.new("RGB", (WIDTH, HEIGHT), theme["background"])
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle((35, 35, 1045, 1885), radius=25, outline=theme["border"], width=3)
    centered_text(draw, theme["header"], 105, load_font("arialbd.ttf", 38), theme["gold"])
    draw.line((220, 185, 860, 185), fill=theme["border"], width=2)
    title_font = load_font("georgia.ttf", 62)
    title_y = 225
    for line in wrap_text(draw, product_name, title_font, 900)[:2]:
        centered_text(draw, line, title_y, title_font, theme["accent"])
        title_y += 78
    product = Image.open(image_path).convert("RGB")
    product.thumbnail((940, 1050), Image.Resampling.LANCZOS)
    photo_x, photo_y = (WIDTH - product.width) // 2, 450
    draw.rounded_rectangle((photo_x - 12, photo_y - 12, photo_x + product.width + 12, photo_y + product.height + 12), radius=20, fill=theme["photo_background"], outline=theme["border"], width=4)
    canvas.paste(product, (photo_x, photo_y))
    draw = ImageDraw.Draw(canvas)
    badge_top = 1560
    draw.rounded_rectangle((220, badge_top, 860, badge_top + 105), radius=24, fill=theme["photo_background"], outline=theme["border"], width=3)
    centered_text(draw, f"ONLY {price}", badge_top + 20, load_font("arialbd.ttf", 48), theme["accent"])
    centered_text(draw, "FREE SHIPPING", 1695, load_font("arialbd.ttf", 40), theme["gold"])
    centered_text(draw, "DM TO ORDER", 1770, load_font("arialbd.ttf", 50), theme["text"])
    centered_text(draw, "LIMITED STOCK | ORDER NOW", 1840, load_font("arial.ttf", 24), theme["gold"])
    canvas.save(output_path, quality=95)


def generate_reel(image_path, product_name, price, theme_name, output_dir=None):
    output_dir = Path(output_dir or OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    poster_path = output_dir / f"{theme_name}_poster.jpg"
    video_path = output_dir / f"{theme_name}.mp4"
    create_poster(image_path, product_name, price, poster_path, theme_name)
    # command = [
    #     "ffmpeg", "-y", "-loop", "1", "-i", str(poster_path),
    #     "-stream_loop", "-1", "-i", str(MUSIC), "-t", str(DURATION),
    #     "-vf", "zoompan=z='min(zoom+0.0003,1.025)':d=240:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30,format=yuv420p",
    #     "-c:v", "libx264", "-preset", "medium", "-crf", "20",
    #     "-c:a", "aac", "-b:a", "128k", "-ar", "48000",
    #     "-shortest", "-movflags", "+faststart", str(video_path),
    # ]

    command = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", str(poster_path),
        "-stream_loop", "-1", "-i", str(MUSIC),
        "-t", str(DURATION),

        "-vf",
        "zoompan=z='min(zoom+0.0003,1.025)':d=240:"
        "x='iw/2-(iw/zoom/2)':"
        "y='ih/2-(ih/zoom/2)':"
        "s=1080x1920:fps=30,"
        "scale=1080:1920:in_range=full:out_range=tv:"
        "out_color_matrix=bt709,"
        "format=yuv420p",

        "-c:v", "libx264",
        "-preset", "slow",
        "-crf", "18",
        "-profile:v", "high",
        "-level:v", "4.1",
        "-pix_fmt", "yuv420p",
        "-color_range", "tv",
        "-colorspace", "bt709",
        "-color_primaries", "bt709",
        "-color_trc", "bt709",
        "-r", "30",
        "-g", "60",

        "-c:a", "aac",
        "-b:a", "128k",
        "-ar", "48000",

        "-shortest",
        "-movflags", "+faststart",
        str(video_path),
    ]

    subprocess.run(command, check=True)
    print(f"SUCCESS: {video_path}")
    return video_path


def generate_all(image_path, product_name, price, output_dir=None):
    image_path = Path(image_path)
    if not image_path.exists():
        raise FileNotFoundError(f"Product image not found: {image_path}")
    if not MUSIC.exists():
        raise FileNotFoundError(f"Music not found: {MUSIC}")
    output_dir = Path(output_dir or OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    generated = []
    for theme_name in THEMES:
        print(f"\nGenerating: {theme_name}")
        generated.append(generate_reel(image_path, product_name, price, theme_name, output_dir))
    print("\nALL FOUR REELS GENERATED SUCCESSFULLY")
    return generated


if __name__ == "__main__":
    videos = generate_all("uploads/necklace.jpg", "German Silver Necklace", "₹550")
    for video in videos:
        print(video)
