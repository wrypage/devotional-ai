import csv
import requests
from requests.auth import HTTPBasicAuth
import html
from rapidfuzz import fuzz, process  # fuzzy matching library

# CONFIGURATION
site_url = "https://selahonradio.com"
username = "indiaconnect"
app_password = "o5Jz Zshn 8tYk b1MD gHQN mIGe"  # replace with your app password
csv_file = "devotional_post_tag_map.csv"  # your CSV file with 'title' and 'tags'

auth = HTTPBasicAuth(username, app_password)
headers = {"User-Agent": "Mozilla/5.0"}

def get_tag_id(tag_name):
    """Search for tag by name; create if not exists"""
    search_url = f"{site_url}/wp-json/wp/v2/tags"
    params = {"search": tag_name}
    resp = requests.get(search_url, params=params, auth=auth, headers=headers)
    if resp.status_code != 200:
        print(f"Failed to search tag '{tag_name}': HTTP {resp.status_code}")
        return None
    tags = resp.json()
    for tag in tags:
        if tag["name"].lower() == tag_name.lower():
            return tag["id"]
    # Tag not found, create it
    create_resp = requests.post(search_url, auth=auth, headers=headers, json={"name": tag_name})
    if create_resp.status_code == 201:
        print(f"Created tag '{tag_name}'")
        return create_resp.json()["id"]
    else:
        print(f"Failed to create tag '{tag_name}': HTTP {create_resp.status_code}")
        return None

def get_post_titles_batch(search_term):
    """Return a list of (post_id, title) tuples for posts matching search_term (partial/fuzzy search)"""
    posts_url = f"{site_url}/wp-json/wp/v2/posts"
    params = {"search": search_term, "per_page": 20}
    resp = requests.get(posts_url, params=params, auth=auth, headers=headers)
    if resp.status_code != 200:
        print(f"Failed to search posts '{search_term}': HTTP {resp.status_code}")
        return []
    posts = resp.json()
    return [(post["id"], html.unescape(post["title"]["rendered"]).strip()) for post in posts]

def find_best_fuzzy_match(title, candidates, threshold=85):
    """Find best fuzzy match for title among candidates; returns candidate or None"""
    if not candidates:
        return None
    match = process.extractOne(title, candidates, scorer=fuzz.token_sort_ratio)
    if match and match[1] >= threshold:
        return match[0]
    return None

def get_post_id_by_title_fuzzy(title):
    """Try exact match first; if fails, do fuzzy match on candidates from WP search"""
    # Decode HTML entities in title
    decoded_title = html.unescape(title).strip()

    # Try exact match (case-insensitive)
    posts_url = f"{site_url}/wp-json/wp/v2/posts"
    params = {"search": decoded_title, "per_page": 20}
    resp = requests.get(posts_url, params=params, auth=auth, headers=headers)
    if resp.status_code != 200:
        print(f"Failed to search post '{decoded_title}': HTTP {resp.status_code}")
        return None
    posts = resp.json()

    for post in posts:
        post_title = html.unescape(post["title"]["rendered"]).strip()
        if post_title.lower() == decoded_title.lower():
            return post["id"]

    # No exact match found, do fuzzy matching
    candidates = [html.unescape(post["title"]["rendered"]).strip() for post in posts]
    best_match = find_best_fuzzy_match(decoded_title, candidates)
    if best_match:
        # Find corresponding post ID for best match
        for post in posts:
            pt = html.unescape(post["title"]["rendered"]).strip()
            if pt == best_match:
                print(f"⚠️ Fuzzy matched '{decoded_title}' to '{best_match}'")
                return post["id"]

    return None

def update_post_tags(post_id, tag_ids):
    """Update post tags by IDs"""
    url = f"{site_url}/wp-json/wp/v2/posts/{post_id}"
    resp = requests.post(url, auth=auth, headers=headers, json={"tags": tag_ids})
    if resp.status_code == 200:
        print(f"✅ Updated post ID {post_id} with tags {tag_ids}")
    else:
        print(f"❌ Failed to update post ID {post_id}: HTTP {resp.status_code} {resp.text}")

def main():
    with open(csv_file, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            title = row["title"]
            tags_raw = row["tags"]
            if not tags_raw.strip():
                print(f"Skipping post '{title}' (no tags)")
                continue
            tag_names = [t.strip() for t in tags_raw.split(",")]
            tag_ids = []
            for tag_name in tag_names:
                tag_id = get_tag_id(tag_name)
                if tag_id:
                    tag_ids.append(tag_id)
            if not tag_ids:
                print(f"No valid tags for post '{title}', skipping update.")
                continue
            post_id = get_post_id_by_title_fuzzy(title)
            if post_id:
                update_post_tags(post_id, tag_ids)
            else:
                print(f"❌ Post not found: {title}")

if __name__ == "__main__":
    main()
