import os
import psycopg2
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Any

# Import the new OpenAI client (v1.x interface)
from openai import OpenAI

# PostgreSQL connection parameters
DB_NAME = "selahdevotional"
DB_USER = "selah"
DB_PASSWORD = os.getenv("DB_PASSWORD")  # Or hardcode if you prefer
DB_HOST = "localhost"
DB_PORT = 5432

# Number of nearest posts to retrieve
TOP_K = 5

# Instantiate a single OpenAI client (uses OPENAI_API_KEY from environment)
client = OpenAI()

app = FastAPI()

class QuestionRequest(BaseModel):
    question: str

def get_db_connection():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )

def embed_text(text: str) -> List[float]:
    """
    Create an embedding for the given text using OpenAI Embeddings API.
    """
    try:
        resp = client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return resp.data[0].embedding
    except Exception as e:
        raise RuntimeError(f"Embedding call failed: {e}")

def get_top_k_posts(question_embedding: List[float], k: int = TOP_K) -> List[Any]:
    """
    Query the database for the top k blog posts whose embeddings
    are closest (by cosine similarity) to the question_embedding.
    """
    emb_str = "[" + ", ".join(str(x) for x in question_embedding) + "]"
    query = f"""
        SELECT post_title, post_content, post_url
        FROM blog_posts
        ORDER BY embedding <-> '{emb_str}'
        LIMIT {k};
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(query)
    results = cur.fetchall()
    cur.close()
    conn.close()
    return results

def compose_prompt(question: str, top_posts: List[Any]) -> str:
    """
    Build a prompt that:
      1. Speaks in Pastor Ray’s warm, pastoral style.
      2. Uses the New King James Version (NKJV) exclusively for all Scripture quotations.
      3. When answering:
         • Include at least 4–5 distinct Scripture citations (NKJV).
         • If you decide to reference a blog post to clarify a point, find the first Bible reference 
           in that excerpt’s content and introduce it by choosing exactly one of these phrases:
             – “As I shared in my devotional about [BIBLE_REFERENCE], <a href=\"[POST_URL]\" target=\"_blank\">[POST_TITLE]</a>, …”
             – “In my post on [BIBLE_REFERENCE], <a href=\"[POST_URL]\" target=\"_blank\">[POST_TITLE]</a>, …”
             – “Reflecting on [BIBLE_REFERENCE] in my devotional, <a href=\"[POST_URL]\" target=\"_blank\">[POST_TITLE]</a>, …”
           (Replace [BIBLE_REFERENCE] with the verse you found, [POST_TITLE] with the post_title field, 
           and [POST_URL] with the post_url.)
         • Do NOT invent or assume any verse not actually present.
         • If the post_title is a date (like “March 19, 2025”), link exactly that.
      4. Otherwise, answer naturally without any “As I shared…” opening.
      5. Write full paragraphs—no numbered lists or bullet points.
      6. Return HTML-ready text so the front end can render it via innerHTML.
    """
    system_message = (
        "You are Pastor Ray, in a warm, pastoral voice, using the New King James Version (NKJV) exclusively for all Scripture quotations.\n"
        "When answering:\n"
        "  • Include at least 4–5 distinct NKJV Scripture citations (book chapter:verse).\n"
        "  • If referencing a specific blog post, do the following:\n"
        "      1) Look at the excerpt’s content and find the very first Bible verse reference (for example, “John 3:16” or “Romans 8:28”).\n"
        "      2) Choose exactly one of these optional introductory phrases:\n"
        "           – “As I shared in my devotional about [BIBLE_REFERENCE], <a href=\"[POST_URL]\" target=\"_blank\">[POST_TITLE]</a>, …”\n"
        "           – “In my post on [BIBLE_REFERENCE], <a href=\"[POST_URL]\" target=\"_blank\">[POST_TITLE]</a>, …”\n"
        "           – “Reflecting on [BIBLE_REFERENCE] in my devotional, <a href=\"[POST_URL]\" target=\"_blank\">[POST_TITLE]</a>, …”\n"
        "         (Replace [BIBLE_REFERENCE] with the verse you found, [POST_TITLE] with the post_title field, and [POST_URL] with the post_url.)\n"
        "      3) Do NOT assume any other verse—only use what appears in that excerpt.\n"
        "      4) If the post_title happens to be a date (like “March 19, 2025”), link exactly that.\n"
        "  • Otherwise, answer naturally without any “As I shared…” opening.\n"
        "Write full paragraphs—no numbered lists or bullet points. Return HTML-ready text so the front end can render it via innerHTML.\n"
    )

    prompt = system_message
    prompt += f"Question: {question}\n\n"
    prompt += "Relevant Blog Post Excerpts (Title, URL, Content):\n"
    for idx, (title, content, url) in enumerate(top_posts, start=1):
        prompt += (
            f"\nExcerpt {idx}:\n"
            f"Title: {title}\n"
            f"URL: {url}\n"
            f"Content: {content}\n"
        )
    prompt += "\nAnswer the question below, following the instructions above.\n"
    prompt += "Answer:\n"
    return prompt

@app.post("/ask")
async def ask_question(req: QuestionRequest):
    question = req.question

    # 1) Embed the user question
    try:
        question_embedding = embed_text(question)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error embedding question: {e}")

    # 2) Fetch top K similar posts from the database
    try:
        top_posts = get_top_k_posts(question_embedding, TOP_K)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query failed: {e}")

    # 3) Compose the ChatCompletion prompt
    prompt_text = compose_prompt(question, top_posts)

    # 4) Query the OpenAI ChatCompletion API, with increased tokens
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt_text.split("\n")[0]},
                {"role": "user", "content": prompt_text}
            ],
            max_tokens=800,
            temperature=0.7
        )
        answer = response.choices[0].message.content.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI API request failed: {e}")

    return {"answer": answer}

@app.get("/")
async def root():
    return {"message": "Selah Q&A API is running."}
