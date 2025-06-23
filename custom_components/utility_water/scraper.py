"""
Utility Data Scraper for Home Assistant integration.
Simplified version of the main scraper for use within Home Assistant.
"""

import requests
import json
import logging
import re
import time
from typing import Dict, Optional, Any, List
from bs4 import BeautifulSoup

_LOGGER = logging.getLogger(__name__)


class UtilityDataScraper:
    """Scraper for utility billing system to extract water usage data."""
    
    def __init__(self):
        """Initialize the scraper."""
        self.base_url = "https://utilitybilling.lawrenceks.gov"
        self.timeout = 30
        self.request_delay = 1.0
        self.session = requests.Session()
        
        # Set common headers that match browser behavior
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1'
        })
    
    def login(self, username: str, password: str) -> bool:
        """Login to the utility billing system."""
        try:
            _LOGGER.debug("Attempting to login to utility system")
            
            # Get homepage which contains the login form
            time.sleep(self.request_delay)
            homepage = self.session.get(self.base_url, timeout=self.timeout)
            
            if homepage.status_code != 200:
                _LOGGER.error(f"Failed to get homepage: {homepage.status_code}")
                return False
            
            # Parse the login form from homepage
            soup = BeautifulSoup(homepage.text, 'html.parser')
            
            # Find the login form
            login_form = None
            for form in soup.find_all('form'):
                action = form.get('action', '')
                if '/Home/Login' in action:
                    login_form = form
                    break
            
            if not login_form:
                _LOGGER.error("Could not find login form")
                return False
            
            # Extract form data
            form_data = {}
            for inp in login_form.find_all('input'):
                name = inp.get('name')
                value = inp.get('value', '')
                input_type = inp.get('type', 'text')
                
                if name:
                    if name == 'LoginEmail':
                        form_data[name] = username
                    elif name == 'LoginPassword':
                        form_data[name] = password
                    elif input_type == 'checkbox' and name == 'RememberMe':
                        form_data[name] = 'true'
                    else:
                        form_data[name] = value
            
            # Update headers for form submission
            self.session.headers.update({
                'Content-Type': 'application/x-www-form-urlencoded',
                'Referer': homepage.url
            })
            
            # Submit login form
            time.sleep(self.request_delay)
            login_response = self.session.post(
                f"{self.base_url}/Home/Login", 
                data=form_data, 
                timeout=self.timeout,
                allow_redirects=False
            )
            
            # Handle login response
            if login_response.status_code in [302, 301]:
                redirect_url = login_response.headers.get('Location', '')
                if redirect_url:
                    if not redirect_url.startswith('http'):
                        redirect_url = self.base_url + redirect_url
                    
                    time.sleep(self.request_delay)
                    redirect_response = self.session.get(redirect_url, timeout=self.timeout)
                    
                    if redirect_response.status_code == 200:
                        _LOGGER.debug("Login successful!")
                        return True
                        
            elif login_response.status_code == 200:
                response_text = login_response.text.lower()
                if "dashboard" in response_text or "user account not found" not in response_text:
                    _LOGGER.debug("Login successful!")
                    return True
            
            _LOGGER.error(f"Login failed with status {login_response.status_code}")
            return False
            
        except Exception as e:
            _LOGGER.error(f"Login error: {e}")
            return False
    
    def get_dashboard_data(self) -> Optional[Dict[str, Any]]:
        """Fetch the dashboard table data."""
        try:
            time.sleep(self.request_delay)
            response = self.session.get(f"{self.base_url}/Dashboard/Table", timeout=self.timeout)
            
            if response.status_code == 200:
                try:
                    return response.json()
                except json.JSONDecodeError:
                    return {"html_content": response.text}
            else:
                _LOGGER.error(f"Failed to get dashboard data: {response.status_code}")
                return None
                
        except Exception as e:
            _LOGGER.error(f"Error fetching dashboard data: {e}")
            return None
    
    def parse_usage_data_from_dashboard(self, dashboard_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse usage data from dashboard response."""
        usage_records = []
        
        try:
            # The usage data is embedded in the dashboard HTML as JavaScript
            html_content = dashboard_data.get('AjaxResults', [{}])[0].get('Value', '')
            
            # Look for the tooltipJSON data
            tooltip_match = re.search(r'var tooltipJSON = JSON\.parse\(\'(\[.*?\])\'\)', html_content)
            
            if tooltip_match:
                json_str = tooltip_match.group(1)
                # Unescape the JSON
                json_str = json_str.replace('\\\\u003c', '<').replace('\\\\u003e', '>').replace('\\\\', '\\')
                json_str = json_str.replace('\\"', '"')
                
                tooltip_data = json.loads(json_str)
                
                for item in tooltip_data:
                    value_html = item.get('value', '')
                    
                    # Extract data
                    time_match = re.search(r'<b>(.*?)</b>', value_html)
                    usage_match = re.search(r'<b>WR1</b>: ([\d.]+) gal', value_html)
                    temp_match = re.search(r'<b>Temp</b>: (\d+)°F', value_html)
                    precip_match = re.search(r'<b>Precipitation</b>: ([\d.]+) in\.', value_html)
                    humidity_match = re.search(r'<b>Humidity</b>: ([\d.]+)%', value_html)
                    
                    if time_match and usage_match:
                        record = {
                            'datetime': time_match.group(1),
                            'usage_gallons': float(usage_match.group(1)),
                            'temperature_f': int(temp_match.group(1)) if temp_match else None,
                            'precipitation_in': float(precip_match.group(1)) if precip_match else 0.0,
                            'humidity_percent': float(humidity_match.group(1)) if humidity_match else None
                        }
                        usage_records.append(record)
                        
        except Exception as e:
            _LOGGER.error(f"Error parsing usage data: {e}")
            
        return usage_records
    
    def get_latest_data(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Get the latest usage data for Home Assistant."""
        try:
            # Login
            if not self.login(username, password):
                _LOGGER.error("Failed to login")
                return None
            
            # Get dashboard data
            dashboard_data = self.get_dashboard_data()
            if not dashboard_data:
                _LOGGER.error("Failed to retrieve dashboard data")
                return None
            
            # Parse usage data
            usage_records = self.parse_usage_data_from_dashboard(dashboard_data)
            if not usage_records:
                _LOGGER.warning("No usage data found")
                return None
            
            # Sort records by datetime to ensure proper chronological ordering
            def parse_datetime(datetime_str):
                """Parse utility datetime string to datetime object for sorting."""
                try:
                    start_time_str = datetime_str.split(" - ")[0]
                    return time.strptime(start_time_str, "%a, %b %d, %Y %I:%M %p")
                except ValueError:
                    return time.struct_time((1970, 1, 1, 0, 0, 0, 0, 1, 0))  # Epoch for invalid dates
            
            sorted_records = sorted(usage_records, key=lambda x: parse_datetime(x['datetime']))
            
            # Get the most recent record
            latest_record = sorted_records[-1] if sorted_records else None
            
            # For Home Assistant Energy dashboard, we need a cumulative total
            # This should be the sum of ALL water usage since we started tracking
            total_gallons = sum(record['usage_gallons'] for record in sorted_records)
            
            # Get latest hourly reading for reference
            latest_usage = latest_record['usage_gallons'] if latest_record else 0
            
            # For debugging - log the data we're sending
            _LOGGER.debug(f"Sending to HA: total={total_gallons}, latest_hourly={latest_usage}, records={len(sorted_records)}")
            
            return {
                'latest_record': latest_record,
                'meter_reading': total_gallons,  # This becomes the sensor state - cumulative total
                'latest_hourly': latest_usage,
                'record_count': len(usage_records),
                'all_records': sorted_records,  # All records for statistics import
                'debug_records': [f"{r['datetime']}: {r['usage_gallons']} gal" for r in sorted_records[-5:]]  # Last 5 for debugging
            }
            
        except Exception as e:
            _LOGGER.error(f"Error getting latest data: {e}")
            return None