import os
import json
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from openai import AsyncOpenAI
from core.limiter import limiter
from core.config import settings

router = APIRouter()

# Initialize OpenAI client
client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None

# Load knowledge base
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KNOWLEDGE_PATH = os.path.join(BASE_DIR, "knowledge.json")

try:
    with open(KNOWLEDGE_PATH, "r") as f:
        KNOWLEDGE_BASE = json.load(f)
except FileNotFoundError:
    KNOWLEDGE_BASE = {}

SYSTEM_PROMPT = f"""You are the AI assistant for Ujjwal Jha's digital portfolio.
You must answer questions about his professional experience, skills, and projects concisely and accurately.
You are interacting with a recruiter, employer, or peer. Be professional, engaging, and highlight his expertise as a Generative AI & Full-Stack Engineer.

Knowledge Base:
{json.dumps(KNOWLEDGE_BASE, indent=2)}

Rules:
1. Only answer based on the provided knowledge base. If the user asks something completely unrelated, politely inform them you can only answer questions about Ujjwal's work.
2. Provide concise technical explanations (1-3 paragraphs) as requested.
3. If answering about a specific project or architecture, briefly attribute the source (e.g., "In the High-Integrity Wallet project...").
"""

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

@router.post("/chat", response_model=ChatResponse)
@limiter.limit("5/minute")
async def chat_endpoint(request: Request, chat_req: ChatRequest):
    if not client:
        # Fallback/mock mode if no key provided yet
        return ChatResponse(response="AI is currently offline. Please configure the OpenAI API key to enable responses!")
    
    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": chat_req.message}
            ],
            max_tokens=250,
            temperature=0.3
        )
        answer = response.choices[0].message.content
        return ChatResponse(response=answer)
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate AI response. Please try again later.")
