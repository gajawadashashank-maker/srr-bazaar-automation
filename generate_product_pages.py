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

  <!-- Favicons -->
  <link rel="icon" type="image/png" sizes="48x48" href="https://srrbazaar.com/favicon-48x48.png">
  <link rel="icon" type="image/png" sizes="32x32" href="https://srrbazaar.com/favicon-32x32.png">
  <link rel="icon" type="image/png" sizes="192x192" href="https://srrbazaar.com/icon-192.png">
  <link rel="apple-touch-icon" sizes="180x180" href="https://srrbazaar.com/apple-touch-icon.png">
  <link rel="shortcut icon" href="https://srrbazaar.com/favicon.ico">
  <link rel="icon" href="/favicon.ico">

  <!-- Schema.org Product Structured Data for Google Rich Snippets -->
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "Product",
    "name": "{title}",
    "image": ["{absolute_image}"],
    "description": "{description_meta}",
    "sku": "SRR-{id}",
    "brand": {{
      "@type": "Brand",
      "name": "SRR Bazaar"
    }},
    "offers": {{
      "@type": "Offer",
      "url": "https://srrbazaar.com/p/{id}.html",
      "priceCurrency": "INR",
      "price": "{price}",
      "priceValidUntil": "2027-12-31",
      "itemCondition": "https://schema.org/NewCondition",
      "availability": "https://schema.org/InStock",
      "seller": {{
        "@type": "Organization",
        "name": "SRR Bazaar"
      }}
    }},
    "aggregateRating": {{
      "@type": "AggregateRating",
      "ratingValue": "4.9",
      "reviewCount": "142"
    }}
  }}
  </script>

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
      <a href="https://srrbazaar.com" class="text-xs sm:text-sm font-semibold text-stone-800 bg-stone-100 hover:bg-stone-200 border border-stone-300 px-3.5 py-1.5 rounded-full transition flex items-center gap-1">
        <i data-lucide="arrow-left" class="w-3.5 h-3.5"></i>
        <span>Back to Store</span>
      </a>
    </div>
  </header>

  <!-- Product Showcase -->
  <main class="max-w-4xl mx-auto px-4 py-4 sm:py-8 flex-1 w-full">
    <div class="mb-3">
      <a href="https://srrbazaar.com" class="inline-flex items-center gap-1.5 text-xs sm:text-sm font-semibold text-stone-600 hover:text-stone-900 transition">
        <i data-lucide="arrow-left" class="w-4 h-4"></i>
        <span>Back to Store Catalogue</span>
      </a>
    </div>
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

          <div class="p-3.5 bg-stone-50 rounded-2xl border border-stone-200/80 space-y-2">
            <h3 class="text-xs font-bold text-stone-900 uppercase tracking-wider flex items-center gap-1.5">
              <i data-lucide="info" class="w-3.5 h-3.5 text-amber-600"></i> Product Overview & Quality Details
            </h3>
            <p class="text-xs sm:text-sm text-stone-700 leading-relaxed">
              {description}
            </p>
            <ul class="text-[11px] sm:text-xs text-stone-600 space-y-1 pt-1 border-t border-stone-200/60">
              <li class="flex items-center gap-1.5">
                <i data-lucide="check" class="w-3.5 h-3.5 text-emerald-600"></i>
                <span>100% genuine quality & carefully inspected before dispatch</span>
              </li>
              <li class="flex items-center gap-1.5">
                <i data-lucide="check" class="w-3.5 h-3.5 text-emerald-600"></i>
                <span>Safe, secure packaging & pan-India tracked delivery (3-5 business days)</span>
              </li>
              <li class="flex items-center gap-1.5">
                <i data-lucide="check" class="w-3.5 h-3.5 text-emerald-600"></i>
                <span>Direct WhatsApp assistance & express door delivery across India</span>
              </li>
            </ul>
          </div>

          <!-- Official Social Channels -->
          <div class="p-3 bg-amber-50/60 rounded-2xl border border-amber-200/70 space-y-2">
            <div class="flex items-center justify-between">
              <span class="text-[11px] font-bold text-amber-950 uppercase tracking-wider flex items-center gap-1">
                <i data-lucide="sparkles" class="w-3.5 h-3.5 text-amber-600"></i> Official Channels
              </span>
              <span class="text-[10px] text-amber-800 font-semibold">@SRRBazaar</span>
            </div>
            <div class="grid grid-cols-2 gap-2 text-xs font-semibold">
              <a href="https://www.instagram.com/sujatha60861/" target="_blank"
                 class="flex items-center justify-center gap-1.5 py-2 px-3 rounded-xl bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white shadow-xs transition">
                <i data-lucide="instagram" class="w-3.5 h-3.5"></i>
                <span>@sujatha60861</span>
              </a>
              <a href="https://www.youtube.com/@SRRBazaar" target="_blank"
                 class="flex items-center justify-center gap-1.5 py-2 px-3 rounded-xl bg-red-600 hover:bg-red-700 text-white shadow-xs transition">
                <i data-lucide="youtube" class="w-3.5 h-3.5"></i>
                <span>@SRRBazaar</span>
              </a>
            </div>
          </div>

          <!-- Hashtags -->
          <div class="pt-1">
            <span class="text-[10px] font-bold text-stone-500 uppercase tracking-wider block mb-1.5">Popular Tags</span>
            <div class="flex flex-wrap gap-1.5 text-[11px]">
              {hashtags_html}
            </div>
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="space-y-2.5 pt-4 border-t border-stone-100">
          <a href="https://srrbazaar.com/?buy={id}"
             class="w-full py-3 rounded-2xl gold-gradient text-stone-950 font-bold text-sm text-center shadow-md hover:opacity-95 transition flex items-center justify-center gap-2">
            <i data-lucide="shopping-bag" class="w-4 h-4"></i>
            Buy Online & Pay (Direct Checkout)
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
  <footer class="bg-stone-900 text-stone-400 py-6 px-4 text-center text-xs space-y-3">
    <p>© 2026 SRR Bazaar • Sujatha Collections (@sujatha60861). Free shipping pan-India.</p>
    <div class="flex items-center justify-center gap-3 text-white">
      <a href="https://www.instagram.com/sujatha60861/" target="_blank"
         class="w-8 h-8 rounded-full bg-white/10 hover:bg-pink-600 flex items-center justify-center transition"
         title="Instagram @sujatha60861">
        <i data-lucide="instagram" class="w-4 h-4"></i>
      </a>
      <a href="https://www.youtube.com/@SRRBazaar" target="_blank"
         class="w-8 h-8 rounded-full bg-white/10 hover:bg-red-600 flex items-center justify-center transition"
         title="YouTube @SRRBazaar">
        <i data-lucide="youtube" class="w-4 h-4"></i>
      </a>
      <a href="https://wa.me/918185012453" target="_blank"
         class="w-8 h-8 rounded-full bg-white/10 hover:bg-emerald-600 flex items-center justify-center transition"
         title="WhatsApp Order">
        <i data-lucide="message-circle" class="w-4 h-4"></i>
      </a>
      <a href="tel:+917013416296"
         class="w-8 h-8 rounded-full bg-white/10 hover:bg-royal-600 flex items-center justify-center transition"
         title="Helpline +91 70134 16296">
        <i data-lucide="phone" class="w-4 h-4"></i>
      </a>
    </div>
    <div class="flex items-center justify-center gap-4 text-stone-400 text-[11px]">
      <a href="/return-policy.html" class="hover:text-amber-300 underline">Cancellation & Refund Policy</a>
      <span>•</span>
      <a href="/" class="hover:text-amber-300 underline">Storefront Home</a>
      <span>•</span>
      <a href="https://www.youtube.com/@SRRBazaar" target="_blank" class="hover:text-amber-300 underline">YouTube Channel</a>
      <span>•</span>
      <a href="https://www.instagram.com/sujatha60861/" target="_blank" class="hover:text-amber-300 underline">Instagram Profile</a>
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

        cat_lower = str(p.get("category", "")).lower()
        t_lower = title.lower()
        tags_list = ["#SRRBazaar", "#SujathaCollections"]
        if "saree" in cat_lower or "saree" in t_lower:
            tags_list.extend(["#Sarees", "#KhadiCotton", "#SilkSarees", "#EthnicWear"])
        elif any(k in cat_lower or k in t_lower for k in ["jewel", "necklace", "earring", "mangalsutra", "haram", "chain", "bangle"]):
            tags_list.extend(["#FashionJewellery", "#KundanJewellery", "#BridalJewellery", "#TraditionalJewellery"])
        elif any(k in cat_lower or k in t_lower for k in ["cleaning", "bleach", "acid", "phenyl"]):
            tags_list.extend(["#HouseholdSupplies", "#CleaningEssentials", "#BazaarDeals"])
        elif any(k in cat_lower or k in t_lower for k in ["samagri", "decor", "pooja", "wick", "vattulu", "diya"]):
            tags_list.extend(["#PoojaSamagri", "#HomeDecor", "#FestiveEssentials"])
        elif any(k in cat_lower or k in t_lower for k in ["disposable", "plate", "cup", "buffet"]):
            tags_list.extend(["#BuffetPlates", "#EcoFriendly", "#PartySupplies"])
        else:
            tags_list.extend(["#ShoppingIndia", "#TrendingDeals", "#PanIndiaShipping"])
        tags_list.extend(["#COD", "#FreeShipping", "#OnlineShoppingIndia"])

        hashtags_html = "".join(
            f'<span class="bg-stone-100 text-stone-700 px-2 py-0.5 rounded-md border border-stone-200/60 font-medium">{t}</span>'
            for t in tags_list
        )

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
            hashtags_html=hashtags_html,
        )

        out_file = PAGES_DIR / f"{p_id}.html"
        out_file.write_text(page_content, encoding="utf-8")
        count += 1

    print(f"Successfully generated {count} individual product landing pages in {PAGES_DIR}")
    return count


if __name__ == "__main__":
    generate_all_product_pages()
