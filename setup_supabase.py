"""
Supabase Database Setup for NYC Heat Wave Risk System
======================================================
Creates tables and populates with synthetic data
"""

import json
import os
from datetime import datetime, timedelta
import random

try:
    from supabase import create_client, Client
except ImportError:
    print("Please install supabase: pip install supabase")
    exit(1)


def load_config():
    """Load Supabase credentials"""
    config_path = os.path.join(os.path.dirname(__file__), "supabase_config.json")
    with open(config_path) as f:
        return json.load(f)


def create_tables(client: Client):
    """Create database tables"""

    # Create neighborhoods table
    client.table("neighborhoods").execute()
    print("✓ Table 'neighborhoods' ready")

    # Create daily_risk table
    client.table("daily_risk").execute()
    print("✓ Table 'daily_risk' ready")

    # Create live_weather table
    client.table("live_weather").execute()
    print("✓ Table 'live_weather' ready")


def insert_neighborhoods(client: Client):
    """Insert NYC neighborhood data"""

    neighborhoods = [
        {"zip_code": "10001", "name": "Chelsea", "borough": "Manhattan", "elderly_pct": 18.5, "ac_pct": 78.2, "poverty_pct": 12.3, "green_space_pct": 15.2, "population": 37000},
        {"zip_code": "10002", "name": "Lower East Side", "borough": "Manhattan", "elderly_pct": 16.2, "ac_pct": 72.5, "poverty_pct": 18.7, "green_space_pct": 8.1, "population": 62000},
        {"zip_code": "10451", "name": "Mott Haven", "borough": "Bronx", "elderly_pct": 14.8, "ac_pct": 45.3, "poverty_pct": 32.1, "green_space_pct": 5.2, "population": 45000},
        {"zip_code": "10453", "name": "Morris Heights", "borough": "Bronx", "elderly_pct": 15.3, "ac_pct": 42.1, "poverty_pct": 35.6, "green_space_pct": 4.8, "population": 38000},
        {"zip_code": "11212", "name": "Brownsville", "borough": "Brooklyn", "elderly_pct": 13.2, "ac_pct": 38.5, "poverty_pct": 38.2, "green_space_pct": 6.1, "population": 52000},
        {"zip_code": "11216", "name": "Bedford-Stuyvesant", "borough": "Brooklyn", "elderly_pct": 12.8, "ac_pct": 55.2, "poverty_pct": 28.4, "green_space_pct": 9.3, "population": 68000},
        {"zip_code": "10035", "name": "East Harlem", "borough": "Manhattan", "elderly_pct": 17.5, "ac_pct": 58.3, "poverty_pct": 25.8, "green_space_pct": 7.2, "population": 55000},
        {"zip_code": "10456", "name": "Highbridge", "borough": "Bronx", "elderly_pct": 14.1, "ac_pct": 41.2, "poverty_pct": 33.5, "green_space_pct": 5.8, "population": 41000},
        {"zip_code": "11101", "name": "Long Island City", "borough": "Queens", "elderly_pct": 13.5, "ac_pct": 68.4, "poverty_pct": 14.2, "green_space_pct": 12.5, "population": 48000},
        {"zip_code": "11368", "name": "Corona", "borough": "Queens", "elderly_pct": 12.1, "ac_pct": 52.3, "poverty_pct": 22.8, "green_space_pct": 8.7, "population": 72000},
        {"zip_code": "10301", "name": "Stapleton", "borough": "Staten Island", "elderly_pct": 16.8, "ac_pct": 65.2, "poverty_pct": 16.5, "green_space_pct": 18.3, "population": 28000},
        {"zip_code": "10303", "name": "Mariners Harbor", "borough": "Staten Island", "elderly_pct": 15.2, "ac_pct": 62.1, "poverty_pct": 18.3, "green_space_pct": 14.2, "population": 32000},
        {"zip_code": "11433", "name": "Jamaica", "borough": "Queens", "elderly_pct": 14.5, "ac_pct": 58.2, "poverty_pct": 19.5, "green_space_pct": 10.1, "population": 58000},
        {"zip_code": "11436", "name": "Queens Village", "borough": "Queens", "elderly_pct": 16.2, "ac_pct": 72.5, "poverty_pct": 12.8, "green_space_pct": 13.5, "population": 42000},
        {"zip_code": "10003", "name": "Greenwich Village", "borough": "Manhattan", "elderly_pct": 19.2, "ac_pct": 85.3, "poverty_pct": 8.5, "green_space_pct": 22.1, "population": 25000},
    ]

    # Clear existing data
    try:
        client.table("neighborhoods").delete().neq("id", 0).execute()
    except:
        pass

    # Insert new data
    for n in neighborhoods:
        client.table("neighborhoods").insert(n).execute()

    print(f"✓ Inserted {len(neighborhoods)} neighborhoods")


