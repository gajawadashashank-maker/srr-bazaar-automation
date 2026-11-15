# SRR Bazaar Automation (WhatsApp to Instagram Reel Publisher)

Automated workflow that receives product media and details via WhatsApp Cloud API webhook, generates high-quality 9:16 Instagram Reels with background music and branded styling, uploads to Cloudinary CDN, and automatically publishes them as Instagram Reels via Meta Graph API.

## Features

- **WhatsApp Cloud API Webhook**: Handles incoming product images and descriptions from authorized senders.
- **Dynamic Reel Generator**: Creates 1080x1920 (9:16) vertical video reels with product imagery, smooth motion, text overlays, and audio integration.
- **Cloudinary Integration**: Uploads reels for public CDN hosting required by Instagram Graph API.
- **Meta / Instagram Graph API**: Publishes reels directly to Instagram with auto-captioning and status tracking.
- **Async Processing**: Background queue for processing media, video generation, and publishing.

## Setup & Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/gajawadashashank-maker/srr-bazaar-automation.git
   cd srr-bazaar-automation
   ```

2. **Configure Environment:**
   Copy `.env.example` to `.env` and fill in your credentials:
   ```bash
   cp .env.example .env
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Application:**
   ```bash
   python app.py
   ```
