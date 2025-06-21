#!/usr/bin/env python3
"""
Utility Data Scraper for City Utility Billing
Extracts water usage data from city utility billing systems
"""

import requests
import json
import os
from typing import Dict, Optional, Any
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class UtilityDataScraper:
    def __init__(self):
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
        Login to the utility billing system
        Returns True if login successful, False otherwise
        """
        try:
            # Get homepage which contains the login form
            time.sleep(self.request_delay)
            homepage = self.session.get(self.base_url, timeout=self.timeout)
            
            if homepage.status_code != 200:
                print(f"Failed to get homepage: {homepage.status_code}")
                return False
            
            # Parse the login form from homepage
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(homepage.text, 'html.parser')
            
            # Find the login form (action contains /Home/Login)
            login_form = None
            for form in soup.find_all('form'):
                action = form.get('action', '')
                if '/Home/Login' in action:
                    login_form = form
                    break
            
            if not login_form:
                print("Could not find login form")
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
            
            # Also check for any CSRF tokens in the page's cookies or meta tags
            csrf_token = None
            for cookie_name, cookie_value in self.session.cookies.items():
                if 'token' in cookie_name.lower() or 'csrf' in cookie_name.lower():
                    csrf_token = cookie_value
                    break
            
            if csrf_token and '__RequestVerificationToken' not in form_data:
                form_data['__RequestVerificationToken'] = csrf_token
            
            print(f"Form data being submitted: {form_data}")
            
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
            
            print(f"Login response status: {login_response.status_code}")
            print(f"Login response headers: {dict(login_response.headers)}")
            
            # Handle different login response scenarios
            if login_response.status_code == 302 or login_response.status_code == 301:
                # Successful login with redirect
                redirect_url = login_response.headers.get('Location', '')
                print(f"Login redirect to: {redirect_url}")
                
                if redirect_url:
                    if not redirect_url.startswith('http'):
                        redirect_url = self.base_url + redirect_url
                    
                    # Follow the redirect
                    time.sleep(self.request_delay)
                    redirect_response = self.session.get(redirect_url, timeout=self.timeout)
                    print(f"Redirect response status: {redirect_response.status_code}")
                    
                    if redirect_response.status_code == 200:
                        print("Login successful!")
                        return True
                
            elif login_response.status_code == 200:
                response_text = login_response.text.lower()
                print(f"Login response content: {login_response.text[:200]}")  # Debug output
                if "user account not found" in response_text or "invalid" in response_text:
                    print("Login failed: Invalid credentials")
                    print(f"Full response excerpt: {login_response.text[:500]}")
                    return False
                elif "dashboard" in response_text:
                    print("Login successful!")
                    return True
                else:
                    print("Login status unclear - checking dashboard access...")
                    # Try to access dashboard to verify login
                    time.sleep(self.request_delay)
                    dashboard_test = self.session.get(f"{self.base_url}/Dashboard", timeout=self.timeout)
                    if dashboard_test.status_code == 200 and "dashboard" in dashboard_test.text.lower():
                        print("Login successful!")
                        return True
            
            print(f"Login failed with status {login_response.status_code}")
            return False
            
        except Exception as e:
            print(f"Login error: {e}")
            return False
    
    def get_dashboard_data(self) -> Optional[Dict[str, Any]]:
        """
        Fetch the dashboard table data (water usage data)
        This corresponds to the '/Dashboard/Table' endpoint
        """
        try:
            time.sleep(self.request_delay)  # Rate limiting
            response = self.session.get(f"{self.base_url}/Dashboard/Table", timeout=self.timeout)
            
            if response.status_code == 200:
                # The response might be JSON or HTML
                try:
                    return response.json()
                except json.JSONDecodeError:
                    # If it's HTML, you might need to parse it
                    return {"html_content": response.text}
            else:
                print(f"Failed to get dashboard data: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error fetching dashboard data: {e}")
            return None
    
    def get_chart_data(self) -> Optional[Dict[str, Any]]:
        """
        Fetch the chart data which might contain raw usage numbers
        This corresponds to the '/Dashboard/Chart' endpoint
        """
        try:
            time.sleep(self.request_delay)  # Rate limiting
            response = self.session.get(f"{self.base_url}/Dashboard/Chart", timeout=self.timeout)
            
            if response.status_code == 200:
                try:
                    return response.json()
                except json.JSONDecodeError:
                    return {"html_content": response.text}
            else:
                print(f"Failed to get chart data: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error fetching chart data: {e}")
            return None
    
    def get_usage_data(self, date_range: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get usage data with optional date range
        """
        params = {}
        if date_range:
            params['dateRange'] = date_range
            
        try:
            time.sleep(self.request_delay)  # Rate limiting
            response = self.session.get(f"{self.base_url}/Usage/Data", params=params, timeout=self.timeout)
            
            if response.status_code == 200:
                try:
                    return response.json()
                except json.JSONDecodeError:
                    return {"html_content": response.text}
            else:
                print(f"Failed to get usage data: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error fetching usage data: {e}")
            return None
    
    def parse_usage_data_from_dashboard(self, dashboard_data: Dict[str, Any]) -> list:
        """
        Parse usage data from dashboard response
        """
        usage_records = []
        
        try:
            # The usage data is embedded in the dashboard HTML as JavaScript
            html_content = dashboard_data.get('AjaxResults', [{}])[0].get('Value', '')
            
            # Look for the tooltipJSON data which contains the actual usage information
            import re
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
                        
        except Exception as e:
            print(f"Error parsing usage data: {e}")
            
        return usage_records
    
    def save_usage_data_to_csv(self, usage_records: list, filename: str) -> bool:
        """
        Save usage records to CSV file
        """
        try:
            import csv
            
            if not usage_records:
                print("No usage data to save")
                return False
                
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['datetime', 'usage_gallons', 'temperature_f', 'precipitation_in', 'humidity_percent']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for record in usage_records:
                    writer.writerow(record)
                    
            print(f"Saved {len(usage_records)} usage records to {filename}")
            return True
            
        except Exception as e:
            print(f"Error saving CSV: {e}")
            return False

    def export_data(self, format_type: str = "csv") -> Optional[bytes]:
        """
        Export usage data in specified format
        """
        try:
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
                print(f"Failed to export data: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error exporting data: {e}")
            return None


