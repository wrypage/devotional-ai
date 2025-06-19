import requests
from requests.auth import HTTPBasicAuth

# Configuration
site_url = "https://selahonradio.com"
username = "indiaconnect"  # your WP username
app_password = "o5Jz Zshn 8tYk b1MD gHQN mIGe"  # your app password
cutoff_date = "2025-01-01T00:00:00"
category_name = "Selah"

auth = HTTPBasicAuth(username, app_password)
headers = {"User-Agent": "Mozilla/5.0"}

def get_category_id(name):
    url = f"{site_url}/wp-json/wp/v2/categories"
    params = {"search": name}
    resp = requests.get(url, params=params, auth=auth, headers=headers)
    if resp.status_code == 200:
        categories = resp.json()
        for cat in categories:
            if cat["name"].lower() == name.lower():
                return cat["id"]
    print(f"Category '{name}' not found.")
    return None

def get_posts(cat_id, before_date, page=1):
    url = f"{site_url}/wp-json/wp/v2/posts"
    params = {
        "categories": cat_id,
        "before": before_date,
        "per_page": 100,
        "page": page,
    }
    resp = requests.get(url, params=params, auth=auth, headers=headers)
    if resp.status_code == 200:
        return resp.json(), int(resp.headers.get("X-WP-TotalPages", 1))
    else:
        print(f"Failed to get posts page {page}: {resp.status_code} {resp.text}")
        return [], 0

def delete_post(post_id):
    url = f"{site_url}/wp-json/wp/v2/posts/{post_id}"  # soft delete (move to Trash)
    resp = requests.delete(url, auth=auth, headers=headers)
    if resp.status_code == 200:
        print(f"Moved post ID {post_id} to Trash")
        return True
    else:
        print(f"Failed to trash post ID {post_id}: {resp.status_code} {resp.text}")
        return False

def main():
    cat_id = get_category_id(category_name)
    if not cat_id:
        return

    page = 1
    while True:
        posts, total_pages = get_posts(cat_id, cutoff_date, page)
        if not posts:
            print("No more posts found.")
            break

        for post in posts:
            delete_post(post["id"])

        if page >= total_pages:
            break
        page += 1

if __name__ == "__main__":
    main()
