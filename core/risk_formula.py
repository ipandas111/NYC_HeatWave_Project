"""
NYC Heat Wave Risk Assessment System
=====================================
Based on NWS Heat Index Formula + Heat Vulnerability Index (HVI) Framework

NWS Heat Index: https://en.wikipedia.org/wiki/Heat_index
"""

from dataclasses import dataclass
from typing import Dict


def calculate_heat_index(T: float, RH: float) -> float:
    """
    Calculate NWS Heat Index (体感温度)

    Args:
        T: Temperature in Fahrenheit
        RH: Relative Humidity in percentage

    Returns:
        Heat Index in Fahrenheit

    Note: Formula is valid for T >= 80°F and RH >= 40%
    """
    # Apply the NWS Heat Index formula
    HI = (-42.379 +
           2.04901523 * T +
           10.14333127 * RH -
           0.22475541 * T * RH -
           0.00683783 * T**2 -
           0.05481717 * RH**2 +
           0.00122874 * T**2 * RH +
           0.00085282 * T * RH**2 -
           0.00000199 * T**2 * RH**2)

    # If conditions don't meet threshold, return actual temp
    if T < 80 or RH < 40:
        return T

    return max(HI, T)


def get_risk_level(score: float) -> tuple:
    """
    Determine risk level based on score

    Args:
        score: Risk score (0-100)

    Returns:
        (level_name, color_emoji, description)
    """
    if score >= 75:
        return ("极高", "🔴", "紧急状态 - 立即采取行动")
    elif score >= 50:
        return ("高", "🟠", "预警状态 - 需要关注")
    elif score >= 25:
        return ("中", "🟡", "关注状态 - 保持警惕")
    else:
        return ("低", "🟢", "正常状态")


def calculate_heat_risk(
    temperature: float,      # Temperature in °F
    humidity: float,        # Humidity in %
    elderly_pct: float,    # Elderly population (65+) percentage
    ac_pct: float,         # AC coverage percentage
    poverty_pct: float,   # Poverty rate percentage
    green_space_pct: float # Green space coverage percentage
) -> Dict:
    """
    Calculate comprehensive heat risk score based on NWS Heat Index + HVI Framework

    Args:
        temperature: Air temperature in Fahrenheit
        humidity: Relative humidity in percentage
        elderly_pct: Percentage of population aged 65+
        ac_pct: Percentage of households with AC
        poverty_pct: Poverty rate percentage
        green_space_pct: Green space coverage percentage

    Returns:
        Dictionary with risk score, level, and breakdown
    """

    # ======== Step 1: Calculate Heat Index ========
    heat_index = calculate_heat_index(temperature, humidity)

    # ======== Step 2: Calculate component scores ========

    # Temperature/Heat Index Score (0-30 points)
    # Based on NWS risk categories
    if heat_index >= 130:
        temp_score = 30
    elif heat_index >= 105:
        temp_score = 20 + (heat_index - 105) / 25 * 10
    elif heat_index >= 90:
        temp_score = 10 + (heat_index - 90) / 15 * 10
    else:
        temp_score = max(0, heat_index / 90 * 10)

    # Population Vulnerability Score (0-30 points)
    # Elderly (60%) + Poverty (40%)
    pop_vulnerability = elderly_pct * 0.6 + poverty_pct * 0.4
    pop_score = min(30, pop_vulnerability * 0.3)

    # AC Coverage Score (0-20 points)
    # Penalty for lack of AC
    ac_score = (100 - ac_pct) * 0.20

    # Environment Vulnerability Score (0-20 points)
    # Penalty for lack of green space
    green_score = (100 - green_space_pct) * 0.20

    # ======== Step 3: Calculate total score ========
    total_score = temp_score + pop_score + ac_score + green_score

    # Clamp to 0-100
    total_score = min(100, max(0, round(total_score, 1)))

    # ======== Step 4: Determine risk level ========
    risk_level, color, description = get_risk_level(total_score)

    return {
        "risk_score": total_score,
        "risk_level": risk_level,
        "color": color,
        "description": description,
        "heat_index": round(heat_index, 1),
        "breakdown": {
            "temperature": round(temp_score, 1),
            "population": round(pop_score, 1),
            "ac_coverage": round(ac_score, 1),
            "environment": round(green_score, 1)
        }
    }


# Example usage
if __name__ == "__main__":
    # Test with Mott Haven data
    result = calculate_heat_risk(
        temperature=98,
        humidity=88,
        elderly_pct=18,
        ac_pct=45,
        poverty_pct=32,
        green_space_pct=5
    )

    print("Mott Haven Risk Assessment:")
    print(f"  Risk Score: {result['risk_score']}")
    print(f"  Risk Level: {result['color']} {result['risk_level']}")
    print(f"  Heat Index: {result['heat_index']}°F")
    print(f"  Breakdown: {result['breakdown']}")
