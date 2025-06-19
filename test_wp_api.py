import requests
from requests.auth import HTTPBasicAuth

# CONFIG
username = "indiaconnect"
app_password = "YOUR_APP_PASSWORD_HERE"  # ← replace with your real App Password
site_url = "https://selahonradio.com"
post_title = "The Cross and the Power of God"  # ← can change this

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36"
}

# Make the request
search_url = f"{site_url}/wp-json/wp/v2/posts"
params = {"search": post_title}
auth = HTTPBasicAuth(username, app_password)

response = requests.get(search_url, auth=auth, params=params, headers=headers)

# Handle response
if response.status_code == 200:
    posts = response.json()
    if posts:
        print(f"✅ Found {len(posts)} post(s):")
        for post in posts:
            print(f"- ID {post['id']}: {post['title']['rendered']} (Tags: {post['tags']})")
    else:
        print("⚠️ No posts found matching that title.")
else:
    print(f"❌ Failed: HTTP {response.status_code}")
    print(response.text)
import requests
from requests.auth import HTTPBasicAuth

# CONFIG
username = "indiaconnect"
app_password = "YOUR_APP_PASSWORD_HERE"  # replace this!
site_url = "https://selahonradio.com"
post_title = "The Cross and the Power of God"  # example post

# Request headers with browser-like User-Agent
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36"
}

# Make the request
search_url = f"{site_url}/wp-json/wp/v2/posts"
params = {"search": post_title}
auth = HTTPBasicAuth(username, app_password)

response = requests.get(search_url, auth=auth, params=params, headers=headers)

# Handle response
if response.status_code == 200:
    posts = response.json()
    if posts:
        print(f"✅ Found {len(posts)} post(s):")
        for post in posts:
            print(f"- ID {post['id']}: {post['title']['rendered']} (Tags: {post['tags']})")
    else:
        print("⚠️ No posts found matching that title.")
else:
    print(f"❌ Failed: HTTP {response.status_code}")
    print(response.text)
