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

### 15. AI CONCIERGE & STYLIST ENGINE (MULTI-TIER CLOUD + LOCAL FREE OLLAMA + STATIC CLIENT ARCHITECTURE)
- **The Critical Trap**:
  - Relying solely on a single cloud LLM API (e.g. Groq) leaves your store completely stranded when cloud API keys expire, hit rate limits (HTTP 429), run out of monthly quota, or when internet connectivity hiccups.
  - Relying solely on a backend API endpoint (e.g., `/api/ai-stylist`) breaks on static CDNs or GitHub Pages because no Python server is running there.
  - Using complex reasoning models (like `gpt-oss-20b`) burns through token limits on hidden reasoning tokens, returning empty responses.
  - Stuffing the entire 100-item catalog into local LLMs (like Ollama on CPU) causes severe prompt evaluation delays (> 35s), timing out customer requests.
- **The Mandatory Solution (Resilient 3-Tier AI Orchestrator)**:
  1. **Tier 1: Cloud Ultra-Fast LPU (`Groq` via `qwen/qwen3.8-27b`)**:
     - Sub-second streaming responses (< 250ms latency) for instant customer satisfaction.
     - Always provide custom headers: `headers = {"User-Agent": "Storefront-AI/1.0", "Authorization": f"Bearer {key}"}`.
  2. **Tier 2: 100% Free Local Fallback (`Ollama` via `llama3.2`)**:
     - When Groq fails (non-200 status code, HTTP 429 rate limit, 500 error, network timeout, or missing `GROQ_API_KEY`), automatically and silently fall back to local Ollama running on `http://127.0.0.1:11434/api/chat`.
     - 100% free, runs completely offline on the host machine, eliminates recurring API costs, and guarantees 24/7 uptime for WhatsApp customer support.
  3. **Tier 3: Client-Side Browser Engine (`generateClientAiResponse`)**:
     - When running on static hosting (GitHub Pages) or if all backend services are unreachable, catch fetch errors and immediately invoke client-side JavaScript knowledge engine using live `products.json` and fuzzy search. Zero disruption to the customer!
  4. **Focused RAG Retrieval Optimization (Preventing Local LLM CPU Timeouts)**:
     - Never dump the entire raw catalog into the LLM prompt.
     - Use token-scoring helper `_filter_relevant_catalog(query, products_list, max_items=8)` to extract only the top 5 to 8 candidate products relevant to the user query.
     - Reduces prompt size from 1,500+ tokens to < 180 tokens, slashing local Ollama CPU processing time from > 35s down to 8–15s.
  5. **Catalog Injection & Product ID Tagging**:
     - Prompt includes candidate items with ID, title, and price in ₹.
     - Instruct AI to append `[PRODUCTS: id1, id2]` at the end of its response.
     - Frontend regex parses `[PRODUCTS: ...]` and dynamically renders interactive product cards with photo, price, "View in Quick View", and direct WhatsApp buy buttons right inside the chat bubble!
  6. **Starter Chips & Floating Widget**:
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
| **Cloud LLM Quota / Outage** | Cloud LLM (Groq) rate-limits, expires key, or goes down | Multi-tier failover: Groq Cloud LPU $\rightarrow$ Local Ollama (`llama3.2`) $\rightarrow$ Static Catalog RAG |
| **Budget & Price Filters** | Shopper asks "under 500" but search/AI returns ₹999 items because "500" was treated as a text keyword | Extract `parsePriceIntent` regex (`under X`, `below X`, `between X and Y`) and filter `price <= maxPrice` BEFORE text scoring or LLM prompt generation |
| **Voice Search Typing Barrier** | Non-English / mobile shoppers struggle typing complex traditional terms | Integrate HTML5 Web Speech API (`en-IN`) on desktop & mobile search bars with live animated mic toggle |
| **Occasion-Based Kit Building** | Customers must manually find pooja brassware and buffet disposables individually | Smart Occasion Combo Engine generating complete 1-tap kits (e.g. Satyanarayana Pooja / Maroon Bridal) with bundled savings |
| **Visual Search ("Snap & Shop")** | Low-capacity vision models (e.g. Moondream) misclassify Indian jewelry/pooja items as generic urns | Use high-capacity local vision model (`minicpm-v` via Ollama) or Groq Vision, extract structured tags, and query catalog |
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

