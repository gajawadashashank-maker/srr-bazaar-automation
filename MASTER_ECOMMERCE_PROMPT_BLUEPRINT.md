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

### 9. GOOGLE SEARCH SEO & RICH SNIPPETS (Schema.org JSON-LD)
- **Problem Solved**: Default websites show a generic globe `🌐` icon in Google without star ratings, prices, or sitelinks.
- **Mandatory Head Requirements**:
  1. **Square Multiples of 48px Favicons**:
     - `favicon-48x48.png`, `favicon-32x32.png`, `icon-192.png`, `icon-512.png`, `apple-touch-icon.png`, and `favicon.ico`.
     - Explicit `<link rel="icon" type="image/png" sizes="48x48" href="...">`.
  2. **Schema.org Structured Data (`application/ld+json`)**:
     - `WebSite` with `SearchAction` (enables Google sitelinks searchbox).
     - `OnlineStore` / `Organization` with official `logo`, `name`, `telephone`, `address`, and `aggregateRating` (e.g. 4.9 ★ across 4,800 reviews).
     - `ItemList` of top featured `Product` items with individual prices in INR, `InStock` availability, and review ratings.
  3. **Google Image Sitemap (`sitemap.xml`)**:
     - Must include `<image:image>` tags with `<image:loc>`, `<image:title>`, and `<image:caption>` for all flagship products and logo.

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

### 12. AUTOMATED NEW PRODUCT PIPELINE
- When new photos are uploaded via WhatsApp or script:
  1. Auto-detect category using keyword heuristic (jewellery, sarees, decor, groceries, dry fruits, snacks, disposables, samagri).
  2. Generate and compress matching reel using FFmpeg.
  3. Prepend the new product with its matching video path into `products.json` and storefront fallback.
  4. Auto-generate the individual SEO page `/p/<id>.html`.

---

### 13. MULTI-LEVEL MODAL STACK & THE CART-TO-CHECKOUT NAVIGATION CONTRACT
- **The Critical Trap**:
  - When a customer adds items to their Cart Drawer and clicks **"Proceed to Order & Pay"**, the Address / Checkout modal opens.
  - If the customer clicks the **"X" close button**, the top **Back arrow**, the bottom **"Back to Shopping Cart" button**, the **keyboard Escape key**, or the **mobile browser swipe-back gesture**, a naive implementation hides the checkout modal and dumps the user onto the Home page with everything closed! The customer gets frustrated and thinks their cart was erased.
- **The Mandatory Solution**:
  1. **Source State Tracking (`checkoutOpenedFrom`)**:
     - When `proceedToCheckout()` is invoked, check if `#cartDrawer` is currently open or in the history stack:
       `checkoutOpenedFrom = 'cartDrawer';`
     - Cleanly hide the Cart Drawer DOM without destroying the history stack: `toggleCartDrawer(false, false);`.
     - Push the checkout state: `pushModalHistory('checkoutModal');`.
  2. **Multi-Exit Return Guarantee**:
     - In `closeCheckout()`, check `if (checkoutOpenedFrom === 'cartDrawer')`:
       Immediately reopen the Cart Drawer: `toggleCartDrawer(true, false);` with all items and quantities intact!
     - Add 3 explicit visual escape hatches on the Checkout modal:
       a) Top-Left: `<button onclick="closeCheckout()" title="Back to Shopping Cart"><i data-lucide="arrow-left"></i></button>`
       b) Top-Right: `<button onclick="closeCheckout()" title="Close Checkout"><i data-lucide="x"></i></button>`
       c) Bottom (under Confirm Order): `<button onclick="closeCheckout()">← Back to Shopping Cart</button>`
  3. **Browser `popstate` Back-Gesture Interceptor**:
     ```javascript
     window.addEventListener('popstate', (e) => {
       const checkoutEl = document.getElementById('checkoutModal');
       if (checkoutEl && !checkoutEl.classList.contains('hidden')) {
         const hadCart = (checkoutOpenedFrom === 'cartDrawer' || srrModalHistory.includes('cartDrawer'));
         checkoutOpenedFrom = null;
         hideModalDOM('checkoutModal');
         const idx = srrModalHistory.lastIndexOf('checkoutModal');
         if (idx !== -1) srrModalHistory.splice(idx, 1);
         if (hadCart) {
           toggleCartDrawer(true, false); // Reopens cart drawer seamlessly!
           return;
         }
       }
     });
     ```
  4. **Post-Order Cart Clear**:
     - ONLY when the order is successfully placed (`submitFinalOrder()`), clear `checkoutOpenedFrom = null;`, empty the cart, close checkout, and open `#orderSuccessModal`. When the user closes the success modal, they return to the clean homepage.