def insert_daily_risk(client: Client, days: int = 14):
    """Insert historical risk data"""

    # Base temperatures (vary by borough tendency)
    base_temps = {
        "Manhattan": 85,
        "Bronx": 88,
        "Brooklyn": 86,
        "Queens": 84,
        "Staten Island": 82
    }

    data = []
    dates = [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days, 0, -1)]

    # Load neighborhoods
    response = client.table("neighborhoods").select("*").execute()
    neighborhoods = response.data

    for n in neighborhoods:
        borough = n["borough"]
        base_temp = base_temps.get(borough, 85)

        for i, date in enumerate(dates):
            # Simulate temperature variation
            temp = base_temp + random.uniform(-5, 10)
            humidity = random.uniform(50, 80)
            heat_index = temp + (humidity - 50) / 10  # Simplified

            # Calculate risk score
            elderly = n["elderly_pct"]
            ac = n["ac_pct"]
            poverty = n["poverty_pct"]
            green = n["green_space_pct"]

            # Simple risk formula
            temp_score = min(40, (temp - 60) * 0.8)
            elderly_score = elderly * 0.5
            ac_score = (100 - ac) * 0.3
            poverty_score = poverty * 0.2
            green_score = (20 - green) * 0.2

            risk_score = temp_score + elderly_score + ac_score + poverty_score + green_score
            risk_score = max(0, min(100, risk_score))

            if risk_score >= 75:
                risk_level = "极高"
            elif risk_score >= 50:
                risk_level = "高"
            elif risk_score >= 25:
                risk_level = "中"
            else:
                risk_level = "低"

            data.append({
                "zip_code": n["zip_code"],
                "date": date,
                "temperature": round(temp, 1),
                "humidity": round(humidity, 1),
                "heat_index": round(heat_index, 1),
                "risk_score": round(risk_score, 1),
                "risk_level": risk_level
            })

    # Insert in batches
    batch_size = 50
    for i in range(0, len(data), batch_size):
        batch = data[i:i+batch_size]
        try:
            client.table("daily_risk").insert(batch).execute()
        except Exception as e:
            print(f"Batch {i//batch_size} error: {e}")

    print(f"✓ Inserted {len(data)} daily risk records")


def main():
    """Main setup function"""
    print("=" * 50)
    print("NYC Heat Wave Risk - Supabase Setup")
    print("=" * 50)

    # Load config
    try:
        config = load_config()
    except FileNotFoundError:
        print("❌ Please create supabase_config.json with your credentials")
        print("   Get them from: https://supabase.com/dashboard")
        return

    # Connect to Supabase
    print("\n📡 Connecting to Supabase...")
    client: Client = create_client(config["supabase_url"], config["supabase_anon_key"])

    # Create tables
    print("\n📋 Creating tables...")
    create_tables(client)

    # Insert data
    print("\n📊 Inserting neighborhood data...")
    insert_neighborhoods(client)

    print("\n📊 Inserting historical risk data...")
    insert_daily_risk(client, days=14)

    print("\n" + "=" * 50)
    print("✅ Setup complete!")
    print("=" * 50)


if __name__ == "__main__":
    main()