### 8. Cloud LLM Rate-Limits & Outages: Seamless Local Ollama (llama3.2) Fallback
- **What Happened**: Relying solely on cloud Groq API keys introduces single-point-of-failure risks: hitting free-tier token rate limits (HTTP 429), expired API keys, or cloud network timeouts, leaving customer WhatsApp inquiries unanswered.
- **Why It Happened**: Cloud LLMs are subject to rate limiting, network interruptions, and quotas. Without a local backup, the backend either throws an exception or returns a generic static error message.
- **How to Avoid**:
  1. Build a multi-tier fallback pipeline in `ask_groq_stylist`:
     - **Tier 1 (Cloud LPU)**: Query Groq API (`qwen/qwen3.8-27b`) for sub-second responses.
     - **Tier 2 (Zero-Cost Local Host)**: If Groq fails (non-200 code, 429, timeout, or missing key), automatically fall back to local Ollama (`http://127.0.0.1:11434/api/chat`) running `llama3.2`.
     - **Tier 3 (Catalog Static Heuristic)**: If both are offline, return curated catalog bestsellers with direct WhatsApp ordering links.
  2. Implement Token-Scored Retrieval (RAG) before calling Ollama:
     - On CPU, passing 40+ raw catalog items (1,500+ tokens) causes local Ollama prompt evaluation to take > 35 seconds, hitting client timeouts.
     - Pre-filter catalog with a lightweight token scorer (`_filter_relevant_catalog`) to extract only the top 5 to 8 matching items (< 180 tokens).
     - Result: Local Ollama `llama3.2` inference finishes cleanly in 8 to 15 seconds with zero cloud dependencies and ₹0 cost.

### 9. The Budget Constraint Failure: "Under 500" Returning ₹999 Items
- **What Happened**: Shopper opened the website AI Stylist and asked: *"give me anything under 500"*. The AI returned:
  1. *Royal 6.5" Swan Decorative Tray & Organizer — ₹999* ❌
  2. *Biodegradable Leaf Buffet Plates — ₹200* ✅
  3. *Pure Cz Stone Ear rings — ₹499* ✅
  The top recommendation was double the shopper's budget!
- **Why It Happened**:
  1. Both the search engine and client-side AI knowledge engine treated the query as a plain text string. The token `"500"` was matched against product text, and stopwords (`"give"`, `"me"`, `"anything"`, `"under"`) scored fuzzily against product descriptions.
  2. There was zero semantic price parsing: the system had no concept that `"under 500"` represents a mathematical constraint (`price <= 500`).
- **How to Avoid**:
  1. Always parse numerical price intent first with a regex extractor (`parsePriceIntent`):
     - Maximum price: `/(?:under|below|less than|within|max|upto|up to|<|<=)\s*(?:rs\.?|inr|₹)?\s*([0-9]+)/i` or Telugu `([0-9]+)\s*lopala`.
     - Price range: `/(?:between|from)?\s*([0-9]+)\s*(?:to|-|and)\s*([0-9]+)/i`.
     - Minimum price: `/(?:above|more than|over|min|from|>|>=)\s*([0-9]+)/i`.
  2. Clean noise words (`"give me anything under"`, `"items"`, `"show me"`) to obtain the remaining subject query.
  3. Filter the candidate pool strictly with `price <= maxPrice` BEFORE running text scoring, and sort budget queries by price ascending.
  4. In backend LLM prompts (`_filter_relevant_catalog`), enforce the exact same price ceiling so the LLM is physically never shown items that exceed the customer's specified budget.

