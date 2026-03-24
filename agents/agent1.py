import os
import pandas as pd
from API.database_connectors import db_connector
from dotenv import load_dotenv

load_dotenv()

def sync_and_clean_pipeline():
    try:
        # --- STEP 1: FETCH FROM SQL ---
        engine = db_connector.get_sql_engine()
        # Fetching raw data from company DB
        raw_df = pd.read_sql("SELECT * FROM firm_metrics", engine)
        
        if raw_df.empty:
            print(" No data found in Company Database.")
            return

        # --- STEP 2: OPERATIONAL CLEANING (Your Original Logic) ---
        operational_cols = [
            "Firm_ID", "Year", "Industry_Type", 
            "E_Score", "S_Score", "G_Score", "Board_Independence"
        ]
        
        # Ensure only your required columns are kept
        df = raw_df[operational_cols].copy()
        df = df.dropna().reset_index(drop=True)

        # --- STEP 3: SAVE TO MONGODB ---
        db = db_connector.get_mongo_db()
        collection = db[os.getenv("MONGO_COLLECTION", "raw_firm_data")]
        
        # Clear old cache and insert fresh cleaned data
        collection.delete_many({}) 
        collection.insert_many(df.to_dict(orient="records"))
        print(f" Synced {len(df)} cleaned records to MongoDB.")

        # --- STEP 4: EXPORT TO CSV ---
        # Using a relative path consistent with Image 1 structure
        output_dir = "outputs"
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, "agent1_operational_output.csv")
        
        df.to_csv(output_file, index=False)
        print(f" Operational CSV saved at: {output_file}")

    except Exception as e:
        print(f" sync_and_clean_pipeline failed: {e}")
        raise e

if __name__ == "__main__":
    sync_and_clean_pipeline()