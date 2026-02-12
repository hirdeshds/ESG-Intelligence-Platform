import os
from fastapi import FastAPI
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize FastAPI
app = FastAPI()

# Load ESG context from file
with open("esg_context.txt", "r", encoding="utf-8") as file:
    ESG_CONTEXT = file.read()

@app.get("/")
def home():
    return {"message": "ESG AI Chatbot is running 🚀"}

@app.get("/chat")
def chat(prompt: str):

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": f"""
                You are an ESG AI assistant.
                Answer ONLY using the following context.
                If answer is not found in context,
                say: 'This information is not available in the ESG system.'

                Context:
                {ESG_CONTEXT}
                """
            },
            {"role": "user", "content": prompt}
        ]
    )

    return {"response": response.choices[0].message.content}