### 10. Voice Search & Smart Dynamic Occasion Bundling
- **What Happened**: Many mobile customers, especially elders and regional Telugu/Hindi speakers, find typing long product names or complex pooja terminology difficult on small touchscreens. Furthermore, shoppers organizing weddings or ceremonies had to manually hunt down and add 5 different individual items (diya stand, thali plate, disposables, nomu kit).
- **Why It Happened**: Traditional storefronts only provide a text input box and flat single-item catalog grids.
- **How to Avoid**:
  1. **HTML5 Native Voice Search**:
     - Integrate `window.SpeechRecognition` / `window.webkitSpeechRecognition` into search bars and the AI Stylist modal.
     - Use `lang = 'en-IN'` which natively handles Indian English accents and Telugu/Hindi transliteration (e.g. *"Kundan choker"*, *"Nomu set"*, *"Diya stand"*).
     - Provide visual listening feedback (pulsing mic icon and listening toast) and trigger instant client-side catalog filtering upon speech completion.
  2. **Smart Occasion Combo Builder**:
     - Detect occasion and attire intents in the AI engine (e.g. *"Satyanarayana Pooja for 30 people"*, *"Maroon Kanjeevaram Bridal look"*).
     - Dynamically package complete kits (Pooja ritual brassware + guest buffet dining leaf plates; bridal choker + matching studs + black beads) with 1-tap combo discounts and direct WhatsApp purchase routing.

### 11. Visual Search ("Snap & Shop"): Model Selection Pitfall (Moondream vs MiniCPM-V)
- **What Happened**: When testing local visual search on traditional Indian retail products (Kundan choker necklace, CZ earrings, silver swan decorative tray), a lightweight vision model (`moondream:latest`, 1.7 GB) misidentified all items as generic *"urn"* or decorative pot, rendering the visual search feature unusable.
- **Why It Happened**: Ultralight vision models lack domain features and cultural vocabulary for intricate ethnic jewelry, brass pooja ware, and Indian craft motifs.
- **How to Avoid**:
  1. Use high-capability vision models (`minicpm-v:latest`, 5.5 GB) in Ollama or Groq Vision (`llama-3.2-11b-vision-preview`).
  2. Structure the vision prompt to force a specific keyword extraction syntax:
     `Identify the primary product, category, jewelry/handicraft type, gemstone, and metal. Output 3-6 search keywords inside <start of keywords> and <end of keywords>.`
  3. Wire a seamless client fallback: If backend visual inference is offline, extract clean keywords from the uploaded filename (`kundan-choker.jpg` $\rightarrow$ *"kundan choker"*) and trigger instant client-side catalog filtering without dropping the customer.

### 12. Silent Visual Search Failure on Image Selection (Missing Toast & Hidden File Input Traps)
- **What Happened**: User clicked the 📷 camera icon on the website search bar or AI stylist, picked a photo, and clicked "Done" on their phone/browser. Nothing appeared—no photo preview, no loading spinner, no response at all.
- **Why It Happened**:
  1. `showToastNotification(...)` was invoked at the very top of `handleVisualSearchFileSelected`, but the helper function had never been declared in global scope. The browser threw `ReferenceError: showToastNotification is not defined`, immediately terminating execution before image processing could start.
  2. The hidden `<input type="file" id="visualSearchFileInput">` was nested inside `#aiStylistModal`, which had `display: none` (`hidden`). Certain mobile browsers ignore or restrict file picker events originating from hidden descendants.
  3. On static GitHub Pages hosting (`srrbazaar.com`), an unconstrained `fetch('/api/visual-search')` attempt to hit a nonexistent server endpoint stalled before failing, with no client-side image classifier fallback.
- **How to Avoid**:
  1. Define a persistent, robust `showToastNotification` helper attached to a root `#globalFloatingToast` element early in the script execution flow.
  2. Always place hidden file inputs (`<input type="file">`) directly under `<body>` at the root DOM level so click triggers never fail regardless of modal state.
  3. When an image is picked, immediately read it via `FileReader.readAsDataURL` and open the AI chat with the customer's actual photo thumbnail (`<img>`) and an animated analyzing indicator so the customer gets immediate visual confirmation.
  4. Detect `isLocalHost`: only probe `/api/visual-search` when running on a local development server. On production static hosts (GitHub Pages), immediately run an in-browser HTML5 canvas color & pattern classifier (`analyzeImageClient`) to match against the catalog in under 100 ms with zero network latency.

