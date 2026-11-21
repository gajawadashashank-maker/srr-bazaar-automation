# MASTER PROMPT: The Modern High-Converting Quick-Commerce Storefront Blueprint

> **How to use this prompt:**
> Copy and paste this complete specification prompt into any AI agent (or give to any senior engineering team) when starting a new e-commerce storefront project for any domain (Jewellery, Fashion, D2C, Grocery, Pooja, Electronics, or Artisanal Products). It encapsulates all architectural, design, mobile UX, SEO, and automation lessons learned.

---

## 📋 The Master Prompt (Copy Below)

```markdown
You are an expert Principal Full-Stack Engineer and Elite E-Commerce Product Designer.
Your task is to build a modern, high-converting, mobile-first e-commerce storefront inspired by the best conversion patterns of Blinkit, Amazon, Meesho, and Myntra.

### 1. CORE DESIGN PHILOSOPHY & BRANDING
- **Visual Aesthetic**: Premium, clean, and trustworthy.
- **Color Palette**: 
  - Primary / Background: Warm luxury tones (e.g., Deep Maroon `#380612` / Gold gradients `linear-gradient(135deg, #d49b18 0%, #fbd46c 50%, #b87c0f 100%)` for luxury/heritage; or Emerald/Slate for modern tech/grocery).
  - Accent / Trust: Emerald green (`#059669`) for Free Shipping badges, stock availability, and verified buyer badges.
  - CTAs: Amazon-standard high-converting CTA buttons:
    - "Add to Cart": `#ffd814` (border `#fcd200`, text `#0f1111`, bold).
    - "Buy Now / Checkout": `#ffa41c` (border `#ff8f00`, text `#0f1111`, bold).
- **Typography**: 
  - Brand & Titles: Elegant Editorial Serif (e.g., `Cinzel`, `Playfair Display`).
  - Interface & Body: Ultra-clean modern sans-serif (e.g., `Plus Jakarta Sans`, `Inter`).

---

### 2. MOBILE-FIRST NAVIGATION & CATEGORY ARCHITECTURE (Blinkit-Style)
- **Problem Solved**: On mobile web, traditional horizontal single-row category carousels hide 70% of categories off-screen because users rarely scroll horizontally.
- **Implementation**:
  - Implement a **4-Column Responsive Category Grid** on mobile viewports (`grid grid-cols-4 gap-2.5 sm:gap-4`).
  - Each category tile consists of:
    1. A circular or rounded-2xl studio photograph / icon.
    2. A crisp category title underneath with item counts (e.g., "Necklaces (23)").
    3. An active gold/brand border indicator when selected.
  - Smooth client-side category filtering with instantaneous DOM transitions and zero page reloads.

---

### 3. SHOPPING CART, TOAST & CHECKOUT SPEED (Amazon Pattern)
- **1-Tap Add to Cart**:
  - When clicking "Add to Cart" on any product card, the button immediately transforms into a green checkmark `✓ Added` for 2 seconds.
  - Floating top toast notification slides down:
    - Displays thumbnail, item title, "Added to Cart", and a direct "View Cart" CTA.
    - Auto-dismisses after 4 seconds or on user interaction.
- **Slide-In Mini-Cart Drawer (`#cartDrawer`)**:
  - Full-height slide-over drawer from the right edge with a frosted glass backdrop overlay (`bg-black/50 backdrop-blur-xs`).
  - Features:
    - Free Shipping progress banner (`Congratulations! You get FREE Express Delivery`).
    - Dynamic coupon code engine with instant discount recalculation (e.g. `WELCOME100` = ₹100 OFF).
    - Quantity increment/decrement buttons (`-`, `+`) with live subtotal/tax/discount calculation.
    - Prominent gold "Proceed to Order & Pay" button.

---

### 4. CRITICAL MOBILE HARDWARE & GESTURE BACK-BUTTON MANAGER
- **The Problem**: On mobile browsers (Android Chrome, iOS Safari), whenever a shopper opens a drawer, image modal, or checkout sheet, they tap the **phone's hardware Back button** or use the **swipe-back gesture** to close it. If unhandled, the browser navigates back to the previous website (e.g. Google or Instagram), losing the customer!
- **Mandatory Solution (Unified Modal & History Stack)**:
  1. **Baseline State**: Initialize `window.history.replaceState({ srrBase: true }, '')` on page load.
  2. **Push State on Open**: Every time ANY drawer or modal opens (`cartDrawer`, `quickViewModal`, `checkoutModal`, `trackingModal`, `policyModal`), execute:
     ```javascript
     window.history.pushState({ srrModal: modalId }, '');
     ```
  3. **Trapping `popstate`**:
     ```javascript
     window.addEventListener('popstate', (e) => {
       const priority = ['checkoutModal', 'trackingModal', 'policyModal', 'cartDrawer', 'quickViewModal'];
       for (const id of priority) {
         const el = document.getElementById(id);
         if (el && !el.classList.contains('hidden')) {
           el.classList.add('hidden'); // Close modal cleanly without leaving site!
           return;
         }
       }
     });
     ```
  4. **Backdrop & Escape Key**:
     - Clicking the backdrop overlay outside any modal closes it safely.
     - Pressing the keyboard `Escape` key dismisses the top-most modal.

