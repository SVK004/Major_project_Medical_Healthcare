from .FDA_search import fetch_from_fda
import httpx
from fastapi import HTTPException, Query
import requests
import os

HF_API_URL = "https://router.huggingface.co/featherless-ai/v1/completions"
HEADERS = {"Authorization": f"Bearer {os.getenv('HUGGINGFACE_API_KEY')}"}

async def ai_diagnose(symptoms: str = str, knowledge_chunks = []):
    """This is the RAG endpoint using Llama-3.1-8B"""
    
    # 1. Retrieval (Basic keyword match for now)
    input_words = set(symptoms.lower().split())
    context = "\n".join([c for c in knowledge_chunks if any(w in c.lower() for w in input_words)])
    
    # 2. Llama 3.1 Prompting
    llama_prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
    Identify the disease from the context. Output ONLY the name. If unknown, say Unknown.
    Context: {context}
    <|eot_id|><|start_header_id|>user<|end_header_id|>
    Symptoms: {symptoms}
    Disease: <|eot_id|><|start_header_id|>assistant<|end_header_id|>"""

    # 3. Request to Hugging Face
    payload = {
        "model": "meta-llama/Meta-Llama-3.1-8B-Instruct",
        "prompt": llama_prompt,
        "temperature": 0.1,
        "max_tokens": 20,
        "stop": ["<|eot_id|>"]
    }
    
    hf_res = requests.post(HF_API_URL, headers=HEADERS, json=payload)
    
    if hf_res.status_code != 200:
        raise HTTPException(status_code=500, detail="AI service currently unavailable.")
        
    disease_name = hf_res.json()['choices'][0]['text'].strip()

    if "Unknown" in disease_name or not disease_name:
        raise HTTPException(status_code=404, detail="Could not map symptoms to a known disease.")

    # 4. Trigger the shared FDA search logic
    data = await fetch_from_fda(disease_name)
    
    return {
        "source": "AI-RAG-Diagnosis",
        "identified_disease": disease_name,
        "symptoms": symptoms,
        "data": data
    }