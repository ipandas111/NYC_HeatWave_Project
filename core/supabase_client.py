"""
Supabase Database Client for NYC Heat Wave Risk System
=====================================================
"""

import json
import os
from typing import Optional, List, Dict
from supabase import create_client, Client

# Load config
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "supabase_config.json")


def get_supabase_client() -> Optional[Client]:
    """Get Supabase client"""
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH) as f:
                config = json.load(f)
                return create_client(config["supabase_url"], config["supabase_anon_key"])
    except Exception as e:
        print(f"Supabase connection error: {e}")
    return None


class Database:
    """Database operations using Supabase"""

    def __init__(self):
        self.client = get_supabase_client()

    def is_connected(self) -> bool:
        """Check if database is connected"""
        if self.client is None:
            return False
        try:
            self.client.table("neighborhoods").select("*").limit(1).execute()
            return True
        except:
            return False

    def get_all_neighborhoods(self) -> List[Dict]:
        """Get all neighborhoods"""
        if not self.client:
            return []
        try:
            response = self.client.table("neighborhoods").select("*").execute()
            return response.data
        except Exception as e:
            print(f"Error fetching neighborhoods: {e}")
            return []

    def get_neighborhood(self, zip_code: str) -> Optional[Dict]:
        """Get single neighborhood by zip code"""
        if not self.client:
            return None
        try:
            response = self.client.table("neighborhoods").select("*").eq("zip_code", zip_code).execute()
            if response.data:
                return response.data[0]
        except Exception as e:
            print(f"Error fetching neighborhood: {e}")
        return None

    def get_latest_weather(self) -> Optional[Dict]:
        """Get latest weather data"""
        if not self.client:
            return None
        try:
            response = self.client.table("weather").select("*").order("date", desc=True).limit(1).execute()
            if response.data:
                return response.data[0]
        except Exception as e:
            print(f"Error fetching weather: {e}")
        return None

    def get_daily_risk(self, zip_code: str, days: int = 14) -> List[Dict]:
        """Get daily risk for a neighborhood"""
        if not self.client:
            return []
        try:
            response = (
                self.client.table("daily_risk")
                .select("*")
                .eq("zip_code", zip_code)
                .order("date", desc=True)
                .limit(days)
                .execute()
            )
            return response.data
        except Exception as e:
            print(f"Error fetching daily risk: {e}")
            return []

    def get_all_latest_risk(self) -> List[Dict]:
        """Get latest risk for all neighborhoods"""
        if not self.client:
            return []
        try:
            # Get distinct zip_codes with their latest date
            neighborhoods = self.get_all_neighborhoods()
            results = []
            for n in neighborhoods:
                risk = self.get_daily_risk(n["zip_code"], 1)
                if risk:
                    r = risk[0]
                    r["name"] = n["name"]
                    r["borough"] = n["borough"]
                    results.append(r)
            return results
        except Exception as e:
            print(f"Error fetching all risk: {e}")
            return []

    def get_historical_average(self, days: int = 14) -> float:
        """Get average risk score for last N days"""
        if not self.client:
            return 0
        try:
            # Get recent data
            response = (
                self.client.table("daily_risk")
                .select("risk_score")
                .order("date", desc=True)
                .limit(days * 15)  # 15 neighborhoods
                .execute()
            )
            if response.data:
                scores = [r["risk_score"] for r in response.data if r.get("risk_score")]
                return sum(scores) / len(scores) if scores else 0
        except Exception as e:
            print(f"Error fetching historical average: {e}")
        return 0


# Example usage
if __name__ == "__main__":
    db = Database()
    print(f"Connected: {db.is_connected()}")

    if db.is_connected():
        neighborhoods = db.get_all_neighborhoods()
        print(f"Neighborhoods: {len(neighborhoods)}")

        weather = db.get_latest_weather()
        print(f"Latest weather: {weather}")
