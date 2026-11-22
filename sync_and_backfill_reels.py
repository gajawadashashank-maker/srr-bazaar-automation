import json
import logging
import os
import re
import sqlite3
import subprocess
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(override=True)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("backfill_reels")

DOCS_DIR = Path("docs")
PRODUCTS_JSON_PATH = DOCS_DIR / "products.json"
VIDEOS_DIR = DOCS_DIR / "videos"
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
WHATSAPP_OUTPUT_DIR = Path("generated/whatsapp")
DB_PATH = Path("generated/whatsapp_jobs.sqlite3")

from reel_generator import generate_all, generate_reel
from instagram_publisher import publish_reel
from youtube_publisher import publish_youtube_short
import cloudinary
import cloudinary.uploader
from app import parse_product_caption, build_instagram_caption

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True,
)

def upload_to_cloudinary(video_path: Path) -> str:
    res = cloudinary.uploader.upload(
        str(video_path),
        resource_type="video",
        folder="product_reels",
    )
    url = res.get("secure_url")
    if not url:
        raise RuntimeError("Cloudinary upload failed")
    return url

def compress_reel_for_web(src_path: Path, dest_path: Path) -> bool:
    try:
        cmd = [
            "ffmpeg", "-y", "-i", str(src_path),
            "-vf", "scale=540:-2",
            "-c:v", "libx264", "-crf", "26", "-preset", "fast",
            "-c:a", "aac", "-b:a", "96k",
            "-movflags", "+faststart",
            str(dest_path)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        return dest_path.exists() and dest_path.stat().st_size > 0
    except Exception as e:
        logger.error(f"Compression error for {src_path} -> {dest_path}: {e}")
        return False

def process_failed_jobs():
    """Retry failed jobs from whatsapp_jobs table and publish them."""
    if not DB_PATH.exists():
        logger.info("DB path does not exist, skipping failed jobs retry.")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT message_id, image_path, caption FROM whatsapp_jobs WHERE status = 'failed' AND created_at LIKE '2026-11-21%'")
    rows = c.fetchall()
    conn.close()

    for msg_id, img_path_str, caption in rows:
        img_path = Path(img_path_str) if img_path_str else None
        if not img_path or not img_path.exists():
            logger.warning(f"Image not found for failed job {msg_id}: {img_path}")
            continue

        logger.info(f"Retrying failed job {msg_id} with caption: {caption[:40]}...")
        product_name, description, price = parse_product_caption(caption)
        job_id = Path(img_path).stem
        out_dir = WHATSAPP_OUTPUT_DIR / job_id
        out_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Generate 4 reels with updated fast generator
            reels = generate_all(
                image_path=img_path,
                product_name=product_name,
                price=price or "Special Offer",
                output_dir=out_dir
            )
            selected_reel = Path(reels[0]) if reels else None
            if not selected_reel or not selected_reel.exists():
                logger.error(f"Failed to generate reel for {msg_id}")
                continue

            # Upload to Cloudinary & Instagram
            ig_caption = build_instagram_caption(product_name, price, description)
            logger.info(f"Uploading {selected_reel} to Cloudinary...")
            video_url = upload_to_cloudinary(selected_reel)
            logger.info(f"Publishing to Instagram: {video_url}...")
            ig_res = publish_reel(video_url, ig_caption)
            ig_media_id = str(ig_res.get("media_id", ""))
            logger.info(f"Instagram published! Media ID: {ig_media_id}")

            # YouTube Short
            try:
                yt_title = f"{product_name} {price} | SRR Bazaar #Shorts"
                publish_youtube_short(video_source=str(selected_reel), title=yt_title, description=ig_caption)
            except Exception as yte:
                logger.warning(f"YouTube publishing skipped: {yte}")

            # Update DB
            conn = sqlite3.connect(DB_PATH)
            conn.execute(
                "UPDATE whatsapp_jobs SET status = 'published', selected_reel = ?, instagram_media_id = ?, error = NULL, updated_at = CURRENT_TIMESTAMP WHERE message_id = ?",
                (str(selected_reel), ig_media_id, msg_id)
            )
            conn.commit()
            conn.close()

            # Add to products.json
            from app import sync_product_to_website_catalogue
            sync_product_to_website_catalogue(
                image_path=img_path,
                product_name=product_name,
                price_str=price,
                description=description,
                job_id=job_id,
                video_path=selected_reel
            )
            logger.info(f"Successfully published and synced failed job {msg_id}!")
        except Exception as e:
            logger.exception(f"Error re-processing job {msg_id}: {e}")

def backfill_all_catalogue_videos():
    """Ensure every product in docs/products.json has a valid working video reel."""
    if not PRODUCTS_JSON_PATH.exists():
        logger.error("docs/products.json not found!")
        return

    products = json.loads(PRODUCTS_JSON_PATH.read_text(encoding="utf-8"))
    logger.info(f"Checking {len(products)} products for missing video reels...")
    updated_count = 0

    for p in products:
        pid = p.get("id")
        current_video = p.get("video")
        
        # Check if already has a valid existing video file
        if current_video:
            target_path = DOCS_DIR / current_video
            if target_path.exists() and target_path.stat().st_size > 10000:
                continue

        dest_name = f"reel_{pid}.mp4"
        dest_video_path = VIDEOS_DIR / dest_name
        rel_video_path = f"videos/{dest_name}"

        # 1. Try to find existing reel from job output directory
        img_rel = p.get("image", "")
        img_stem = Path(img_rel).stem
        found_source = None

        job_dir = WHATSAPP_OUTPUT_DIR / img_stem
        if job_dir.exists():
            mp4s = list(job_dir.glob("*.mp4"))
            if mp4s:
                found_source = mp4s[0]

        # 2. Check if the image exists and generate fresh reel if needed
        local_img_path = DOCS_DIR / img_rel
        if not found_source and local_img_path.exists():
            try:
                temp_dir = WHATSAPP_OUTPUT_DIR / f"backfill_{pid}"
                temp_dir.mkdir(parents=True, exist_ok=True)
                title = p.get("title", "Exclusive Collection")
                price = f"₹{p.get('price', 999)}"
                logger.info(f"Generating on-demand reel for product {pid}: '{title}'...")
                found_source = generate_reel(
                    image_path=local_img_path,
                    product_name=title,
                    price=price,
                    theme_name="minimal_premium",
                    output_dir=temp_dir
                )
            except Exception as e:
                logger.warning(f"Could not generate reel for {pid}: {e}")

        # 3. Compress into docs/videos/
        if found_source and Path(found_source).exists():
            success = compress_reel_for_web(Path(found_source), dest_video_path)
            if success:
                p["video"] = rel_video_path
                updated_count += 1
                logger.info(f"Attached video to product {pid}: {rel_video_path}")

    if updated_count > 0:
        PRODUCTS_JSON_PATH.write_text(json.dumps(products, indent=2, ensure_ascii=False), encoding="utf-8")
        logger.info(f"Updated {updated_count} products with videos in docs/products.json!")

        # Sync index.html DEFAULT_PRODUCTS
        idx_path = DOCS_DIR / "index.html"
        if idx_path.exists():
            idx_html = idx_path.read_text(encoding="utf-8")
            m = re.search(r'const DEFAULT_PRODUCTS\s*=\s*(\[.*?\]);', idx_html, re.DOTALL)
            if m:
                new_idx_json = json.dumps(products, indent=2, ensure_ascii=False)
                updated_idx_html = idx_html[:m.start(1)] + new_idx_json + idx_html[m.end(1):]
                idx_path.write_text(updated_idx_html, encoding="utf-8")
                logger.info("Updated DEFAULT_PRODUCTS in docs/index.html")

        # Regenerate individual SEO product pages
        try:
            from generate_product_pages import generate_all_product_pages
            generate_all_product_pages()
            logger.info("Regenerated all individual product pages with updated video links!")
        except Exception as e_gen:
            logger.warning(f"Could not regenerate product pages: {e_gen}")

if __name__ == "__main__":
    logger.info("=== STEP 1: RETRYING FAILED WHATSAPP JOBS & PUBLISHING REELS ===")
    process_failed_jobs()
    logger.info("=== STEP 2: BACKFILLING CATALOGUE REELS FOR ALL PRODUCTS ===")
    backfill_all_catalogue_videos()
    logger.info("=== FINISHED ALL REEL TASKS ===")
