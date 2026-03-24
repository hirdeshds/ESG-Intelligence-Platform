from API.database_connectors import db_connector
from bson import ObjectId

class MongoDBHandler:
    def __init__(self):
        self.db = db_connector.get_mongo_db()
        self.collection_name = "raw_firm_data"

    def get_collection(self):
        return self.db[self.collection_name]

    def insert_firm_data(self, data_list):
        """Used by Agent 1 to save the synced SQL data."""
        collection = self.get_collection()
        collection.delete_many({}) # Clear old cache
        if data_list:
            collection.insert_many(data_list)
        return len(data_list)

    def fetch_all_firms(self, filters=None, limit=100):
        """Fetches firms based on criteria (e.g., industry or year)."""
        collection = self.get_collection()
        query = filters if filters else {}
        # Exclude _id because it's not JSON serializable by default
        return list(collection.find(query, {"_id": 0}).limit(limit))

    def fetch_firm_by_id(self, firm_id: str):
        """Fetches a specific firm's ESG profile."""
        collection = self.get_collection()
        return collection.find_one({"Firm_ID": firm_id}, {"_id": 0})

    def get_risk_counts(self):
        """Aggregates alert levels for the dashboard 'Risk Summary'."""
        collection = self.get_collection()
        pipeline = [
            {"$group": {"_id": "$alert_level", "count": {"$sum": 1}}}
        ]
        results = list(collection.aggregate(pipeline))
        
        # Format for frontend: {"Critical": 5, "Warning": 12, ...}
        summary = {res["_id"]: res["count"] for res in results if res["_id"]}
        return summary

# Global instance to be used across the API
mongo_handler = MongoDBHandler()