---

### 14. AMAZON-GRADE ROBUST SEARCH: FUZZY TYPO-TOLERANCE & REGIONAL STEMMING
- **The Critical Trap**:
  - Strict substring matching (`title.toLowerCase().includes(query)`) fails completely when users:
    - Type with spaces or missing spaces (e.g. `edu kondala` vs `edukondala`).
    - Type regional spelling variations / typos (e.g. `edukondalu` ending in `u` instead of `a`).
    - Use phonetic transliterations common in India.
  - The store shows "No products found" even though the exact product is in stock!
- **The Mandatory Solution**:
  1. **Real-time Live Recommendation Dropdown (`#searchDropdown`)**:
     - **On Focus (Empty Input)**: Display "Trending Searches" and popular quick-picks (e.g. 🌾 Edu Kondala Nomu, 🪔 33 Diya Stand, 🍃 Leaf Buffet Plates, 👑 Kundan Sets).
     - **On Typing**: Display instant matching suggestions with thumbnail icons, categories, and prices.
     - **Keyboard Navigation**: Pressing `ArrowDown` / `ArrowUp` navigates suggestions; `Enter` commits search; `Escape` closes dropdown.
  2. **Levenshtein Distance & Sliding-Window Fuzzy Matching**:
     - Allow up to **2 character typos** for word lengths $\ge 5$ (e.g., `edukondalu` $\rightarrow$ `edu kondala`, `kundan` $\rightarrow$ `kundan`).
  3. **Indian Regional Language Inflection Stemmer (`getWordStems`)**:
     - Strip common Telugu/Hindi noun declensions and plural suffixes (`lu`, `alu`, `am`, `ya`, `galu`) before matching:
       `edukondalu` $\rightarrow$ stem `edukonda` $\rightarrow$ matches `Edu Kondala Nomu`!
  4. **Two-Tier Search Results (Direct Matches + Related Products)**:
     - When direct query matches are $< 4$, never show an empty screen or sparse grid.
     - Display:
       `Direct Matches (N)`: High-confidence keyword matches.
       `Related Products (M)`: Same category or complementary items with "You May Also Like" styling.
     - When typos are auto-corrected, render an Amazon-style headline:
       *Showing results for "**Edu Kondala Nomu**". Search instead for "edukondalu"?*

---

### 15. AI CONCIERGE & STYLIST ENGINE (HYBRID CLIENT-BACKEND ARCHITECTURE)
- **The Critical Trap**:
  - Relying solely on a backend API endpoint (e.g., `/api/ai-stylist`) breaks completely on static CDNs or GitHub Pages because no Python server is running there.
  - Using complex reasoning models (like `gpt-oss-20b`) burns through token limits on hidden reasoning tokens, returning empty responses.
  - Using default `urllib` HTTP headers results in HTTP 403 Forbidden on Groq/Cloudflare endpoints.
- **The Mandatory Solution**:
  1. **Hybrid Architecture (Graceful Fallback)**:
     - Try `POST /api/ai-stylist` with a 4-second timeout.
     - If the fetch fails (network down or static hosting on GitHub Pages), catch the exception and immediately invoke the client-side JavaScript knowledge engine `generateClientAiResponse(query)` using live `products.json` and client-side fuzzy search!
     - Zero disruption to the customer!
  2. **Model Selection for E-Commerce Shopping**:
     - Use fast, direct multilingual conversational models: `qwen/qwen3.8-27b` on Groq LPU (< 200ms response time).
     - Always provide custom headers: `headers = {"User-Agent": "Storefront-AI/1.0", "Authorization": f"Bearer {key}"}`.
  3. **Catalog Injection & Product ID Tagging**:
     - Prompt includes store catalog summary (top 40 items with IDs, categories, prices in ₹).
     - Instruct AI to append `[PRODUCTS: id1, id2]` at the end of its response.
     - Frontend regex parses `[PRODUCTS: ...]` and dynamically renders interactive product cards with photo, price, "View in Quick View", and direct WhatsApp buy buttons right inside the chat bubble!
  4. **Starter Chips & Floating Widget**:
     - Include quick starter chips (e.g., "🌾 Sankranti Pooja Nomu", "👑 Bridal Kundan Sets", "✨ Sarees Under ₹1,500", "📦 Track My Order").
     - Floating bottom-right button with pulse animation and mobile drawer view.

