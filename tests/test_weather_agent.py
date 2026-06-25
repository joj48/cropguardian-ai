import unittest
from unittest.mock import patch, MagicMock
from agents.weather_agent.weather_agent import WeatherAgent

class TestWeatherAgent(unittest.TestCase):
    def setUp(self):
        self.agent = WeatherAgent()

    @patch('agents.weather_agent.weather_agent.requests.get')
    def test_get_weather_with_location_string(self, mock_get):
        # Mock geocoding response
        mock_geo_resp = MagicMock()
        mock_geo_resp.json.return_value = {
            "results": [
                {"latitude": 9.68, "longitude": 76.34, "name": "Cherthala", "admin1": "Kerala", "country": "India"}
            ]
        }
        
        # Mock weather response
        mock_weather_resp = MagicMock()
        mock_weather_resp.json.return_value = {
            "current": {
                "temperature_2m": 30.5,
                "relative_humidity_2m": 85,
                "precipitation": 12.0
            }
        }
        
        # Configure the side_effect to return different responses for the two API calls
        mock_get.side_effect = [mock_geo_resp, mock_weather_resp]
        
        result = self.agent.get_weather("Cherthala")
        
        self.assertEqual(result["location"], "Cherthala, Kerala, India")
        self.assertEqual(result["latitude"], 9.68)
        self.assertEqual(result["longitude"], 76.34)
        self.assertEqual(result["weather"]["temperature"], 30.5)
        self.assertEqual(result["weather"]["humidity"], 85)

    @patch('agents.weather_agent.weather_agent.requests.get')
    def test_get_weather_with_coordinates(self, mock_get):
        mock_weather_resp = MagicMock()
        mock_weather_resp.json.return_value = {
            "current": {
                "temperature_2m": 28.0,
                "relative_humidity_2m": 70
            }
        }
        mock_get.return_value = mock_weather_resp
        
        result = self.agent.get_weather(lat=9.68, lon=76.34)
        
        # Geocoding should be skipped
        self.assertEqual(mock_get.call_count, 1)
        self.assertEqual(result["weather"]["temperature"], 28.0)

if __name__ == "__main__":
    unittest.main()
