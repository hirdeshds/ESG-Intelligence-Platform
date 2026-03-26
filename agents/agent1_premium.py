import os
import json
import time
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[1]
CONFIG_DIR = BASE_DIR / "config"


def _resolve_mapping_file(company_id):
    candidates = [
        CONFIG_DIR / f"{company_id}_mapping.json",
        CONFIG_DIR / f"{company_id.replace('company', 'company_')}_mapping.json",
    ]
    for path in candidates:
        if path.exists():
            return path
    return None

def run_agent1_premium(emit_callback, company_id="company3"):
    """
     AGENT 1 PRIME (PREMIUM): 
    Real-time MongoDB Listener using a robust while-loop.
    """
    print(f" Agent 1 Premium: Real-time Listener active for {company_id}...")

    # 1. Load the Client Mapping
    mapping_file = _resolve_mapping_file(company_id)
    client_mapping = None
    if mapping_file:
        with open(mapping_file, "r", encoding="utf-8") as f:
            client_mapping = json.load(f)
    else:
        print(f" Warning: Mapping file missing for {company_id}. Falling back to raw document passthrough.")

    # 2. Setup MongoDB Connection
    uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    db_name = os.getenv("MONGO_DB_NAME", company_id)
    collection_name = os.getenv("MONGO_COLLECTION", "raw_firm_data")

    # While loop recursion se bachata hai aur auto-reconnect handle karta hai
    while True:
        try:
            client = MongoClient(uri)
            collection = client[db_name][collection_name]

            # 3. Watch for Live Insertions (updateLookup helps with data consistency)
            pipeline = [{"$match": {"operationType": "insert"}}]
            
            with collection.watch(pipeline, full_document="updateLookup") as stream:
                print(f" Change Stream connected. Watching {collection_name}...")
                
                for change in stream:
                    raw_doc = change['fullDocument']
                    
                    # 4. Standardize the Data
                    if client_mapping:
                        standardized_data = {}
                        for standard_col, client_col in client_mapping.items():
                            standardized_data[standard_col] = raw_doc.get(client_col)
                    else:
                        standardized_data = {k: v for k, v in raw_doc.items() if k != "_id"}

                    # Add Metadata
                    standardized_data["Firm_ID"] = raw_doc.get("Firm_ID", "Unknown")
                    standardized_data["Sync_Time"] = time.strftime('%H:%M:%S')
                    standardized_data["Type"] = "PREMIUM_REALTIME_MAPPED"

                    # 5. Emit via WebSocket Callback
                    # Is 'event_name' ko frontend par listen karein
                    emit_callback('agent1_live_operational', standardized_data)
                    
                    print(f" [Agent 1 Premium] Streamed data for: {standardized_data['Firm_ID']}")

        except Exception as e:
            error_text = str(e)
            if "only supported on replica sets" in error_text:
                print(" Agent 1 Premium requires MongoDB replica set for Change Streams. Stopping listener.")
                if 'client' in locals():
                    client.close()
                break

            print(f" Agent 1 Premium connection lost: {e}. Retrying in 5 seconds...")
            if 'client' in locals():
                client.close()
            time.sleep(5) 
            continue # Loop dubara start hoga bina recursion depth badhaye