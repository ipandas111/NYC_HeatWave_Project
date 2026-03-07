"""
Real NYC Data Sources Integration
=================================
This module provides functions to fetch real NYC data for the Heat Wave Risk System.

Data Sources:
1. NYC Open Data - Various environmental and demographic datasets
2. NOAA National Weather Service - Real-time weather data
3. US Census Bureau - Demographic data

API Endpoints:
- NYC Open Data: https://data.cityofnewyork.us/api/views/
- NOAA: https://api.weather.gov/
- Census: https://api.census.gov/
"""

try:
    import requests
except ImportError:
    requests = None

import pandas as pd
from typing import Optional, Dict, List
from datetime import datetime


class NYCRealDataLoader:
    """Loader for real NYC data from various sources"""

    # NYC Open Data Socrata API base
    SODA_BASE = "https://data.cityofnewyork.us/resource/"

    # Known dataset endpoints
    DATASETS = {
        # NYC Neighborhood Statistics
        "neighborhood_stats": "hhdx-uv46.json",
        # Tree census (green space)
        "tree_census": "5rq2-4hqu.json",
        # Air quality
        "air_quality": "ia6d-86ji.json",
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})

    def get_noaa_weather(self, station_id: str = "KNYC", date: str = None) -> Optional[Dict]:
        """
        Get real weather data from NOAA API

        Args:
            station_id: Weather station ID (default: KNYC - Central Park)
            date: Date in YYYY-MM-DD format (default: today)

        Returns:
            Weather data dict or None
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        # NOAA API v2 - requires API key registration
        # For demo, returning structure
        base_url = f"https://api.weather.gov/stations/{station_id}/observations/{date}"

        try:
            response = self.session.get(base_url, timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"NOAA API error: {e}")

        return None

    def get_nyc_neighborhood_data(self) -> pd.DataFrame:
        """
        Fetch NYC neighborhood statistics from NYC Open Data

        Uses the neighborhood tabulation areas (NTA) data
        """
        # NYC NTA (Neighborhood Tabulation Areas) data
        # This is a placeholder - real implementation would use specific dataset
        nta_url = f"{self.SODA_BASE}hhdx-uv46.json"

        try:
            response = self.session.get(nta_url, timeout=30)
            if response.status_code == 200:
                return pd.DataFrame(response.json())
        except Exception as e:
            print(f"NYC Open Data error: {e}")

        return pd.DataFrame()

    def get_census_demographics(self, zip_codes: List[str]) -> pd.DataFrame:
        """
        Get Census demographic data for ZIP codes

        Uses US Census Bureau API

        Args:
            zip_codes: List of ZIP codes

        Returns:
            DataFrame with demographic data
        """
        # Census API variables:
        # B01001_001E - Total population
        # B01001_020E - Male 65+
        # B01001_044E - Female 65+
        # B19013_001E - Median household income (poverty proxy)

        base_url = "https://api.census.gov/data/2022/acs/acs5"

        params = {
            "get": "B01001_001E,B01001_020E,B01001_044E,B19013_001E",
            "for": "zip code tabulation area:" + ",".join(zip_codes)
        }

        try:
            response = self.session.get(base_url, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                # First row is headers
                df = pd.DataFrame(data[1:], columns=data[0])
                return df
        except Exception as e:
            print(f"Census API error: {e}")

        return pd.DataFrame()

    def get_green_space_data(self, boro: str = "Manhattan") -> pd.DataFrame:
        """
        Get NYC tree canopy/green space data

        Source: NYC Street Tree Census
        """
        # NYC Street Tree Census - 2015/2022 data
        tree_url = f"{self.SODA_BASE}5rq2-4hqu.json"

        params = {"boro": boro.lower()}

        try:
            response = self.session.get(tree_url, params=params, timeout=30)
            if response.status_code == 200:
                return pd.DataFrame(response.json())
        except Exception as e:
            print(f"Tree data error: {e}")

        return pd.DataFrame()


def fetch_live_weather() -> Dict:
    """
    Fetch live weather for NYC

    Uses Open-Meteo API (free, no API key required)
    """
    if requests is None:
        return {"error": "requests library not installed"}

    # NYC coordinates
    lat, lon = 40.7128, -74.0060

    url = f"https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature",
        "timezone": "America/New_York"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            current = data.get("current", {})
            return {
                "temperature": current.get("temperature_2m"),
                "humidity": current.get("relative_humidity_2m"),
                "apparent_temperature": current.get("apparent_temperature"),
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        print(f"Weather API error: {e}")

    return {}


def fetch_historical_weather(date_str: str) -> Dict:
    """
    Fetch historical weather for NYC on a specific date.

    Uses Open-Meteo Archive API (free, no API key required).
    Covers data from 1940 to 5 days ago.

    Args:
        date_str: Date in YYYY-MM-DD format

    Returns:
        Dict with temperature, humidity, apparent_temperature
    """
    if requests is None:
        return {"error": "requests library not installed"}

    lat, lon = 40.7128, -74.0060

    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": date_str,
        "end_date": date_str,
        "daily": "temperature_2m_max,temperature_2m_min,temperature_2m_mean,apparent_temperature_max,apparent_temperature_min",
        "hourly": "relative_humidity_2m",
        "timezone": "America/New_York"
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            daily = data.get("daily", {})
            hourly = data.get("hourly", {})

            temp_mean = daily.get("temperature_2m_mean", [None])[0]
            temp_max = daily.get("temperature_2m_max", [None])[0]
            apparent_max = daily.get("apparent_temperature_max", [None])[0]

            # Average humidity from hourly data
            humidity_values = hourly.get("relative_humidity_2m", [])
            avg_humidity = sum(v for v in humidity_values if v is not None) / len(humidity_values) if humidity_values else None

            # Use max temp as the representative daytime temperature
            temp = temp_max if temp_max is not None else temp_mean
            apparent = apparent_max if apparent_max is not None else temp

            return {
                "temperature": temp,
                "humidity": round(avg_humidity) if avg_humidity is not None else 50,
                "apparent_temperature": apparent,
                "temp_mean": temp_mean,
                "temp_max": temp_max,
                "date": date_str,
                "timestamp": date_str
            }
    except Exception as e:
        print(f"Historical weather API error: {e}")

    return {"error": f"Failed to fetch historical data for {date_str}"}


# Example usage
if __name__ == "__main__":
    # Test live weather
    print("=== Testing Live Weather ===")
    weather = fetch_live_weather()
    print(f"Weather: {weather}")

    # Test data loader
    print("\n=== Testing NYC Data Loader ===")
    loader = NYCRealDataLoader()

    # Try to get neighborhood data
    neighborhoods = loader.get_nyc_neighborhood_data()
    print(f"NYC neighborhoods: {len(neighborhoods)} records")
