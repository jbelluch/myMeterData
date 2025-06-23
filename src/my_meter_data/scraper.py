#!/usr/bin/env python3
"""
Utility Data Scraper for City Utility Billing
Extracts water usage data from utility billing systems
"""

import requests
import json
import os
import logging
from typing import Dict, Optional, Any, List
import time
import csv
import re
import datetime
from dotenv import load_dotenv
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class UtilityDataScraper:
    """
    Scraper for city utility billing system to extract water usage data.
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize the scraper with configuration.
        
        Args:
            config_file: Path to .env file. If None, loads from default location.
        """
        if config_file:
            load_dotenv(config_file)
        else:
            load_dotenv()
            
        self.base_url = os.getenv('BASE_URL', 'https://utilitybilling.lawrenceks.gov')
        self.timeout = int(os.getenv('TIMEOUT', '30'))
        self.request_delay = float(os.getenv('REQUEST_DELAY', '1.0'))
        self.output_dir = os.getenv('OUTPUT_DIRECTORY', './data')
        self.session = requests.Session()
        
        # Set common headers that match browser behavior exactly
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
        """
        Login to the utility billing system.
        
        Args:
            username: Email address for login
            password: Password for login
            
        Returns:
            True if login successful, False otherwise
        """
        try:
            logger.info("Attempting to login to utility system")
            
            # Get homepage which contains the login form
            time.sleep(self.request_delay)
            homepage = self.session.get(self.base_url, timeout=self.timeout)
            
            if homepage.status_code != 200:
                logger.error(f"Failed to get homepage: {homepage.status_code}")
                return False
            
            # Parse the login form from homepage
            soup = BeautifulSoup(homepage.text, 'html.parser')
            
            # Find the login form (action contains /Home/Login)
            login_form = None
            for form in soup.find_all('form'):
                action = form.get('action', '')
                if '/Home/Login' in action:
                    login_form = form
                    break
            
            if not login_form:
                logger.error("Could not find login form")
                return False
            
            # Extract form data including any CSRF tokens
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
                        # Keep existing values (hidden fields, CSRF tokens, etc.)
                        form_data[name] = value
            
            # Also check for any CSRF tokens in the page's cookies
            csrf_token = None
            for cookie_name, cookie_value in self.session.cookies.items():
                if 'token' in cookie_name.lower() or 'csrf' in cookie_name.lower():
                    csrf_token = cookie_value
                    break
            
            if csrf_token and '__RequestVerificationToken' not in form_data:
                form_data['__RequestVerificationToken'] = csrf_token
            
            logger.debug(f"Form data being submitted: {form_data}")
            
            # Update headers for form submission
            self.session.headers.update({
                'Content-Type': 'application/x-www-form-urlencoded',
                'Referer': homepage.url
            })
            
            # Submit login form with proper redirect handling
            time.sleep(self.request_delay)
            login_response = self.session.post(
                f"{self.base_url}/Home/Login", 
                data=form_data, 
                timeout=self.timeout,
                allow_redirects=False  # Handle redirects manually
            )
            
            logger.debug(f"Login response status: {login_response.status_code}")
            
            # Handle different login response scenarios
            if login_response.status_code in [302, 301]:
                # Successful login with redirect
                redirect_url = login_response.headers.get('Location', '')
                logger.debug(f"Login redirect to: {redirect_url}")
                
                if redirect_url:
                    if not redirect_url.startswith('http'):
                        redirect_url = self.base_url + redirect_url
                    
                    # Follow the redirect
                    time.sleep(self.request_delay)
                    redirect_response = self.session.get(redirect_url, timeout=self.timeout)
                    
                    if redirect_response.status_code == 200:
                        logger.info("Login successful!")
                        return True
                
            elif login_response.status_code == 200:
                response_text = login_response.text.lower()
                if "user account not found" in response_text or "invalid" in response_text:
                    logger.error("Login failed: Invalid credentials")
                    return False
                elif "dashboard" in response_text:
                    logger.info("Login successful!")
                    return True
                else:
                    # Try to access dashboard to verify login
                    time.sleep(self.request_delay)
                    dashboard_test = self.session.get(f"{self.base_url}/Dashboard", timeout=self.timeout)
                    if dashboard_test.status_code == 200 and "dashboard" in dashboard_test.text.lower():
                        logger.info("Login successful!")
                        return True
            
            logger.error(f"Login failed with status {login_response.status_code}")
            return False
            
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False
    
    def get_dashboard_data(self) -> Optional[Dict[str, Any]]:
        """
        Fetch the dashboard table data (water usage data).
        
        Returns:
            Dictionary containing dashboard data or None if failed
        """
        try:
            logger.info("Fetching dashboard data")
            time.sleep(self.request_delay)
            response = self.session.get(f"{self.base_url}/Dashboard/Table", timeout=self.timeout)
            
            if response.status_code == 200:
                try:
                    return response.json()
                except json.JSONDecodeError:
                    return {"html_content": response.text}
            else:
                logger.error(f"Failed to get dashboard data: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching dashboard data: {e}")
            return None
    
    def get_chart_data(self) -> Optional[Dict[str, Any]]:
        """
        Fetch the chart data which might contain raw usage numbers.
        
        Returns:
            Dictionary containing chart data or None if failed
        """
        try:
            logger.info("Fetching chart data")
            time.sleep(self.request_delay)
            response = self.session.get(f"{self.base_url}/Dashboard/Chart", timeout=self.timeout)
            
            if response.status_code == 200:
                try:
                    return response.json()
                except json.JSONDecodeError:
                    return {"html_content": response.text}
            else:
                logger.error(f"Failed to get chart data: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching chart data: {e}")
            return None
    
    def parse_usage_data_from_dashboard(self, dashboard_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse usage data from dashboard response.
        
        Args:
            dashboard_data: Raw dashboard data from API
            
        Returns:
            List of usage records with datetime, usage, and weather data
        """
        usage_records = []
        
        try:
            logger.info("Parsing usage data from dashboard response")
            
            # The usage data is embedded in the dashboard HTML as JavaScript
            html_content = dashboard_data.get('AjaxResults', [{}])[0].get('Value', '')
            
            # Look for the tooltipJSON data which contains the actual usage information
            tooltip_match = re.search(r'var tooltipJSON = JSON\.parse\(\'(\[.*?\])\'\)', html_content)
            
            if tooltip_match:
                # The JSON string is escaped, so we need to unescape it
                json_str = tooltip_match.group(1)
                # Unescape the JSON
                json_str = json_str.replace('\\\\u003c', '<').replace('\\\\u003e', '>').replace('\\\\', '\\')
                json_str = json_str.replace('\\"', '"')
                
                tooltip_data = json.loads(json_str)
                
                for item in tooltip_data:
                    # Parse the tooltip value which contains usage info
                    value_html = item.get('value', '')
                    
                    # Extract date/time
                    time_match = re.search(r'<b>(.*?)</b>', value_html)
                    
                    # Extract water usage (look for "WR1: X.X gal")
                    usage_match = re.search(r'<b>WR1</b>: ([\d.]+) gal', value_html)
                    
                    # Extract temperature
                    temp_match = re.search(r'<b>Temp</b>: (\d+)°F', value_html)
                    
                    # Extract precipitation  
                    precip_match = re.search(r'<b>Precipitation</b>: ([\d.]+) in\.', value_html)
                    
                    # Extract humidity
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
                        
                logger.info(f"Parsed {len(usage_records)} usage records")
                        
        except Exception as e:
            logger.error(f"Error parsing usage data: {e}")
            
        return usage_records
    
    def save_usage_data_to_csv(self, usage_records: List[Dict[str, Any]], filename: str) -> bool:
        """
        Save usage records to CSV file.
        
        Args:
            usage_records: List of usage data records
            filename: Output filename
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not usage_records:
                logger.warning("No usage data to save")
                return False
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(filename), exist_ok=True)
                
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['datetime', 'usage_gallons', 'temperature_f', 'precipitation_in', 'humidity_percent']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for record in usage_records:
                    writer.writerow(record)
                    
            logger.info(f"Saved {len(usage_records)} usage records to {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving CSV: {e}")
            return False

    def export_data(self, format_type: str = "csv") -> Optional[bytes]:
        """
        Export usage data in specified format.
        
        Args:
            format_type: Export format (currently only 'csv' supported)
            
        Returns:
            Raw export data or None if failed
        """
        try:
            logger.info(f"Exporting data in {format_type} format")
            
            # First initialize download settings
            time.sleep(self.request_delay)
            self.session.get(f"{self.base_url}/Usage/InitializeDownloadSettings", timeout=self.timeout)
            
            # Then request the export
            time.sleep(self.request_delay)
            response = self.session.get(f"{self.base_url}/Usage/Export", 
                                      params={"format": format_type}, timeout=self.timeout)
            
            if response.status_code == 200:
                return response.content
            else:
                logger.error(f"Failed to export data: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            return None

    def scrape_usage_data(self, username: str, password: str) -> Optional[str]:
        """
        Complete workflow to scrape usage data.
        
        Args:
            username: Login email
            password: Login password
            
        Returns:
            Path to saved CSV file or None if failed
        """
        logger.info("Starting usage data scraping workflow")
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Login
        if not self.login(username, password):
            logger.error("Failed to login")
            return None
        
        # Get dashboard data
        dashboard_data = self.get_dashboard_data()
        if not dashboard_data:
            logger.error("Failed to retrieve dashboard data")
            return None
        
        # Parse usage data
        usage_records = self.parse_usage_data_from_dashboard(dashboard_data)
        if not usage_records:
            logger.error("No usage data found")
            return None
        
        # Save to CSV
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(self.output_dir, f"water_usage_{timestamp}.csv")
        
        if self.save_usage_data_to_csv(usage_records, filename):
            logger.info(f"Successfully completed scraping. Data saved to {filename}")
            return filename
        else:
            logger.error("Failed to save usage data")
            return None

    def get_latest_data(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Get the latest usage data for debugging/HA integration."""
        try:
            # Login
            if not self.login(username, password):
                logger.error("Failed to login")
                return None
            
            # Get dashboard data
            dashboard_data = self.get_dashboard_data()
            if not dashboard_data:
                logger.error("Failed to retrieve dashboard data")
                return None
            
            # Parse usage data
            usage_records = self.parse_usage_data_from_dashboard(dashboard_data)
            if not usage_records:
                logger.warning("No usage data found")
                return None
            
            # Sort records by datetime to ensure proper chronological ordering
            def parse_datetime(datetime_str):
                """Parse utility datetime string to datetime object for sorting."""
                try:
                    start_time_str = datetime_str.split(" - ")[0]
                    return datetime.datetime.strptime(start_time_str, "%a, %b %d, %Y %I:%M %p")
                except ValueError:
                    return datetime.datetime.min  # Put invalid dates at the beginning
            
            sorted_records = sorted(usage_records, key=lambda x: parse_datetime(x['datetime']))
            
            # Get the most recent record
            latest_record = sorted_records[-1] if sorted_records else None
            
            # For Home Assistant Energy dashboard, we need a cumulative total
            # This should be the sum of ALL water usage since we started tracking
            total_gallons = sum(record['usage_gallons'] for record in sorted_records)
            
            # Get latest hourly reading for reference
            latest_usage = latest_record['usage_gallons'] if latest_record else 0
            
            # For debugging - log the data we're sending
            logger.debug(f"Sending to HA: total={total_gallons}, latest_hourly={latest_usage}, records={len(sorted_records)}")
            
            return {
                'latest_record': latest_record,
                'meter_reading': total_gallons,  # This becomes the sensor state - cumulative total
                'latest_hourly': latest_usage,
                'record_count': len(usage_records),
                'all_records': sorted_records,  # All records for statistics import
                'debug_records': [f"{r['datetime']}: {r['usage_gallons']} gal" for r in sorted_records[-5:]]  # Last 5 for debugging
            }
            
        except Exception as e:
            logger.error(f"Error getting latest data: {e}")
            return None