---

### 5. DEDICATED PRODUCT VIDEO REELS (Myntra / Meesho Pattern)
- **Problem Solved**: Customers hesitate to buy physical luxury or craft goods from static photos alone. Short video clips show real sparkle, drape, and physical dimensions.
- **Rules**:
  1. **Zero Mismatched Videos**: NEVER play a generic or wrong video on a product.
  2. **Dedicated Reel Mapping**: If a product has a video, set `video: "videos/reel_<id>.mp4"`.
  3. **Conditional Rendering in Quick View**:
     - If `product.video` exists: Render the `[📸 Photo] / [🎬 Video Reel]` toggle pill and autoplay/loop the matching reel.
     - If `product.video` is null: DO NOT render any video button or player. Render only the verified high-res photograph with a `100% Artisanal Quality` badge.
  4. **Fast-Streaming Mobile Optimization**: All reels MUST be compressed via FFmpeg:
     `ffmpeg -i input.mp4 -vf "scale=540:-2" -c:v libx264 -crf 26 -preset fast -movflags +faststart output.mp4`
     Target file size: **~850 KB – 1.2 MB** so it streams instantly on mobile without buffering.

---

### 6. "FREQUENTLY BOUGHT TOGETHER" COMBO BUNDLES
- **Purpose**: Increase Average Order Value (AOV).
- **Implementation**:
  - Hand-curated 2-piece and 3-piece combo kits placed prominently on the homepage (e.g. Bridal Duo, Festive Pooja Kit).
  - Explicit visual equation: `[Photo 1] + [Photo 2] = [Bundle Price]`.
  - Displays original MRP struck out, discounted package price, and green badge `Save ₹XYZ`.
  - Clicking "Add Combo to Cart" adds the bundled package as a single item with bundle pricing and savings badge in the cart drawer.

---

### 7. SOCIAL PROOF & VERIFIED CUSTOMER REVIEWS
- Include a dedicated section: **"Real Customer Reviews & WhatsApp Unboxing"**.
- Feature real buyer testimonials with:
  - Verified Buyer Badge (`✓ Verified Order`).
  - Star rating (`5.0 ★`).
  - Real customer quote highlighting fast delivery, packaging quality, and finish.
  - Delivery dispatch stamp (`Dispatched via The Professional Couriers`).
- Summary Trust Scoreboard: `4.9 / 5.0 Rating` | `4,800+ Happy Customers` | `0 Breakage Guarantee`.

---

### 8. LIVE PARCEL TRACKING SCREEN (`/track`)
- Header and footer link to an instant **Live Order Tracking Modal**.
- Customer inputs their **Order ID** (e.g. `SRR-2026-XXXX`) or **10-Digit Mobile Number**.
- Displays an interactive 4-step delivery progress timeline:
  1. `Order Confirmed & Quality Checked`
  2. `Securely Packed with Multi-Layer Bubble Wrap`
  3. `Dispatched via The Professional Couriers (Armoor Hub)`
  4. `In Transit / Out for Delivery`
- Includes a direct 1-tap button: **"Instant Dispatch Query on WhatsApp"** opening a pre-filled WhatsApp chat with the seller.

---

### 9. GOOGLE SEARCH SEO, FAVICONS & RICH SNIPPETS (Schema.org JSON-LD)
- **Problem Solved**: Default websites show a generic globe `🌐` icon in Google without star ratings, prices, sitelinks, or logos, or show outdated cached previews for weeks.
- **Mandatory Requirements Across Homepage AND All Product Pages (`/p/<id>.html`)**:
  1. **Square Multiples of 48px Favicons (Strict Googlebot Standard)**:
     - `favicon-48x48.png`, `favicon-32x32.png`, `icon-192.png`, `icon-512.png`, `apple-touch-icon.png`, and `favicon.ico`.
     - Explicit `<link rel="icon" type="image/png" sizes="48x48" href="...">` and `<link rel="shortcut icon" href="...">` must be embedded in the `<head>` of **every single HTML page**, not just the homepage.
  2. **Schema.org Structured Data (`application/ld+json`)**:
     - **Homepage**:
       - `WebSite` with `SearchAction` (enables Google sitelinks searchbox).
       - `OnlineStore` / `Organization` with official `logo`, `name`, `telephone`, `address`, and `aggregateRating` (e.g. 4.9 ★ across 4,800 reviews).
       - `ItemList` of top featured products with individual prices in INR, `InStock` availability, and review ratings.
     - **Every Product Landing Page (`/p/<id>.html`)**:
       - Standalone `Product` Schema with `sku`, `name`, `image`, `description`, `offers` (price in INR, `InStock`), and `aggregateRating`.
  3. **Google Image Sitemap (`sitemap.xml`)**:
     - Must include `<image:image>` tags with `<image:loc>`, `<image:title>`, and `<image:caption>` for all flagship products and logo.
  4. **Google Search Console (GSC) Expedited Indexing Protocol**:
     - Googlebot-Image crawls favicons independently and may show the generic globe `🌐` for 7–14 days if left alone.
     - To force Google to update the logo and rich snippets within **24–48 hours**:
       - In Google Search Console, inspect `https://<domain>` and click **"Request Indexing"**.
       - Submit `/sitemap.xml` under the Sitemaps tab.

