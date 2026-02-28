import httpx
from fastapi import FastAPI, HTTPException, Query
from typing import List, Optional
# Ensure these imports exist and don't import 'app' back into themselves!
from Model.FDA_search import get_drugs, fetch_from_fda 
from Model.RAG_model import ai_diagnose

app = FastAPI()

# 1. Renamed to avoid shadowing inside the function
DEFAULT_KNOWLEDGE_CHUNKS = [
    "Symptom: memory loss, confusion, disorientation. Disease: Alzheimers",
    "Symptom: high blood sugar, excessive thirst, frequent urination. Disease: Diabetes",
    "Symptom: wheezing, shortness of breath, chest tightness. Disease: Asthma"
]

@app.get("/search-drugs")
async def search_drugs(
    disease: str, 
    status: str = Query("approved", description="e.g., approved, experimental")
):
    return await get_drugs(disease, status)

@app.get("/ai-diagnose")
async def ai_diagnose_endpoint(
    symptoms: str = Query(..., description="Describe your symptoms"), 
    knowledge_chunks: Optional[List[str]] = Query(None)
):
    # 2. Logic fix: If URL params are empty, use the DEFAULT list
    chunks_to_use = knowledge_chunks if knowledge_chunks else DEFAULT_KNOWLEDGE_CHUNKS
    
    try:
        return await ai_diagnose(symptoms, chunks_to_use)
    except Exception as e:
        # This will show you the ACTUAL error in your terminal
        print(f"CRITICAL ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))