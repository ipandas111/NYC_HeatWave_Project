"""
Data Loader for NYC Heat Wave Risk System
=========================================
Loads and manages neighborhood and heat data from CSV files
"""

import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime, timedelta


class DataLoader:
    """Data loader for neighborhood and heat risk data"""

    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize data loader

        Args:
            data_dir: Directory containing CSV files. Defaults to project data folder
        """
        if data_dir is None:
            # Default to project data folder
            base_dir = Path(__file__).parent.parent
            data_dir = base_dir

        self.data_dir = Path(data_dir)
        self.neighborhoods_file = self.data_dir / "neighborhoods.csv"
        self.heat_data_file = self.data_dir / "daily_heat_data.csv"

        self.neighborhoods = None
        self.heat_data = None
        self._load_data()

    def _load_data(self):
        """Load data from CSV files"""
        try:
            self.neighborhoods = pd.read_csv(self.neighborhoods_file)
            self.heat_data = pd.read_csv(self.heat_data_file)

            # Convert date column to datetime
            self.heat_data['date'] = pd.to_datetime(self.heat_data['date'])

            print(f"Loaded {len(self.neighborhoods)} neighborhoods")
            print(f"Loaded {len(self.heat_data)} heat data records")

        except FileNotFoundError as e:
            print(f"Error loading data: {e}")
            print("Please ensure neighborhoods.csv and daily_heat_data.csv are in the data directory")

    def get_all_neighborhoods(self) -> pd.DataFrame:
        """Get all neighborhoods"""
        return self.neighborhoods

    def get_neighborhood(self, zip_code: str) -> Optional[Dict]:
        """Get single neighborhood by ZIP code"""
        # Convert zip_code to int for comparison
        try:
            zip_int = int(zip_code)
            row = self.neighborhoods[self.neighborhoods['zip_code'] == zip_int]
        except (ValueError, TypeError):
            row = self.neighborhoods[self.neighborhoods['zip_code'].astype(str) == zip_code]
        if len(row) > 0:
            return row.iloc[0].to_dict()
        return None

    def get_latest_heat_data(self, zip_code: str) -> Optional[Dict]:
        """Get latest heat data for a ZIP code"""
        try:
            zip_int = int(zip_code)
            data = self.heat_data[self.heat_data['zip_code'] == zip_int]
        except (ValueError, TypeError):
            data = self.heat_data[self.heat_data['zip_code'].astype(str) == zip_code]
        if len(data) > 0:
            latest = data.loc[data['date'].idxmax()]
            return latest.to_dict()
        return None

    def get_heat_data_by_date(self, zip_code: str, date: str) -> Optional[Dict]:
        """Get heat data for a specific ZIP code and date"""
        date = pd.to_datetime(date)
        try:
            zip_int = int(zip_code)
            data = self.heat_data[
                (self.heat_data['zip_code'] == zip_int) &
                (self.heat_data['date'] == date)
            ]
        except (ValueError, TypeError):
            data = self.heat_data[
                (self.heat_data['zip_code'].astype(str) == zip_code) &
                (self.heat_data['date'] == date)
            ]
        if len(data) > 0:
            return data.iloc[0].to_dict()
        return None

    def get_heat_trend(self, zip_code: str, days: int = 7) -> pd.DataFrame:
        """Get heat risk trend for last N days"""
        try:
            zip_int = int(zip_code)
            data = self.heat_data[
                self.heat_data['zip_code'] == zip_int
            ].sort_values('date', ascending=False).head(days)
        except (ValueError, TypeError):
            data = self.heat_data[
                self.heat_data['zip_code'].astype(str) == zip_code
            ].sort_values('date', ascending=False).head(days)

        return data.sort_values('date', ascending=True)

    def get_all_latest_data(self) -> pd.DataFrame:
        """Get latest heat data for all neighborhoods"""
        latest = self.heat_data.loc[
            self.heat_data.groupby('zip_code')['date'].idxmax()
        ]

        # Merge with neighborhood info
        result = latest.merge(
            self.neighborhoods,
            on='zip_code',
            how='left'
        )

        return result

    def get_high_risk_neighborhoods(self, threshold: float = 50) -> pd.DataFrame:
        """Get neighborhoods with risk score above threshold"""
        latest = self.get_all_latest_data()
        return latest[latest['risk_score'] >= threshold]

    def get_borough_summary(self) -> Dict:
        """Get summary by borough"""
        latest = self.get_all_latest_data()

        summary = {}
        for borough in latest['borough'].unique():
            borough_data = latest[latest['borough'] == borough]
            summary[borough] = {
                'count': len(borough_data),
                'avg_risk': round(borough_data['risk_score'].mean(), 1),
                'max_risk': borough_data['risk_score'].max(),
                'high_risk_count': len(borough_data[borough_data['risk_score'] >= 50])
            }

        return summary

    def get_date_range(self) -> tuple:
        """Get the date range of heat data"""
        return (self.heat_data['date'].min(), self.heat_data['date'].max())

    def get_historical_average(self, days: int = 14) -> float:
        """Get average risk score across all neighborhoods for the last N days"""
        recent_data = self.heat_data.tail(days * len(self.neighborhoods))
        if len(recent_data) > 0:
            return recent_data['risk_score'].mean()
        return 0

    def get_risk_acceleration(self) -> list:
        """Calculate risk change from yesterday to today for each neighborhood"""
        # Get unique dates sorted
        dates = sorted(self.heat_data['date'].unique())
        if len(dates) < 2:
            return []

        yesterday = dates[-2]
        today = dates[-1]

        yesterday_data = self.heat_data[self.heat_data['date'] == yesterday][['zip_code', 'risk_score']]
        today_data = self.heat_data[self.heat_data['date'] == today][['zip_code', 'risk_score']]

        # Merge and calculate change
        merged = today_data.merge(yesterday_data, on='zip_code', suffixes=('_today', '_yesterday'))
        merged['change'] = merged['risk_score_today'] - merged['risk_score_yesterday']

        # Get neighborhood names
        merged = merged.merge(self.neighborhoods[['zip_code', 'name']], on='zip_code')

        # Sort by change (descending)
        return merged.sort_values('change', ascending=False).to_dict('records')


# Example usage
if __name__ == "__main__":
    # Load data
    loader = DataLoader()

    # Get all neighborhoods
    print("\nAll Neighborhoods:")
    print(loader.get_all_neighborhoods()[['zip_code', 'name', 'borough']])

    # Get latest data for all
    print("\nLatest Heat Data:")
    latest = loader.get_all_latest_data()
    print(latest[['name', 'temperature', 'humidity', 'risk_score', 'risk_level']])

    # Get Mott Haven data
    print("\nMott Haven (10451):")
    nh = loader.get_neighborhood("10451")
    heat = loader.get_latest_heat_data("10451")
    print(f"  Name: {nh['name']}")
    print(f"  Temperature: {heat['temperature']}°F")
    print(f"  Humidity: {heat['humidity']}%")
    print(f"  Risk Score: {heat['risk_score']}")

    # Get trend
    print("\n7-Day Trend for 10451:")
    trend = loader.get_heat_trend("10451", 7)
    print(trend[['date', 'temperature', 'risk_score']])
