import requests
import re
import json
import sys
import time

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/123.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
              "image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def fetch(url):
    """HTTP GET with retry support"""
    for attempt in range(3):
        response = requests.get(url, headers=HEADERS, timeout=30)
        if response.status_code in (429, 500, 502, 503, 504):
            wait = 2 * (attempt + 1)
            print(f"Retrying in {wait}s due to {response.status_code}...")
            time.sleep(wait)
            continue
        response.raise_for_status()
        return response
    response.raise_for_status()


def extract_json(html_text):
    """Extract embedded JSON from Instagram page"""
    # Old structure
    match = re.search(
        r'window\._sharedData\s*=\s*(\{.*?\});\s*</script>',
        html_text,
        re.DOTALL
    )
    if match:
        return json.loads(match.group(1))

    # New Next.js structure
    match = re.search(
        r'<script type="application/json" id="__NEXT_DATA__">\s*(\{.*?\})\s*</script>',
        html_text,
        re.DOTALL
    )
    if match:
        return json.loads(match.group(1))

    raise Exception("Could not locate embedded JSON data.")


def get_latest_post(username):
    url = f"https://www.instagram.com/{username}/"
    print(f"Fetching profile: {url}")
    response = fetch(url)
    data = extract_json(response.text)

    # Try classic format
    user = (
        data.get("entry_data", {})
            .get("ProfilePage", [{}])[0]
            .get("graphql", {})
            .get("user")
    )

    # Try Next.js format fallback
    if not user:
        user = (
            data.get("props", {})
                .get("pageProps", {})
                .get("profile", {})
                .get("user")
        )

    if not user:
        raise Exception("User data not found (private account or structure changed).")

    edges = (
        user.get("edge_owner_to_timeline_media", {}).get("edges")
        or user.get("timeline_media", {}).get("edges")
    )

    if not edges:
        raise Exception("No posts found.")

    latest = edges[0]["node"]

    # Only download images (skip videos/reels)
    if latest.get("is_video"):
        raise Exception("Latest post is a video. This script downloads images only.")

    image_url = (
        latest.get("display_url")
        or latest.get("display_resources", [{}])[-1].get("src")
    )

    shortcode = latest.get("shortcode") or "latest"

    if not image_url:
        raise Exception("Could not extract image URL.")

    return image_url, shortcode


def save_image(image_url, shortcode):
    print("Downloading image...")
    img_data = fetch(image_url).content
    filename = f"{shortcode}.jpg"
    with open(filename, "wb") as f:
        f.write(img_data)
    print(f"Saved as {filename}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python download.py <instagram_username>")
        sys.exit(1)

    username = sys.argv[1]

    try:
        image_url, shortcode = get_latest_post(username)
        save_image(image_url, shortcode)
        print("Download completed successfully ✅")

    except Exception:
        import traceback
        print("ERROR OCCURRED:")
        traceback.print_exc()
        sys.exit(1)