### 13. Amazon Lens Visual Search Dual-Mode Architecture (Search Bar vs. Chatbot Modal)
- **What Happened**: When shoppers tapped the 📷 camera icon on the top search bar, the UI unexpectedly popped open the full-screen AI Stylist chatbot window over their screen. Shoppers expected the camera on the search bar to filter the catalog grid directly on the page (like Amazon / Google Lens) rather than interrupting their shopping flow with a chatbot modal.
- **Why It Happened**: The image selection handler routed all camera uploads uniformly to `openAiStylistModal(true)`, regardless of where the camera trigger was clicked.
- **How to Avoid**:
  1. **Dual-Mode Context Routing** (`visualSearchTarget`):
     - If triggered from **Search Bar** (`desktop` or `mobile`): Keep the chatbot modal CLOSED. Auto-fill the search input with detected keywords, smoothly scroll down to `#catalogue`, and display an Amazon-style `#visualLensBanner` showing the uploaded photo thumbnail, detected keywords, and a 1-tap "✕ Clear" button.
     - If triggered from **AI Stylist Modal** (`chat`): Keep the flow inside the chat stream, rendering the uploaded photo bubble, analyzing indicator, and interactive recommendation cards.
  2. **Fail-Safe Network Timeout**:
     - Constrain backend visual search network fetches to a maximum 4-second timeout (`AbortController`). If the backend tunnel is offline or sleeping, fail over immediately to the local in-browser visual classifier (`analyzeImageClient`) so mobile shoppers never encounter hanging requests.

### 14. WhatsApp Media Webhook Video Reel Failures (FFmpeg Exit Code 4294967284 & Catalogue Sync Traps)
- **What Happened**: When new product photos were sent to the WhatsApp Business automation, video reels were not getting uploaded to Instagram or attached to the website catalogue. The jobs in `whatsapp_jobs.sqlite3` recorded: `Command '['ffmpeg', '-y', ... 'luxury_gold_black.mp4']' returned non-zero exit status 4294967284`, and new items in `docs/products.json` had `"video": null`.
- **Why It Happened**:
  1. **Resource Starvation & Crash (`4294967284` / `0xFFFFFFF4`)**:
     - The reel generator configured `DURATION = 30` (900 frames at 30 fps), `-preset slow`, `-crf 18`, and complex `zoompan` filters across 4 distinct themes sequentially for every single photo.
     - When multiple photos arrived within minutes of each other, background tasks spawned concurrent FFmpeg processes that exhausted Windows thread handles and memory, crashing with access violation / fatal app exit.
  2. **FastAPI Webhook Process Restart & Desync**:
     - Uvicorn was run without `--reload`. Code updates to `sync_product_to_website_catalogue` were not picked up in memory, causing products to be committed to `products.json` without the `video` key.
     - If Uvicorn was stopped or restarted while FFmpeg was encoding, the child process was terminated abruptly with exit code `4294967284`.
- **How to Avoid**:
  1. **Streamline Reel Encoding**:
     - Set `DURATION = 15` (450 frames), which is ideal for Instagram Reels, Meta Shorts, and mobile status view rates.
     - Use `-preset fast` and `-crf 20`. Encoding time drops from 40 seconds to 3 seconds per reel with zero discernible difference in visual quality on graphic posters.
  2. **Thread Locking (`threading.Lock`)**:
     - Guard FFmpeg execution with a process-level lock (`FFMPEG_LOCK`) so multiple concurrent WhatsApp webhooks queue gracefully rather than hammering CPU cores at the same second.
  3. **Multi-Stage Resilient Fallback**:
     - Wrap primary `zoompan` encoding in a `try...except` block. If any crash occurs, automatically execute a lightweight, bulletproof motion pad/scale command (`-preset veryfast`) so video generation never throws unhandled errors.
  4. **Catalogue Sync Self-Healing**:
     - In `sync_product_to_website_catalogue`, if `video_path` is missing or `None`, automatically scan `generated/whatsapp/<job_id>` for any existing `.mp4` reels.
     - If still missing, immediately invoke `generate_reel` on-demand to create a web-optimized 15s reel, compress it to `docs/videos/reel_<id>.mp4`, and record `"video": "videos/reel_<id>.mp4"` in `products.json`.
  5. **Direct Video Reel Playback in Storefront**:
     - Wire the "Video Reel" badge on every product card in `docs/index.html` with an `onclick` handler to open QuickView and instantly switch to the video player, allowing shoppers to view the product sparkle in 1 tap directly from the catalogue.