---

### 10. MULTI-PAYMENT & WHATSAPP CHECKOUT ENGINE
- Support multi-payment options:
  - **UPI QR & Deep Links**: Dynamic QR generation with payee VPA, payee name, and exact order total encoded in UPI URI format.
  - **Cash on Delivery (COD)**: With verification notice.
  - **Razorpay Online Card / NetBanking**: Fully integrated checkout SDK.
- **Automated WhatsApp Order Dispatch**:
  - Immediately upon order placement, formats an itemized WhatsApp receipt and opens `https://wa.me/<SellerNumber>?text=<ItemizedReceipt>`.
  - Clears cart, displays order success modal, and stores the order in `localStorage` and merchant dashboard.

---

### 11. REGULATORY & PAYMENT AGGREGATOR COMPLIANCE
- Include fully accessible modal popups for store policies in footer:
  - Privacy Policy
  - Terms & Conditions
  - Shipping & Delivery Policy (with transit SLA: 24-48h dispatch, 3-5 days delivery)
  - Cancellation & 7-Day Refund Policy (with unboxing video guideline)
  - Contact Us page (legal entity name, physical address, support phone, and support email).

---

### 12. AUTOMATED NEW PRODUCT PIPELINE & SMART FALLBACK PARSER
- **Problem Solved**: When sellers forward photos on WhatsApp, they often include NO caption or ONLY a price number (e.g., `1200` or `₹699 fs`). Hard validation halts the pipeline, parking the post in "needs review" indefinitely.
- **Mandatory 2-Stage Extraction Hierarchy**:
  1. **Stage 1 (Real Text Parsing)**:
     - Ignore standalone price lines (`1300 rs`, `₹699`, `fs`, `free shipping`).
     - Extract the first descriptive text line as the authentic product name.
  2. **Stage 2 (Intelligent Price-Tier Fallback)**:
     - If the caption has NO descriptive words (or is 100% blank), DO NOT halt or pause for review. Automatically assign an authentic collection name based on the detected price tier:
       - **≥ ₹1,200**: `"Premium Bridal Pure Jadau Kundan Collection"`
       - **₹750 – ₹1,199**: `"Festive Handcrafted Traditional Collection"`
       - **₹400 – ₹749**: `"Handcrafted Designer Jewellery Collection"`
       - **Under ₹400**: `"<StoreName> Curated Collection"`
  3. **Auto-Generate & Sync**:
     - Automatically compress the video reel using FFmpeg (`scale=540:-2`, `crf 26`, `+faststart`).
     - Prepend the new product into `products.json` and storefront fallback array.
     - Auto-generate the dedicated SEO landing page `/p/<id>.html` with complete favicons and Schema.org `Product` markup.

---

### 13. FULL-FUNNEL PAID ADVERTISING & MARKETING SPECIFICATION
- **Tracking & Pixel Infrastructure**:
  - Install Meta Pixel & Conversions API (CAPI) with standard events (`PageView`, `ViewContent`, `AddToCart`, `InitiateCheckout`, `Purchase` with dynamic `value` and `currency: "INR"`).
  - Verify event firing via Meta Pixel Helper Chrome extension.
- **Click-to-WhatsApp (CTWA) Ad Funnel**:
  - For high-ticket items (₹1,000+), run Instagram/Facebook Reels ads with a **"Send WhatsApp Message"** CTA.
  - Pre-fill WhatsApp greeting: *"Hi, I want to order [Product Name] (₹[Price]). Is COD available to my pincode?"*
  - Establish a < 5 minute response SLA with automated greeting flows and address intake templates.
- **Creative Standard (9:16 Vertical Video Reels)**:
  - 3-second visual hook (macro close-up of sparkle, stone cut, or unboxing).
  - On-screen bold subtitle overlays (since 80% of mobile users watch on mute).
  - Slashing MRP price anchoring (*"Worth ₹1,650, Launch Offer ₹1,300 with Free Express Delivery"*).
- **Abandoned Cart Follow-Up**:
  - Automatically capture phone number on step 1 of checkout.
  - Fire an automated WhatsApp recovery ping within 30 minutes with a one-tap direct checkout link.
```