def main():
    """
    Example usage of the scraper
    """
    scraper = UtilityDataScraper()
    
    # Get credentials from environment variables
    username = os.getenv('UTILITY_USERNAME')
    password = os.getenv('UTILITY_PASSWORD')
    
    if not username or not password:
        print("Error: Please set UTILITY_USERNAME and UTILITY_PASSWORD in your .env file")
        return
    
    # Create output directory if it doesn't exist
    os.makedirs(scraper.output_dir, exist_ok=True)
    
    print("Attempting to login...")
    if scraper.login(username, password):
        print("Login successful!")
        
        # Get dashboard data
        print("Fetching dashboard data...")
        dashboard_data = scraper.get_dashboard_data()
        if dashboard_data:
            print("Dashboard data retrieved successfully")
            
            # Parse usage data from dashboard
            print("Parsing usage data...")
            usage_records = scraper.parse_usage_data_from_dashboard(dashboard_data)
            
            if usage_records:
                # Save to CSV
                import datetime
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = os.path.join(scraper.output_dir, f"water_usage_{timestamp}.csv")
                
                if scraper.save_usage_data_to_csv(usage_records, filename):
                    print(f"Successfully saved {len(usage_records)} usage records to {filename}")
                else:
                    print("Failed to save usage data to CSV")
            else:
                print("No usage data found in dashboard response")
                # Debug: show what we got
                print("Dashboard data structure:")
                print(json.dumps(dashboard_data, indent=2))
        
        # Get chart data
        print("Fetching chart data...")
        chart_data = scraper.get_chart_data()
        if chart_data:
            print("Chart data retrieved:")
            print(json.dumps(chart_data, indent=2))
        
        # Try to export data
        print("Attempting to export data...")
        export_format = os.getenv('DEFAULT_EXPORT_FORMAT', 'csv')
        exported_data = scraper.export_data(export_format)
        if exported_data:
            output_file = os.path.join(scraper.output_dir, f"usage_data.{export_format}")
            with open(output_file, "wb") as f:
                f.write(exported_data)
            print(f"Data exported to {output_file}")
    
    else:
        print("Login failed. Please check your credentials.")


if __name__ == "__main__":
    main()