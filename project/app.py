import httpx
from fastapi import FastAPI, HTTPException, Query
from typing import List, Optional
from Model.FDA_search import get_drugs
from Model.RAG_model import ai_diagnose

app = FastAPI()

# Mock RAG source (Replace with your load_rag_data() function)
RAG_DATA_SOURCE = """
Symptom: memory loss, confusion, disorientation. Disease: Alzheimer
Symptom: high blood sugar, excessive thirst, frequent urination. Disease: Diabetes
Symptom: wheezing, shortness of breath, chest tightness. Disease: Asthma
"""
knowledge_chunks = [line.strip() for line in RAG_DATA_SOURCE.splitlines() if line.strip()]



async def fetch_from_fda(disease: str, status: str):
    # 1. Clean the disease name
    clean_disease = disease.replace("'", "").strip()
    
    # 2. Switch to the LABEL endpoint for better matches
    # This searches the 'indications_and_usage' section of the drug label
    label_url = "https://api.fda.gov/drug/label.json"
    
    # 3. Construct a broader query
    # We search for the disease in the indications and filter by product type
    search_query = f'indications_and_usage:"{clean_disease}"'
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            label_url, 
            params={"search": search_query, "limit": 10},
            timeout=10.0
        )
        
        # Log this to your terminal to see the actual FDA call!
        print(f"DEBUG: FDA URL: {response.url}")
        
        if response.status_code != 200:
            return None
        
        return response.json().get("results", [])
@app.get("/search-drugs")
async def search_drugs(
    disease: str, 
    status: str = Query("approved", description="e.g., approved, experimental")
):
    return await get_drugs(disease, status)


@app.get("/ai-diagnose")
async def ai_diagnose_endpoint(symptoms: str = Query(..., description="Describe your symptoms")):
    return await ai_diagnose(symptoms, knowledge_chunks)