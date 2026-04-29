   import requests
   import json
   import re
   import sys

   HEADERS = {
       "User-Agent": "Mozilla/5.0",
       "Accept": "text/html,application/json"
   }

   def get_latest_post(username):
       url = f"https://www.instagram.com/{username}/"

       response = requests.get(url, headers=HEADERS)

       if response.status_code != 200:
           raise Exception("Failed to load profile")

       html = response.text

       match = re.search(r'window\._sharedData = (.*?);</script>', html)

       if not match:
           raise Exception("Could not find Instagram data")

       data = json.loads(match.group(1))

       user = data["entry_data"]["ProfilePage"][0]["graphql"]["user"]
       posts = user["edge_owner_to_timeline_media"]["edges"]

       if not posts:
           raise Exception("No posts found")

       latest = posts[0]["node"]

       media_url = latest["display_url"]
       shortcode = latest["shortcode"]

       return media_url, shortcode


   def download_image(url, filename):
       r = requests.get(url, headers=HEADERS)
       r.raise_for_status()
       with open(filename, "wb") as f:
           f.write(r.content)


   def main():
       if len(sys.argv) < 2:
           print("Usage: python download.py USERNAME")
           return

       username = sys.argv[1]

       print("Fetching latest post for:", username)

       media_url, shortcode = get_latest_post(username)

       filename = f"{username}_{shortcode}.jpg"

       download_image(media_url, filename)

       print("Downloaded:", filename)


   if __name__ == "__main__":
       main()
