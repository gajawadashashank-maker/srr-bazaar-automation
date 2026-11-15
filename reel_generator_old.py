
from pathlib import Path
import subprocess

from PIL import Image, ImageDraw, ImageFont

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

WIDTH = 1080
HEIGHT = 1920
DURATION = 8
FPS = 30

MUSIC = Path(
    "music/hitslab-luxury-jewellery-jewelry-music-489239.mp3"
)

OUTPUT_DIR = Path("generated")
OUTPUT_DIR.mkdir(exist_ok=True)

FONT_DIR = Path("C:/Windows/Fonts")

# Four design themes
THEMES = {
    "luxury_gold_black": {
        "background": (10, 9, 8),
        "gold": (218, 181, 105),
        "accent": (245, 220, 160),
        "text": (255, 255, 255),
        "photo_background": (22, 19, 15),
        "border": (218, 181, 105),
        "header": "EXCLUSIVE COLLECTION",
    },

    "elegant_white_gold": {
        "background": (250, 247, 239),
        "gold": (173, 132, 65),
        "accent": (125, 91, 39),
        "text": (48, 43, 35),
        "photo_background": (255, 255, 255),
        "border": (196, 161, 102),
        "header": "ELEGANT COLLECTION",
    },

    "pink_modern": {
        "background": (255, 231, 239),
        "gold": (174, 93, 119),
        "accent": (130, 49, 85),
        "text": (75, 35, 54),
        "photo_background": (255, 247, 249),
        "border": (218, 143, 166),
        "header": "NEW ARRIVALS",
    },

    "minimal_premium": {
        "background": (241, 237, 227),
        "gold": (139, 119, 86),
        "accent": (94, 79, 58),
        "text": (47, 44, 38),
        "photo_background": (250, 248, 242),
        "border": (183, 169, 142),
        "header": "THE SIGNATURE EDIT",
    },
}


# --------------------------------------------------
# FONT HELPERS
# --------------------------------------------------

def load_font(name, size):
    font_path = FONT_DIR / name

    if not font_path.exists():
        raise FileNotFoundError(
            f"Font missing: {font_path}"
        )

    return ImageFont.truetype(
        str(font_path),
        size
    )


def centered_text(draw, text, y, font, color):
    box = draw.textbbox(
        (0, 0),
        text,
        font=font
    )

    text_width = box[2] - box[0]

    x = (WIDTH - text_width) // 2

    draw.text(
        (x, y),
        text,
        font=font,
        fill=color
    )


def wrap_text(draw, text, font, max_width):
    words = text.split()
    lines = []
    current = ""

    for word in words:
        candidate = f"{current} {word}".strip()

        box = draw.textbbox(
            (0, 0),
            candidate,
            font=font
        )

        if box[2] - box[0] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word

    if current:
        lines.append(current)

    return lines


# --------------------------------------------------
# POSTER GENERATION
# --------------------------------------------------

