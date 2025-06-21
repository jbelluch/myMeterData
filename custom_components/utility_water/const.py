"""Constants for the Utility Water Meter integration."""
from datetime import timedelta

DOMAIN = "utility_water"

# Configuration
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_BASE_URL = "base_url"
CONF_UPDATE_INTERVAL = "update_interval"

# Defaults  
DEFAULT_BASE_URL = "https://utilitybilling.lawrenceks.gov"
DEFAULT_UPDATE_INTERVAL = timedelta(hours=1)
DEFAULT_TIMEOUT = 30
DEFAULT_REQUEST_DELAY = 1.0

# Sensor attributes
ATTR_LAST_UPDATED = "last_updated"
ATTR_TEMPERATURE = "temperature_f"
ATTR_PRECIPITATION = "precipitation_in"
ATTR_HUMIDITY = "humidity_percent"
ATTR_USAGE_GALLONS = "usage_gallons"

# Device info
MANUFACTURER = "Utility Water Meter"
MODEL = "Water Usage Scraper"

# Entity names
SENSOR_WATER_USAGE = "water_usage"
SENSOR_TEMPERATURE = "temperature"
SENSOR_PRECIPITATION = "precipitation"
SENSOR_HUMIDITY = "humidity"

# Units
UNIT_GALLONS = "gal"
UNIT_TEMPERATURE = "°F"
UNIT_PRECIPITATION = "in"
UNIT_HUMIDITY = "%"

# State classes for Home Assistant Energy
STATE_CLASS_TOTAL_INCREASING = "total_increasing"
STATE_CLASS_MEASUREMENT = "measurement"

# Device classes
DEVICE_CLASS_WATER = "water"
DEVICE_CLASS_TEMPERATURE = "temperature"
DEVICE_CLASS_PRECIPITATION = "precipitation_intensity"
DEVICE_CLASS_HUMIDITY = "humidity"