---

### 16. DUAL-CHANNEL WHATSAPP CLOUD API: ADMIN AUTOMATION VS CUSTOMER SUPPORT
- **The Critical Trap**:
  - Webhooks built for admin video automation typically reject all incoming text messages (`if msg_type not in ('image', 'video'): continue`) and block all phone numbers except admin numbers.
  - Customers messaging the WhatsApp Business number receive zero response.
- **The Mandatory Solution (Dual-Route Webhook in `app.py`)**:
  1. **Route A: Admin Media Post (`msg_type in ('image', 'video')`)**:
     - Verify sender against `WHATSAPP_ALLOWED_SENDERS`.
     - Parse product title, price, and description from caption.
     - Generate 4 video reels via FFmpeg, upload selected reel to Cloudinary, publish to Instagram Reels and YouTube Shorts, and auto-sync to `docs/products.json`.
  2. **Route B: Customer Text Inquiries (`msg_type in ('text', 'interactive')`)**:
     - Accept from **ANY customer phone number**.
     - Extract customer question (`message['text']['body']`).
     - Query Groq AI Stylist with full store catalog, cash on delivery terms, and **The Professional Couriers (Armoor Hub)** tracking link (`https://www.tpcindia.com/`).
     - Reply directly to customer's WhatsApp via Meta Cloud API:
       `POST https://graph.facebook.com/v27.0/{PHONE_NUMBER_ID}/messages`
       Payload: `{"messaging_product": "whatsapp", "to": sender, "text": {"preview_url": true, "body": reply}}`.
  3. **Idempotency & Deduplication**:
     - Ingest message IDs into SQLite (`whatsapp_jobs`) before processing to prevent duplicate replies on Meta webhook retries.

---

### 17. FREQUENTLY BOUGHT TOGETHER (COMBO BUNDLES) DATA INTEGRITY
- **The Critical Trap**:
  - Adding combo kits to the cart as separate disconnected items causes the cart to re-charge full individual prices, dropping the bundle discount.
  - Storing combo cards with hardcoded dummy videos causes unrelated jewellery videos to play on pooja trays.
- **The Mandatory Solution**:
  1. **Atomic Bundle Entry**:
     - Add combos with unique bundle ID (e.g., `bundle_festive_duo`), title, combined original MRP, discounted combo price, and `isBundle: true`.
     - Render bundle items inside Cart Drawer and Checkout with an explicit green badge: `🎁 Combo Package (Save ₹XYZ)`.
  2. **Strict Video Association**:
     - A video reel must ONLY be associated with a product or combo if the video file actually depicts that specific item.
     - If no matching video reel exists, render ONLY the verified high-resolution photograph. NEVER show a dummy or placeholder video.

---

