from fastapi import FastAPI
from pydantic import BaseModel
from agent import run_agent
from memory import get_history

app = FastAPI()

class ChatRequest(BaseModel):
    session_id: str
    message: str
    
@app.get("/")
def home():
     return {"status": "Vet AI Agent running 🚀"}
@app.post("/chat")
def chat(req: ChatRequest):
    response = run_agent(req.session_id, req.message)
    return {"response": response, "history": get_history(req.session_id)}
    