### 15. Visual Search Fuzzy Substring False Positives ("Plate" vs. "Gold-Plated") & Mobile Viewport Auto-Scroll
- **What Happened**: When a shopper uploaded a photo of buffet dining plates via Visual Search ("Snap & Shop"), the search returned Kundan chokers and black beads necklaces instead of buffet plates. Additionally, while the search was processing, there was no active scanning feedback, and after completion, the page failed to scroll down to the matched products on mobile.
- **Why It Happened**:
  1. **Substring Over-Matching on Descriptions**:
     - The search engine's scoring function used raw substring matching (`descNorm.includes(variant)`) and fuzzy Levenshtein distance on description tokens (`isFuzzyMatch("plates", "plated") === true`, distance = 1).
     - Because over 30 jewelry items contained *"with gold-plated finish"* in their descriptions, they all scored false-positive hits for the query *"plate"*, flooding the top results with jewelry.
  2. **Static Host API Disconnection**:
     - On static GitHub Pages (`srrbazaar.com`), relative API calls (`fetch('/api/visual-search')`) returned 404 because static hosts cannot execute Python endpoints. The fallback color heuristic checked for bright green (`gAvg > rAvg + 15`), which failed on natural kraft/beige/areca nut buffet plates (`R=178, G=166, B=153`), defaulting to jewelry.
  3. **High-Level Section Scroll**:
     - The auto-scroll targeted `<section id="catalogue">`, which stopped at the top of the entire section above the filters, categories, and banners, leaving the actual products below the fold on mobile.
- **How to Avoid**:
  1. **Enforce Whole-Word Boundaries & Exclude Description Fuzzy Matching**:
     - Never use raw substring search (`includes()`) or fuzzy distance matching across descriptions.
     - Match query tokens against word boundaries `new RegExp(`(^|[^a-zA-Z0-9])${variant}([^a-zA-Z0-9]|$)`, 'i')` so that *"plate"* or *"plates"* never matches *"gold-plated"*.
     - Restrict fuzzy matching strictly to product titles (`tTokens`), where typographical errors actually occur.
  2. **Active Laser-Scanning UI Overlay**:
     - When a photo is selected, immediately display `#visualScanningModal` showing the customer's photo with an animated laser scanning beam (`animate-scan`) and pulsing status text: *"AI Lens Scanning Photo... Matching items in SRR Bazaar catalogue..."*.
     - Keep this modal visible until search and filtering finish, providing clear, responsive feedback.
  3. **Pixel-Perfect Auto-Scroll to Results**:
     - Auto-scroll directly to `#visualLensBanner` / `#productGrid` with a negative offset (`top - 75px`) to accommodate the sticky navigation header, placing the matching products squarely into view on mobile.
  4. **Dynamic Backend Routing with 1-Tap Category Refinement**:
     - In production, route `/api/visual-search` and `/api/ai-stylist` to the public backend tunnel (`https://squander-gristle-panhandle.ngrok-free.dev`) with a 2-second timeout and `'ngrok-skip-browser-warning': 'true'`.
     - Provide 1-tap quick category refine pills (`🍃 Buffet Plates`, `🪔 Diya Stands`, `🦢 Swan Trays`, `👑 Kundan Sets`, `🥻 Sarees`) on `#visualLensBanner` so shoppers can jump to any department in a single tap.