### 18. PREVENTING REPEATED ARCHITECTURAL MISTAKES (THE "DON'T DO THIS" CHECKLIST)
| Component | Common Mistake / Bug Encountered | Mandatory Correct Pattern |
| :--- | :--- | :--- |
| **Checkout Close** | Closing checkout drops customer on Home page | Close handler MUST check `checkoutOpenedFrom` and reopen Cart Drawer |
| **Checkout Back Navigation** | Browser Back on Address form exits the site | Intercept `popstate`: if checkout is open, close checkout and restore Cart Drawer |
| **Search Matching** | Exact character-by-character substring search | Multi-word tokenization + Levenshtein distance $\le 2$ + Regional word stemmer |
| **Search Dropdown** | Dropdown stays open after clicking outside | Auto-dismiss on click-outside, Escape key, or product selection |
| **Video Reels** | Reusing a generic reel for all products | Strict 1-to-1 mapping; omit video toggle when video is missing |
| **Promo Carousel** | Auto-scroll timer jerks carousel during manual swipe | Pause auto-scroll on `touchstart` / `mouseenter`; resume after 6s idle |
| **WhatsApp Webhook** | Ignoring customer text messages | Dual-path routing: Media $\rightarrow$ Admin Publisher; Text $\rightarrow$ Groq AI Auto-Reply |
| **Groq LLM Calls** | Using reasoning models (`gpt-oss`) with low token limits | Use conversational fast model (`qwen/qwen3.8-27b`) with custom `User-Agent` |
| **Static Hosting AI** | Fetching `/api/ai-stylist` and throwing uncaught error | Wrap in try/catch and fallback immediately to client-side catalog search |
| **Google Search SEO** | Missing 48px square favicons causing globe 🌐 icon | Provide `favicon-48x48.png` + Schema.org `OnlineStore` + `sitemap.xml` with images |
| **Mobile Viewport Overflow** | Swiping horizontally drags document left, revealing a full-height white/blank empty margin | Lock `html, body` with `overflow-x: hidden !important; overscroll-behavior-x: none;`, budget mobile header width $\le 350$px, and wrap flex scrolls in `overflow-hidden` |
```

---

### 19. MOBILE HORIZONTAL VIEWPORT CONTAINMENT & TOUCH GESTURE LOCK
- **The Core Problem**:
  - On mobile touchscreens, users frequently make diagonal or accidental horizontal thumb swipes while scrolling vertically.
  - If any container, badge, or header row exceeds viewport width by even $1$ pixel, or if standard `overflow-x: hidden` is only on `<body>`, mobile browsers (WebKit on iOS Safari / Blink on Chrome Android) will rubber-band pan the entire document left, exposing an ugly full-height blank white strip along the right side.
- **The Mandatory Solution**:
  1. **Root-Level Viewport Hard Lock**:
     ```css
     html, body {
       width: 100%;
       max-width: 100vw;
       overflow-x: hidden !important;
       position: relative;
       overscroll-behavior-x: none;
       -webkit-overflow-scrolling: touch;
     }
     * {
       box-sizing: border-box;
     }
     ```
  2. **Mobile Header Pixel Budget ($360$px Screen Target)**:
     - Always test against a minimum screen width of $360$px (Samsung Galaxy A-series, older iPhones).
     - Never cram redundant action buttons in the top header. If an inline search bar exists right under the header on mobile, HIDE the header magnifying glass icon on mobile (`hidden sm:flex`).
     - Reduce horizontal padding on mobile (`px-2 sm:px-6`).
     - Constrain brand name with `min-w-0 flex-shrink-1` and responsive font size (`text-base sm:text-2xl`).
     - Avoid negative pixel offsets for notification badges that stick out past screen bounds (use `top-0 right-0` instead of `-top-1 -right-1`).
  3. **Horizontal Carousel Scroll Containment**:
     - Any container with `whitespace-nowrap overflow-x-auto` (e.g. Trust Badges, Category Chips) MUST be wrapped in a parent with `w-full max-w-full overflow-hidden`.
     - Add `overscroll-x-contain` to the scrollable flex row so scrolling to the end of the badge list stops cleanly without bubbling up to document-level panning.
  4. **Full-Width Section Bounding**:
     - Apply `w-full max-w-full overflow-hidden` to all major structural sections (`<nav>`, `#catalogue`, `#comboBundlesSection`, `#reviewsProofSection`, `<footer>`).


---

## 🛠️ Field Log: Mistakes Made, What Was Tweaked & Why (Developer Reference)

This log documents every architectural pitfall discovered and resolved during real-world customer testing of this storefront. Reference this whenever building your next storefront to avoid repeating these mistakes:

### 1. The Cart-to-Checkout "Home Dump" Bug
- **What Happened**: User clicked "Proceed to Pay" from their cart drawer. The address modal opened. When they clicked the "X" button or used the phone's swipe-back gesture to adjust their cart, the entire store closed and returned them to the home page with everything shut.
- **Why It Happened**: `proceedToCheckout()` hid the cart drawer DOM (`toggleCartDrawer(false, false)`). When `closeCheckout()` ran, it only knew how to hide the checkout modal; it had no state tracking of where the user came from.
- **How to Avoid**: Always declare a navigation state variable `let checkoutOpenedFrom = null;`. Whenever checkout opens from the cart, set `checkoutOpenedFrom = 'cartDrawer'`. In both `closeCheckout()` and `window.onpopstate`, if `checkoutOpenedFrom === 'cartDrawer'`, ALWAYS invoke `toggleCartDrawer(true, false)` to bring the user back to their cart with all selected items intact.

### 2. Character-to-Character Search Failure (Typo & Telugu Inflections)
- **What Happened**: Searching for `edu kondala` or `edukondalu` showed 0 results even though "Edu Kondala Nomu" was a top seller.
- **Why It Happened**: Simple JavaScript `.includes()` checks exact character substring. Missing spaces (`edukondala`) or regional suffixes (`-lu`, `-alu`) caused a complete string mismatch.
- **How to Avoid**:
  1. Tokenize query by whitespace and normalize punctuation.
  2. Implement a regional word stemmer (`getWordStems`) that trims Telugu/Hindi noun endings (`lu`, `alu`, `am`, `ya`).
  3. Run Levenshtein distance check ($\le 2$ edits) for words $\ge 5$ chars.
  4. Always render a "Trending Searches" recommendation dropdown on search bar focus so shoppers can tap popular items without typing.

