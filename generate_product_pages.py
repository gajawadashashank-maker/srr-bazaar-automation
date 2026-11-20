#!/usr/bin/env python3
"""
generate_product_pages.py
Generates static SEO and Open Graph landing pages for each product in docs/products.json.
This ensures that when a product is shared on WhatsApp, Facebook, Instagram, or Telegram,
the specific product photo, title, and price are displayed in the rich preview card.
"""
from __future__ import annotations

import html
import json
from pathlib import Path
import urllib.parse

DOCS_DIR = Path("docs")
PAGES_DIR = DOCS_DIR / "p"
PRODUCTS_JSON = DOCS_DIR / "products.json"

PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} — ₹{price:,} | SRR Bazaar</title>
  <meta name="description" content="{description_meta}">

  <!-- Open Graph / WhatsApp / Facebook Preview Tags -->
  <meta property="og:type" content="product">
  <meta property="og:title" content="{title} — ₹{price:,} | SRR Bazaar">
  <meta property="og:description" content="{description_meta}">
  <meta property="og:url" content="https://srrbazaar.com/p/{id}.html">
  <meta property="og:image" content="{absolute_image}">
  <meta property="og:image:secure_url" content="{absolute_image}">
  <meta property="og:image:width" content="800">
  <meta property="og:image:height" content="800">
  <meta property="og:site_name" content="SRR Bazaar">
  <meta property="product:price:amount" content="{price}">
  <meta property="product:price:currency" content="INR">

  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{title} — ₹{price:,}">
  <meta name="twitter:description" content="{description_meta}">
  <meta name="twitter:image" content="{absolute_image}">

  <link rel="canonical" href="https://srrbazaar.com/p/{id}.html">
  <script src="https://cdn.tailwindcss.com"></script>
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;0,700;1,600&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  <script src="https://unpkg.com/lucide@latest"></script>
  <style>
    body {{ font-family: 'Plus Jakarta Sans', sans-serif; }}
    h1, h2, .font-serif {{ font-family: 'Playfair Display', serif; }}
    .gold-gradient {{ background: linear-gradient(135deg, #fce043 0%, #fb7185 100%); }}
    .maroon-bg {{ background: #4a0404; }}
  </style>
</head>
<body class="bg-stone-50 text-stone-800 antialiased min-h-screen flex flex-col justify-between">

  <!-- Header -->
  <header class="bg-white/95 backdrop-blur-md border-b border-stone-200 sticky top-0 z-30 shadow-xs">
    <div class="max-w-5xl mx-auto px-4 py-3 flex items-center justify-between">
      <div class="flex items-center gap-2.5">
        <div class="w-9 h-9 rounded-full gold-gradient p-0.5 shadow-xs">
          <div class="w-full h-full maroon-bg rounded-full flex items-center justify-center text-amber-300 font-serif font-bold text-sm">
            SR
          </div>
        </div>
        <div>
          <a href="/" class="font-serif text-lg font-bold tracking-wider text-amber-950 block hover:opacity-90 leading-tight">
            SRR BAZAAR
          </a>
          <span class="text-[10px] text-stone-500">Official Store • @sujatha60861</span>
        </div>
      </div>
      <a href="/" class="text-xs sm:text-sm font-semibold text-amber-900 bg-amber-50 hover:bg-amber-100 border border-amber-200 px-3.5 py-1.5 rounded-full transition">
        Browse Catalogue →
      </a>
    </div>
  </header>

  <!-- Product Showcase -->
  <main class="max-w-4xl mx-auto px-4 py-6 sm:py-10 flex-1 w-full">
    <div class="bg-white rounded-3xl border border-stone-200 shadow-sm overflow-hidden grid grid-cols-1 md:grid-cols-2 gap-6 sm:gap-8 p-4 sm:p-8">
      
      <!-- Product Image -->
      <div class="relative aspect-square sm:aspect-[4/5] rounded-2xl overflow-hidden bg-stone-100 border border-stone-100 shadow-inner group">
        <img src="{relative_image}" alt="{title}" class="w-full h-full object-cover">
        <span class="absolute top-3 left-3 px-2.5 py-1 rounded-full text-xs font-bold gold-gradient text-stone-900 shadow">
          {tag}
        </span>
      </div>

      <!-- Product Information -->
      <div class="flex flex-col justify-between space-y-4">
        <div class="space-y-3">
          <div class="flex items-center gap-1.5 text-xs text-amber-600 font-semibold uppercase tracking-wider">
            <span>{category}</span>
            <span>•</span>
            <span class="text-emerald-700 flex items-center gap-1">
              <i data-lucide="shield-check" class="w-3.5 h-3.5"></i> In Stock & Verified
            </span>
          </div>

          <h1 class="text-2xl sm:text-3xl font-bold text-stone-900 leading-snug">
            {title}
          </h1>

          <div class="flex items-baseline gap-3 pt-1">
            <span class="text-3xl font-black text-amber-950">₹{price:,}</span>
            <span class="text-sm text-stone-400 line-through">₹{original_price:,}</span>
            <span class="text-xs font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
              {discount_pct}% OFF
            </span>
          </div>

          <!-- Trust Badges -->
          <div class="grid grid-cols-2 gap-2 pt-2 text-[11px] sm:text-xs text-stone-600">
            <div class="flex items-center gap-1.5 p-2 bg-stone-50 rounded-xl border border-stone-200/60">
              <i data-lucide="truck" class="w-4 h-4 text-emerald-600 flex-shrink-0"></i>
              <span><strong>FREE Shipping</strong> Pan-India</span>
            </div>
            <div class="flex items-center gap-1.5 p-2 bg-stone-50 rounded-xl border border-stone-200/60">
              <i data-lucide="banknote" class="w-4 h-4 text-amber-600 flex-shrink-0"></i>
              <span><strong>COD</strong> & UPI Pay</span>
            </div>
          </div>

          <p class="text-xs sm:text-sm text-stone-600 leading-relaxed pt-2">
            {description}
          </p>
        </div>

        <!-- Action Buttons -->
        <div class="space-y-2.5 pt-4 border-t border-stone-100">
          <a href="https://srrbazaar.com/?product={id}"
             class="w-full py-3 rounded-2xl gold-gradient text-stone-950 font-bold text-sm text-center shadow-md hover:opacity-95 transition flex items-center justify-center gap-2">
            <i data-lucide="shopping-bag" class="w-4 h-4"></i>
            Buy Online on Store
          </a>

          <a href="https://wa.me/918185012453?text={wa_text}"
             target="_blank"
             class="w-full py-3 rounded-2xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-sm text-center shadow transition flex items-center justify-center gap-2">
            <i data-lucide="message-circle" class="w-4 h-4"></i>
            Order Directly via WhatsApp
          </a>

          <button onclick="shareThisProduct()"
                  class="w-full py-2.5 rounded-2xl border border-stone-300 hover:bg-stone-50 text-stone-700 font-semibold text-xs flex items-center justify-center gap-2 transition">
            <i data-lucide="share-2" class="w-3.5 h-3.5"></i>
            Share This Product
          </button>
        </div>
      </div>
    </div>
  </main>

  <!-- Footer -->
  <footer class="bg-stone-900 text-stone-400 py-6 px-4 text-center text-xs space-y-2">
    <p>© 2026 SRR Bazaar • Sujatha Collections (@sujatha60861). Free shipping pan-India.</p>
    <div class="flex items-center justify-center gap-4 text-stone-400">
      <a href="/return-policy.html" class="hover:text-amber-300 underline">Cancellation & Refund Policy</a>
      <span>•</span>
      <a href="/" class="hover:text-amber-300 underline">Storefront Home</a>
    </div>
  </footer>

  <script>
    lucide.createIcons();

    function shareThisProduct() {{
      const shareData = {{
        title: "{title_escaped} — ₹{price:,} | SRR Bazaar",
        text: "✨ Check out {title_escaped} for ₹{price:,} on SRR Bazaar! Free shipping across India.",
        url: window.location.href
      }};
      if (navigator.share) {{
        navigator.share(shareData).catch(() => {{}});
      }} else {{
        const waText = encodeURIComponent(shareData.text + "\\n\\n" + shareData.url);
        window.open("https://api.whatsapp.com/send?text=" + waText, "_blank");
      }}
    }}
  </script>
</body>
</html>
"""


def generate_all_product_pages() -> int:
    if not PRODUCTS_JSON.exists():
        print(f"Error: {PRODUCTS_JSON} not found")
        return 0

    PAGES_DIR.mkdir(parents=True, exist_ok=True)
    products = json.loads(PRODUCTS_JSON.read_text(encoding="utf-8"))

    count = 0
    for p in products:
        p_id = p.get("id")
        title = html.escape(str(p.get("title", "Designer Item")).strip())
        title_escaped = title.replace('"', '\\"')
        price = int(p.get("price", 999))
        original_price = int(p.get("originalPrice", int(price * 1.5)))
        discount_pct = int(round((1 - price / original_price) * 100)) if original_price > price else 30
        category = html.escape(str(p.get("category", "Jewellery")).capitalize())
        tag = html.escape(str(p.get("tag", "Featured")))
        description = html.escape(str(p.get("description", f"Exclusive {title} with premium finish. Free express shipping across India.")))
        description_meta = f"₹{price:,} - Free Express Shipping Pan-India & COD. {description}"[:200]

        img_rel = str(p.get("image", "images/jadau_kundan_necklace.jpg")).lstrip("/")
        absolute_image = f"https://srrbazaar.com/{img_rel}"
        relative_image = f"/{img_rel}"

        wa_order_msg = f"Hi SRR Bazaar, I would like to order *{p.get('title')}* (Price: ₹{price}). Link: https://srrbazaar.com/p/{p_id}.html"
        wa_text = urllib.parse.quote(wa_order_msg)

        page_content = PAGE_TEMPLATE.format(
            id=p_id,
            title=title,
            title_escaped=title_escaped,
            price=price,
            original_price=original_price,
            discount_pct=discount_pct,
            category=category,
            tag=tag,
            description=description,
            description_meta=description_meta,
            relative_image=relative_image,
            absolute_image=absolute_image,
            wa_text=wa_text,
        )

        out_file = PAGES_DIR / f"{p_id}.html"
        out_file.write_text(page_content, encoding="utf-8")
        count += 1

    print(f"Successfully generated {count} individual product landing pages in {PAGES_DIR}")
    return count


if __name__ == "__main__":
    generate_all_product_pages()