### 16. Google Merchant Center Shopping Feed Compliance & "Instant Fresh Drops" Storefront Architecture
- **What Happened**: 
  1. Google Merchant Center flagged 31 out of 40 products as "Not being shown on Google", with products showing "Not approved" and "Limited". Products imported from raw social media captions contained titles like `Single`, `fs`, `1190 free ship`, `/+ freeshipping`, and `Today special offer`.
  2. Newly uploaded products to the storefront were not immediately visible when shoppers opened the website, as they were buried below top banners, carousels, and category grids.
- **Why It Happened**:
  1. **Google Shopping Strict Policy Violations**:
     - Google explicitly bans promotional text in product titles (e.g., "free shipping", "fs", "special offer", "discount", or prices).
     - Titles that are too short or generic (like `Single` or `fs`) trigger immediate automated disapprovals for lack of descriptive product information.
     - Products lacked `<g:identifier_exists>no</g:identifier_exists>` and standard `<g:google_product_category>` tags, causing Google to flag them as "Limited" for missing global GTIN/barcode identifiers.
  2. **Storefront Visual Hierarchy Friction**:
     - On mobile and desktop, rich hero banners, promotions, and category tabs occupy the first 1200+ pixels. Without a prominent top drop trigger, shoppers opening the store had no way of knowing a new item had just launched without scrolling deep into the catalogue.
- **How to Avoid**:
  1. **Google Merchant Shopping Feed Sanitization**:
     - Automatically sanitize titles when generating RSS/XML feeds (`docs/google_merchant_feed.xml`): strip all promotional keywords, pricing strings, and special characters (`/+`).
     - Map every product to descriptive, high-converting titles (e.g. `Delicate Lotus Pendant Pearl & Ruby Green Beaded Necklace Set`, `Traditional Ruby & Emerald Floral Kada Bangles Set of 4`).
     - Set `<g:identifier_exists>no</g:identifier_exists>` for custom handcrafted, boutique, and artisanal products that do not carry manufacturer GTIN/EAN barcodes to completely eliminate "Limited" visibility penalties.
     - Assign granular `<g:google_product_category>` (e.g. `Apparel & Accessories > Jewelry`, `Apparel & Accessories > Clothing > Traditional & Cultural Wear > Sarees`, `Home & Garden > Religious & Ceremonial`).
  2. **Multi-Touch "Fresh Drops" Storefront Architecture**:
     - **Top Marquee Ticker (`#latestDropTicker`)**: Embed a live, clickable pill in the top announcement bar: `🔥 NEW DROP: [Latest Product Title] | View →` that smoothly auto-scrolls down and highlights the product card with a 4px golden ring.
     - **Top Shelf Catalogue Aisle**: Automatically position `"🔥 Just Dropped — Fresh New Arrivals"` as the very #1 shelf above all category aisles in the storefront catalogue.
     - **Dedicated "New Drops" Quick Filter**: Provide a high-visibility circular tab (`data-category="new"`) with an animated pulsing notification dot in the category navigation bar.
     - **Floating Fresh Drop Toast (`#freshDropToast`)**: Display a sleek, non-intrusive floating pill on the bottom edge (`Just Added to Store: [Title] - [Price]`) with 1-tap view and session dismissal memory (`sessionStorage`) so shoppers are immediately aware without being disrupted.


### 17. High-Conversion "Partial COD" (20% Advance Token via UPI + 12-Digit UTR + Balance on Delivery) & Removal of 100% Unpaid COD
- **What Happened**: 
  1. Offering 100% Cash on Delivery (COD) on high-value jewelry and artisanal festive products exposes the merchant to high Return to Origin (RTO) rates (up to 30–40% in Indian D2C e-commerce) caused by impulse/fake orders or unreachable customers. If Full COD is left enabled alongside Partial COD, buyers who want to place careless orders simply choose Full COD to bypass the advance token.
  2. A fixed ₹150 flat advance token protects low-ticket items (₹500–₹800), but on high-value carts (₹2,500–₹5,000+), ₹150 leaves 95%+ of the order value exposed to refusal at the customer's doorstep.
