import json
import os
import time
import openai
import psycopg2
from psycopg2.extras import execute_values

# ─── CONFIGURATION ─────────────────────────────────────────────────────────────

DB_NAME     = "selahdevotional"
DB_USER     = "selah"
DB_PASSWORD = "4HisGlory!"
DB_HOST     = "localhost"
DB_PORT     = "5432"

# Make sure OPENAI_API_KEY is exported in your shell
openai.api_key = os.getenv("OPENAI_API_KEY")

JSON_FILE = "selah_posts_parsed.json"
BATCH_SIZE = 100
EMBEDDING_MODEL = "text-embedding-ada-002"

# ─── HELPER FUNCTIONS ──────────────────────────────────────────────────────────

def load_posts(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_embeddings(text_list):
    """
    Given a list of strings, return a list of embedding vectors using the new OpenAI v1 API.
    Splits into multiple requests if the list is very large (1000 items per request).
    """
    embeddings = []
    for chunk_start in range(0, len(text_list), 1000):
        chunk = text_list[chunk_start : chunk_start + 1000]
        
        # New v1.0.0+ embeddings call:
        response = openai.embeddings.create(
            model=EMBEDDING_MODEL,
            input=chunk
        )
        # response["data"] is a list of { "object": "embedding", "embedding": [...], "index": i }
        embeddings.extend([d["embedding"] for d in response["data"]])
        
        # Pause briefly to respect rate limits
        time.sleep(1.0)
    return embeddings

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

    # 3) Process in batches
    for i in range(0, len(posts), BATCH_SIZE):
        batch = posts[i : i + BATCH_SIZE]
        texts = [p["content"] for p in batch]

        # 4) Generate embeddings for this batch
        embeddings = get_embeddings(texts)

        # 5) Build rows to insert
        rows = []
        for post, emb in zip(batch, embeddings):
            rows.append((
                post["title"],           # post_title
                post["content"],         # post_content
                post.get("excerpt", ""), # post_excerpt
                post.get("pub_date", None),    # post_date
                post.get("categories", []),    # categories
                post.get("tags", []),          # tags
                post.get("post_url", ""),      # post_url
                emb                             # embedding (vector)
            ))

        # 6) Insert into blog_posts table
        insert_query = """
            INSERT INTO blog_posts
            (post_title, post_content, post_excerpt, post_date, categories, tags, post_url, embedding)
            VALUES %s
            ON CONFLICT (post_url) DO NOTHING
        """
        execute_values(cursor, insert_query, rows)
        conn.commit()
        print(f"Inserted batch {i}–{i+len(batch)-1}")

    cursor.close()
    conn.close()
    print("All posts inserted with embeddings.")

if __name__ == "__main__":
    main()
