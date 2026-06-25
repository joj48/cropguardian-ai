import requests
from typing import Dict, Any, Optional

class WeatherAgent:
    def __init__(self):
        self.geocode_url = "https://geocoding-api.open-meteo.com/v1/search"
        self.weather_url = "https://api.open-meteo.com/v1/forecast"

    def get_weather(self, location_input: Optional[str] = None, lat: Optional[float] = None, lon: Optional[float] = None) -> Dict[str, Any]:
        """
        Retrieves weather data based on location string OR coordinates.
        """
        try:
            resolved_location = "Unknown Location"
            
            # Step 1: Geocoding if lat/lon not provided
            if lat is None or lon is None:
                if not location_input:
                    raise ValueError("Must provide either location_input or lat/lon coordinates.")
                
                geo_resp = requests.get(self.geocode_url, params={"name": location_input, "count": 1, "format": "json"}, timeout=5)
                geo_resp.raise_for_status()
                geo_data = geo_resp.json()
                
                if "results" not in geo_data or len(geo_data["results"]) == 0:
                    raise ValueError(f"Could not resolve location: {location_input}")
                
                result = geo_data["results"][0]
                lat = result.get("latitude")
                lon = result.get("longitude")
                name = result.get("name", "")
                admin1 = result.get("admin1", "")
                country = result.get("country", "")
                
                parts = [p for p in [name, admin1, country] if p]
                resolved_location = ", ".join(parts)
            else:
                resolved_location = f"Lat: {lat}, Lon: {lon}"

            # Step 2: Fetch Weather Data
            weather_params = {
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,rain,showers,weather_code,cloud_cover,pressure_msl,surface_pressure,wind_speed_10m,wind_direction_10m,wind_gusts_10m",
                "timezone": "auto"
            }
            
            weather_resp = requests.get(self.weather_url, params=weather_params, timeout=5)
            weather_resp.raise_for_status()
            weather_data = weather_resp.json()
            
            current = weather_data.get("current", {})
            
            return {
                "location": resolved_location,
                "latitude": lat,
                "longitude": lon,
                "weather": {
                    "temperature": current.get("temperature_2m"),
                    "feels_like": current.get("apparent_temperature"),
                    "humidity": current.get("relative_humidity_2m"),
                    "precipitation": current.get("precipitation"),
                    "rain": current.get("rain"),
                    "cloud_cover": current.get("cloud_cover"),
                    "wind_speed": current.get("wind_speed_10m"),
                    "wind_direction": current.get("wind_direction_10m"),
                    "wind_gusts": current.get("wind_gusts_10m"),
                    "pressure": current.get("surface_pressure")
                }
            }

        except Exception as e:
            return {"error": str(e)}
