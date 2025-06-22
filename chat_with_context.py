import os
import openai
import psycopg2
from psycopg2.extras import RealDictCursor

# ─── CONFIGURATION ─────────────────────────────────────────────────────────────

DB_NAME     = "selahdevotional"
DB_USER     = "selah"
DB_PASSWORD = "4HisGlory!"
DB_HOST     = "localhost"
DB_PORT     = "5432"

# Ensure OPENAI_API_KEY is set in your environment (via ~/.bashrc or export).
openai.api_key = os.getenv("OPENAI_API_KEY")

# ─── HELPER FUNCTIONS ──────────────────────────────────────────────────────────

def semantic_search(question, top_k=3):
    """
    Embed the question, query the DB, and return top_k posts (id, title, content, url, distance).
    """
    # 1) Embed the question
    resp = openai.embeddings.create(
        model="text-embedding-ada-002",
        input=[question]
    )
    q_vec = resp.data[0].embedding  # 1536‐dim list

    # 2) Connect to PostgreSQL
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # 3) Build vector literal '[val1,val2,...]'
    vec_str = "[" + ",".join(map(str, q_vec)) + "]"
    sql = f"""
        SELECT id, post_title, post_content, post_url, embedding <-> '{vec_str}' AS distance
        FROM blog_posts
        ORDER BY distance
        LIMIT {top_k};
    """
    cursor.execute(sql)
    results = cursor.fetchall()  # List of dicts: id, post_title, post_content, post_url, distance
    cursor.close()
    conn.close()

    return results

def build_prompt(question, posts):
    """
    Construct a ChatGPT prompt that includes:
      - A system message instructing the model to answer using only provided excerpts.
      - A user message containing excerpts from the retrieved posts + the question.
    """
    system_msg = (
        "You are an AI assistant answering a theological question using only the content "
        "of the provided Selah blog posts. "
        "If the answer is not explicitly in those excerpts, respond with: "
        "'I’m not sure based on the provided blogs.'"
    )

    # Build the user‐context block
    user_context = "Here are excerpts from relevant Selah blog posts:\n\n"
    for i, post in enumerate(posts, start=1):
        excerpt = post["post_content"][:500]  # first 500 characters
        user_context += (
            f"Post {i} Title: {post['post_title']}\n"
            f"URL: {post['post_url']}\n"
            f"Excerpt:\n{excerpt}\n\n"
        )

    user_context += f"Question: {question}\n\nProvide a clear, detailed answer based only on the excerpts above."

    return [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_context}
    ]

def get_answer(question):
    """
    Run semantic search to get top posts, build the prompt, and call ChatGPT.
    Returns the answer text.
    """
    # 1) Retrieve top 3 posts (you can increase to 5 if you like)
    hits = semantic_search(question, top_k=3)

    # 2) Build the ChatGPT prompt
    messages = build_prompt(question, hits)

    # 3) Call ChatGPT using the new API endpoint
    response = openai.chat.completions.create(
        model="gpt-4o-mini",      # or another model you prefer
        messages=messages,
        temperature=0.0,
        max_tokens=512
    )

    return response.choices[0].message.content.strip()

# ─── MAIN (CLI MODE) ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 chat_with_context.py \"Your question here\"")
        sys.exit(1)

    question = sys.argv[1]
    answer = get_answer(question)
    print("\n==== AI ANSWER ====\n")
    print(answer)
