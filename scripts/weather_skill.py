#!/usr/bin/env python3
"""
Weather Skill for The Alfred Report

Fetches 4-day forecast from weather.gov API for Arlington, VA
Returns formatted section dict ready for JSON serialization
"""

import json
from datetime import datetime
from typing import Dict

def get_forecast(location: str = "22207") -> Dict:
    """
    Fetch weather forecast for Arlington, VA (22207)
    
    Returns dict with schema:
    {
        "title": "...",
        "summary": "...",
        "items": [...],
        "meta": {...}
    }
    """
    
    import urllib.request
    import urllib.error
    
    # Arlington, VA coordinates
    lat, lon = 38.875716, -77.107999
    
    try:
        # Step 1: Get gridpoint info
        points_url = f"https://api.weather.gov/points/{lat},{lon}"
        req = urllib.request.Request(
            points_url,
            headers={"User-Agent": "alfred-ai-assistant"}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            points_data = json.loads(response.read().decode())
        
        # Step 2: Get forecast from gridpoint (extract from properties.forecast)
        # Note: API sometimes returns null, so we construct the URL directly
        office = "LWX"  # Baltimore/Sterling office
        grid_x, grid_y = 98, 71
        forecast_url = f"https://api.weather.gov/gridpoints/{office}/{grid_x},{grid_y}/forecast"
        
        req = urllib.request.Request(
            forecast_url,
            headers={"User-Agent": "alfred-ai-assistant"}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            forecast_data = json.loads(response.read().decode())
        
        periods = forecast_data.get("properties", {}).get("periods", [])
        
        # Collect today + next 2 days (up to 6 periods: today afternoon/night, next day day/night, next day day/night)
        items = []
        for period in periods[:6]:
            item = {
                "name": period.get("name"),
                "temperature": f"{period.get('temperature')}°{period.get('temperatureUnit', 'F')}",
                "forecast": period.get("shortForecast"),
                "wind": period.get("windSpeed"),
                "wind_direction": period.get("windDirection"),
                "precipitation_chance": f"{period.get('probabilityOfPrecipitation', {}).get('value', 0)}%",
                "details": period.get("detailedForecast")
            }
            items.append(item)
        
        # Build summary
        today_forecast = periods[0] if periods else {}
        today_temp = today_forecast.get("temperature", "?")
        today_short = today_forecast.get("shortForecast", "unknown")
        summary = f"Today: {today_short}, high {today_temp}°F. Next 3 days show variable conditions with possible precipitation mid-week."
        
        return {
            "title": "Weather — Arlington, VA",
            "summary": summary,
            "items": items,
            "meta": {
                "location": "Arlington, VA (22207)",
                "source": "National Weather Service (weather.gov)",
                "updated_at": datetime.now().isoformat()
            }
        }
    
    except Exception as e:
        # Fallback: return empty section with error note
        return {
            "title": "Weather — Arlington, VA",
            "summary": f"Unable to fetch forecast: {str(e)}",
            "items": [],
            "meta": {
                "location": "Arlington, VA (22207)",
                "source": "National Weather Service (weather.gov)",
                "error": str(e)
            }
        }

if __name__ == "__main__":
    # Test
    section = get_forecast()
    print(json.dumps(section, indent=2))