### 3. Fake / Mismatched Video Reels on Unrelated Items
- **What Happened**: Quick View modal played a Kundan choker necklace video on a brass Swan Pooja Tray.
- **Why It Happened**: The code fell back to a default video when `product.video` was undefined.
- **How to Avoid**: Enforce strict 1-to-1 video binding. If `product.video` is not explicitly set or confirmed for that exact product ID, DO NOT display the `[🎬 Video Reel]` pill. Display only the studio photograph with an Artisanal Quality guarantee badge.

### 4. WhatsApp Webhook Rejecting Customer Messages
- **What Happened**: Business WhatsApp number was set up for automated Instagram reel generation from images. When customers sent questions like "Price of 33 Diya Stand?" or "Where is my order?", the server dropped them with `if msg_type not in ('image', 'video'): continue`.
- **Why It Happened**: The webhook was originally built exclusively as an admin publisher tool, not a customer concierge.
- **How to Avoid**: Implement dual-channel routing in the webhook:
  - If `image`/`video` AND sender is in `WHATSAPP_ALLOWED_SENDERS`: Route to Reel Publisher.
  - If `text` from ANY sender: Route to Groq AI Shopping Concierge (`ask_groq_stylist`), format with store links and courier partner info (The Professional Couriers Armoor Hub), and send an immediate direct reply via Meta Cloud API.

### 5. AI Assistant Crashing on Static GitHub Pages
- **What Happened**: AI Stylist chat threw a console fetch error on GitHub Pages because there was no live FastAPI backend running on the static CDN.
- **Why It Happened**: The frontend only had `fetch('/api/ai-stylist')`.
- **How to Avoid**: Always build a hybrid AI engine: wrap the backend fetch in a timeout/catch block, and immediately fall back to a rich client-side search engine (`generateClientAiResponse`) that searches the local catalog and formats response cards with direct WhatsApp buy links.

### 6. Google Search Showing Globe 🌐 Instead of Brand Logo
- **What Happened**: Google search results displayed a generic globe `🌐` favicon.
- **Why It Happened**: Google Search Console mandates a square favicon that is a multiple of 48px (e.g. 48x48, 96x96, 192x192) declared in a `<link rel="icon" type="image/png" sizes="48x48" ...>` tag. A simple 16x16 or 32x32 favicon is ignored by Google's crawler.
- **How to Avoid**: Generate explicit `favicon-48x48.png` and `icon-192.png`, reference them with explicit sizes in `<head>`, and submit `sitemap.xml` containing image metadata `<image:image>`.

### 7. The Mobile "Swipe Left Blank Column" Viewport Overflow Bug
- **What Happened**: When testing on mobile touch devices (Chrome Android / iOS Safari), swiping or dragging slightly left caused the whole page to pan sideways, exposing a full-height blank white empty column on the right edge.
- **Why It Happened**:
  1. Setting `overflow-x: hidden` on `<body>` alone is insufficient on mobile touch devices; mobile browser gesture engines (WebKit/Blink) allow horizontal drag bouncing on `<html>`.
  2. The mobile header row exceeded the $360$px pixel budget: container padding (`px-3` = $24$px) + logo ($185$px) + 4 action buttons ($214$px) = $423$px > $360$px.
  3. The shopping cart notification badge had `-right-0.5` which peeked $2$px outside the screen boundary.
  4. Horizontally scrolling flex containers (`whitespace-nowrap overflow-x-auto` like Trust Badges) chain gesture events up to the parent document without scroll chaining containment.
- **How to Avoid**:
  1. Add root CSS lock:
     ```css
     html, body {
       width: 100%;
       max-width: 100vw;
       overflow-x: hidden !important;
       position: relative;
       overscroll-behavior-x: none;
       -webkit-overflow-scrolling: touch;
     }
     ```
  2. Keep mobile header within $360$px: reduce padding to `px-2 sm:px-6`, hide the duplicate mobile search button (`hidden sm:flex`) because mobile already has an inline search bar below the header, and clamp badges to `top-0 right-0`.
  3. Wrap horizontal carousels in `w-full max-w-full overflow-hidden` and add `overscroll-x-contain` so swipe momentum never drags the document.
  4. Put `w-full max-w-full overflow-hidden` on all major sections (`#catalogue`, `#comboBundlesSection`, `#reviewsProofSection`, `footer`).