- **Why It Happened**:
  - Full COD carries zero financial commitment from the buyer, leading to frivolous checkouts where customers refuse parcels upon courier delivery, costing the seller ₹120–₹180 in two-way courier shipping fees.
  - A flat nominal fee does not scale with order risk on luxury sets.
- **How to Avoid**:
  1. **Disable 100% Unpaid COD Completely**:
     - Remove the zero-advance Full COD option. Offer only:
       - **⚡ Partial COD (20% Advance via UPI + Balance on Delivery)**
       - **✨ Instant UPI QR (100% Prepaid - Fastest)**
       - **💳 Cards & Netbanking (Razorpay Online Gateway)**
     - This guarantees that 100% of orders placed have real financial commitment before parcels are packed.
  2. **Smart 20% Dynamic Advance Token with ₹150 Minimum Floor**:
     - Calculate advance dynamically:
       `advanceAmount = Math.min(cartTotal, Math.max(150, Math.round((cartTotal * 0.20) / 10) * 10))`
       `codBalance = Math.max(0, cartTotal - advanceAmount)`
     - **Minimum Floor of ₹150**: Guarantees that two-way courier shipping through The Professional Couriers is covered even on entry-level items.
     - **20% Scaling**: For a ₹2,500 necklace, the buyer pays ₹500 advance; for a ₹5,000 cart, they pay ₹1,000 advance. With substantial money invested, buyer cancellation drops to near 0%.
  3. **Strict Client-Side 12-Digit UTR Validation**:
     - Require customers to enter their **12-digit UPI Transaction Reference (UTR)** from their payment receipt into `#upiRefNumber`.
     - Block order submission and highlight the input field with a shake/red ring alert if the UTR is missing or fewer than 10 digits.
  4. **Itemized Transparency Across Receipts & WhatsApp**:
     - Format customer receipts and the automated WhatsApp order dispatch message with an explicit breakdown:
       - `Payment Mode: ⚡ Partial COD (20% Advance Token Paid)`
       - `Advance Paid via UPI: ₹[advanceAmount] (UTR: 123456789012)`
       - `Remaining Balance Payable on Delivery: ₹[codBalance]`
       - `Order Status: ✅ Confirmed & Locked for Dispatch`
     - Highlight Partial COD orders in the merchant portal with dedicated gold badges and instant WhatsApp chat links so the fulfillment team can verify the UTR in their banking app before parcel handoff to The Professional Couriers.


### 18. Checkout Hardening & Loophole Prevention: Double-Click Locks, Dummy UTR Filtering, and Courier Manifest Validation
- **What Happened**: 
  1. On mobile network jitter (3G/4G), impatient shoppers frequently tap 'Confirm Order & Send to WhatsApp' multiple times in quick succession. Without an explicit submission lock, this creates duplicate order records in Google Sheets and logs multiple order entries in the merchant portal.
  2. Buyers attempting to bypass advance payment sometimes enter dummy placeholder numbers (e.g., 000000000000, 111111111111, or 999999999999).
  3. When an order completes, if the input fields retain the previous transaction's UTR, a customer placing an immediate second order might accidentally submit the old UTR without paying a new advance.
  4. Customers entering invalid phone numbers (e.g., numbers starting with 12345... or 0000000000) or bogus pincodes (000000) cause booking rejections when generating shipping labels at the courier hub (The Professional Couriers, Armoor Hub).
- **Why It Happened**:
  - Simple form submissions lack asynchronous state tracking and submission debounce locks.
  - Basic character-length checks alone (length >= 10) do not verify pattern authenticity against repeating digit sequences.
  - Form state caching across modal closures can leak previous inputs into subsequent carts.
