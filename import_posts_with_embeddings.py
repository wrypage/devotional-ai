import json
import os
import time
import openai
import psycopg2

# ─── CONFIGURATION ─────────────────────────────────────────────────────────────

DB_NAME     = "selahdevotional"
DB_USER     = "selah"
DB_PASSWORD = "4HisGlory!"     # ← Your exact PostgreSQL password
DB_HOST     = "localhost"
DB_PORT     = "5432"

# Make sure OPENAI_API_KEY is exported in your shell before running this script
openai.api_key = os.getenv("OPENAI_API_KEY")

JSON_FILE = "selah_posts_parsed.json"
EMBEDDING_MODEL = "text-embedding-ada-002"

# ─── HELPER FUNCTIONS ──────────────────────────────────────────────────────────

def load_posts(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_embedding_for_text(text):
    """
    Request an embedding for a single string (post content).
    Adjusted for the v1+ OpenAI library: use response.data, not response["data"].
    """
    response = openai.embeddings.create(
        model=EMBEDDING_MODEL,
        input=[text]
    )
    # With the v1+ client, response.data is a list of objects;
    # each object’s .embedding attribute holds the vector.
    return response.data[0].embedding

# ─── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    # 1) Load parsed posts from JSON
    posts = load_posts(JSON_FILE)

    # 2) Connect to PostgreSQL
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    cursor = conn.cursor()

    total = len(posts)
    print(f"Total posts to insert: {total}")

    # 3) Loop through each post individually
    for idx, post in enumerate(posts, start=1):
        title = post.get("title", "")
        content = post.get("content", "")
        excerpt = post.get("excerpt", "")
        pub_date = post.get("pub_date", None)
        categories = post.get("categories", [])
        tags = post.get("tags", [])
        post_url = post.get("post_url", "")

        # 4) Generate an embedding for this single post's content
        try:
            emb_vector = get_embedding_for_text(content)
        except Exception as e:
            print(f"Error embedding post {idx}/{total} (URL={post_url}): {e}")
            continue  # Skip this post if embedding fails

        # 5) Insert this single row into blog_posts
        insert_query = """
            INSERT INTO blog_posts
            (post_title, post_content, post_excerpt, post_date, categories, tags, post_url, embedding)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (post_url) DO NOTHING
        """
        cursor.execute(insert_query, (
            title,
            content,
            excerpt,
            pub_date,
            categories,   # psycopg2 will convert Python list → TEXT[]
            tags,         # similarly for tags
            post_url,
            emb_vector    # vector column for pgvector
        ))
        conn.commit()

        # Print progress every 50 posts (or at the end)
        if idx % 50 == 0 or idx == total:
            print(f"Inserted {idx}/{total} posts")

        # Delay briefly to respect OpenAI rate limits
        time.sleep(0.5)

    cursor.close()
    conn.close()
    print("All posts inserted with embeddings (one by one).")

if __name__ == "__main__":
    main()
