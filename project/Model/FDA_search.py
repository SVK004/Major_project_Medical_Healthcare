import httpx
from fastapi import FastAPI, HTTPException, Query


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


async def get_drugs(
    disease: str, 
    status: str = Query("approved", description="e.g., approved, experimental")
):
    # 1. Try to get data from your MongoDB first (Cache-aside pattern)
    # [Your existing MongoDB logic here]
    
    # 2. If not found or you want fresh data, call FDA
    fda_results = await fetch_from_fda(disease, status)
    
    if not fda_results:
        raise HTTPException(status_code=404, detail="No drugs found on openFDA.")
    
    # Clean up the deep FDA JSON to just what you need
    processed = []
    for item in fda_results:
        # openFDA is nested, we need to check if the 'openfda' key exists first
        openfda_data = item.get("openfda", {})
        
        # Try to get brand_name, if not there, look for generic_name
        brand = openfda_data.get("brand_name", [None])[0]
        generic = openfda_data.get("generic_name", [None])[0]
        
        # Fallback: Some labels have the name in the 'title' or 'description'
        if not brand:
            brand = item.get("title", "Unknown Product").split(',')[0] # Often "Drug Name, Dosage"

        processed.append({
            "brand_name": brand,
            "generic_name": generic or "N/A",
            "manufacturer": openfda_data.get("manufacturer_name", ["N/A"])[0],
            # Adding a snippet of the purpose/indications
            "purpose": item.get("purpose", item.get("indications_and_usage", ["N/A"]))[0][:150] + "..."
        })

# Optional: Filter out the ones that are still "Unknown" to keep the list clean
    filtered_processed = [d for d in processed if d["brand_name"] != "Unknown Product"]    
    return {"source": "openFDA", "data": filtered_processed}