- **How to Avoid**:
  1. **Atomic Submit Lock (isSubmittingOrder)**:
     - Maintain an atomic in-memory flag isSubmittingOrder = false.
     - Upon submitFinalOrder(), immediately check if (isSubmittingOrder) return;.
     - Set isSubmittingOrder = true and disable #placeOrderBtn while replacing its content with 'Processing Order...' and cursor-not-allowed styling.
     - Provide a centralized resetOrderButtonState() helper that safely restores the button to its original state on any validation failure, payment dismissal, or modal close.
  2. **Repeating-Digit Dummy UTR Filter**:
     - Enforce cleanUpiRef.length >= 10 && cleanUpiRef.length <= 12.
     - Reject all-identical repeating sequences via /^(\d)\1{9,11}$/. This instantly blocks 000000000000, 111111111111, etc., and prompts the user for a genuine banking transaction reference.
  3. **Strict Post-Order Input Sanitization**:
     - Immediately upon order record creation and modal transition, wipe #upiRefNumber to empty string and remove any alert styling so subsequent checkouts mandate a new, unique advance token UTR.
  4. **Courier Manifest Validation (Mobile & Pincode)**:
     - Automatically clean +91 or leading 0 from phone inputs, extract the trailing 10 digits, and validate with ^[6-9]\d{9}$ while barring all-identical digits (/^(\d)\1{9}$/).
     - Enforce strict 6-digit Indian postal codes via ^[1-9][0-9]{5}$ to completely eliminate 000000 or invalid PIN entries before booking with The Professional Couriers.
  5. **Post-Test Automation Cleanliness**:
     - Ensure automated test suites and mock checkouts include teardown logic (localStorage.setItem('srr_orders', '[]')) so test runs never pollute the live merchant dashboard.


### 19. Frictionless Growth Architecture: 5% Prepaid Cashback Wallet & Viral WhatsApp Refer & Earn (Zero-Login / Phone-Linked)
- **What Happened**: 
  1. Standard e-commerce loyalty systems require forced sign-up, email verification, and password creation. On high-velocity impulse traffic arriving from Instagram Reels and boosted Meta ads, forcing user registration creates a 40–50% drop-off rate before checkout.
  2. Without an incentive to choose 100% prepaid payments over Partial COD, the merchant bears the burden of door-to-door COD collection reconciliation.
  3. Word-of-mouth sharing among festive and bridal shoppers is overwhelmingly conducted via family WhatsApp groups, which traditional email-based referral programs fail to capture.
- **Why It Happened**:
  - Requiring account registration adds high cognitive friction for casual mobile social shoppers.
  - Absence of a real-time instant reward for paying 100% upfront leaves buyers defaulting to COD.
- **How to Avoid**:
  1. **Phone-Linked Browser Wallet (srr_wallet_balance)**:
     - Automatically award **5% cash cashback** on all 100% Prepaid UPI and Razorpay checkouts (e.g. ₹53 cashback credited on a ₹1,050 order).
     - Store the balance in localStorage['srr_wallet_balance'] and associate with the verified 10-digit customer mobile number (srr_cust_phone).
     - Display a dynamic gold pill in the header navigation (🪙 ₹53) and an instant 1-tap redemption checkbox in the Cart Drawer: [✓] Apply ₹53 Wallet Cash.
     - Automatically cap wallet deduction to keep a minimum ₹50 payable so transactions remain legitimate with courier protection.
  2. **Zero-Login WhatsApp Refer & Earn Engine**:
     - Provide a dedicated **Refer & Earn Modal** (#referModal) accessible from the header navigation and order confirmation receipt.
     - Generate an instant personalized invitation URL: https://srrbazaar.com/?ref=[PHONE] without requiring passwords or registration.
     - **Friend Incentive**: Anyone visiting via ?ref=... triggers a sticky top welcome banner and an automatic **₹100 Welcome Discount** on carts of ₹500+.
     - **Referrer Incentive**: Upon dispatch of the friend's order, the referrer's wallet is credited with ₹100 cash.
  3. **1-Tap WhatsApp Viral Social Pre-Fills**:
     - Pre-format viral WhatsApp invite messages featuring localized emojis, store highlights (temple harams, pure kundan, brass diyas), and personal deep-links for instant sharing into Indian family WhatsApp groups.
