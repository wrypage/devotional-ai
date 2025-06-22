import os
import openai
import json

# Ensure your OPENAI_API_KEY is set in the environment
openai.api_key = os.getenv("OPENAI_API_KEY")

question = "How can I have assurance that I am saved?"

response = openai.embeddings.create(
    model="text-embedding-ada-002",
    input=[question]
)
# New client: use response.data[0].embedding
question_embedding = response.data[0].embedding

# Write out the embedding as a JSON array (for later use)
with open("question_embed.json", "w", encoding="utf-8") as f:
    json.dump(question_embedding, f)
print("Saved question embedding to question_embed.json")