def create_poster(
    image_path,
    product_name,
    price,
    output_path,
    theme_name
):

    theme = THEMES[theme_name]

    bg = theme["background"]
    gold = theme["gold"]
    accent = theme["accent"]
    text_color = theme["text"]
    border = theme["border"]

    canvas = Image.new(
        "RGB",
        (WIDTH, HEIGHT),
        bg
    )

    draw = ImageDraw.Draw(canvas)

    # Outer decorative frame
    draw.rounded_rectangle(
        (35, 35, 1045, 1885),
        radius=25,
        outline=border,
        width=3
    )

    # Header
    centered_text(
        draw,
        theme["header"],
        105,
        load_font("arialbd.ttf", 38),
        gold
    )

    draw.line(
        (220, 185, 860, 185),
        fill=border,
        width=2
    )

    # Product name
    title_font = load_font(
        "georgia.ttf",
        62
    )

    title_lines = wrap_text(
        draw,
        product_name,
        title_font,
        900
    )

    title_y = 225

    for line in title_lines[:2]:
        centered_text(
            draw,
            line,
            title_y,
            title_font,
            accent
        )
        title_y += 78

    # Product photo
    product = Image.open(
        image_path
    ).convert("RGB")

    product.thumbnail(
        (940, 1050),
        Image.Resampling.LANCZOS
    )

    photo_x = (WIDTH - product.width) // 2
    photo_y = 450

    # Photo background and frame
    draw.rounded_rectangle(
        (
            photo_x - 12,
            photo_y - 12,
            photo_x + product.width + 12,
            photo_y + product.height + 12
        ),
        radius=20,
        fill=theme["photo_background"],
        outline=border,
        width=4
    )

    canvas.paste(
        product,
        (photo_x, photo_y)
    )

    draw = ImageDraw.Draw(canvas)

    # Price badge
    badge_top = 1560

    draw.rounded_rectangle(
        (220, badge_top, 860, badge_top + 105),
        radius=24,
        fill=theme["photo_background"],
        outline=border,
        width=3
    )

    centered_text(
        draw,
        f"ONLY {price}",
        badge_top + 20,
        load_font("arialbd.ttf", 48),
        accent
    )

    # Free shipping
    centered_text(
        draw,
        "FREE SHIPPING",
        1695,
        load_font("arialbd.ttf", 40),
        gold
    )

    # CTA
    centered_text(
        draw,
        "DM TO ORDER",
        1770,
        load_font("arialbd.ttf", 50),
        text_color
    )

    centered_text(
        draw,
        "LIMITED STOCK | ORDER NOW",
        1840,
        load_font("arial.ttf", 24),
        gold
    )

    canvas.save(
        output_path,
        quality=95
    )


# --------------------------------------------------
# REEL GENERATION
# --------------------------------------------------

def generate_reel(
    image_path,
    product_name,
    price,
    theme_name
):

    poster_path = OUTPUT_DIR / f"{theme_name}_poster.jpg"

    video_path = OUTPUT_DIR / f"{theme_name}.mp4"

    create_poster(
        image_path=image_path,
        product_name=product_name,
        price=price,
        output_path=poster_path,
        theme_name=theme_name
    )

    command = [
        "ffmpeg",
        "-y",

        "-loop", "1",
        "-i", str(poster_path),

        "-stream_loop", "-1",
        "-i", str(MUSIC),

        "-t", str(DURATION),

        "-vf",
        (
            "zoompan="
            "z='min(zoom+0.0003,1.025)':"
            "d=240:"
            "x='iw/2-(iw/zoom/2)':"
            "y='ih/2-(ih/zoom/2)':"
            "s=1080x1920:fps=30,"
            "format=yuv420p"
        ),

        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "20",

        "-c:a", "aac",
        "-b:a", "128k",
        "-ar", "44100",

        "-shortest",
        "-movflags", "+faststart",

        str(video_path)
    ]

    subprocess.run(
        command,
        check=True
    )

    print(f"SUCCESS: {video_path}")

    return video_path


# --------------------------------------------------
# GENERATE ALL FOUR THEMES
# --------------------------------------------------

def generate_all(
    image_path,
    product_name,
    price
):

    if not Path(image_path).exists():
        raise FileNotFoundError(
            f"Product image not found: {image_path}"
        )

    if not MUSIC.exists():
        raise FileNotFoundError(
            f"Music not found: {MUSIC}"
        )

    generated = []

    for theme_name in THEMES:

        print("\nGenerating:", theme_name)

        video = generate_reel(
            image_path=image_path,
            product_name=product_name,
            price=price,
            theme_name=theme_name
        )

        generated.append(video)

    print("\nALL FOUR REELS GENERATED SUCCESSFULLY")

    for video in generated:
        print(video)


# --------------------------------------------------
# MAIN
# --------------------------------------------------

if __name__ == "__main__":

    generate_all(
        image_path="uploads/necklace.jpg",
        product_name="German Silver Necklace",
        price="₹550"
    )
