#!/usr/bin/env python3
"""
Debug Login Script for City Utility Billing
Analyzes the login process step-by-step to understand authentication requirements
"""

import requests
import json
import os
from typing import Dict, Optional, Any
import time
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import logging

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class LoginDebugger:
    def __init__(self):
        self.base_url = os.getenv('BASE_URL', 'https://utilitybilling.lawrenceks.gov')
        self.timeout = int(os.getenv('TIMEOUT', '30'))
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
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1'
        })
    
    def log_response(self, response: requests.Response, step: str):
        """Log detailed response information"""
        logger.info(f"=== {step} ===")
        logger.info(f"URL: {response.url}")
        logger.info(f"Status Code: {response.status_code}")
        logger.info(f"Headers: {dict(response.headers)}")
        
        # Log cookies
        if response.cookies:
            logger.info(f"Cookies: {dict(response.cookies)}")
        
        # Log response content (truncated)
        content = response.text[:1000] if len(response.text) > 1000 else response.text
        logger.info(f"Content (first 1000 chars): {content}")
        logger.info("=" * 50)
    
    def step1_get_homepage(self):
        """Step 1: Get the homepage to understand initial state"""
        logger.info("Step 1: Getting homepage...")
        try:
            response = self.session.get(self.base_url, timeout=self.timeout)
            self.log_response(response, "Homepage")
            
            # Analyze homepage for login links/forms
            self.analyze_homepage_for_login(response)
            
            return response
        except Exception as e:
            logger.error(f"Error getting homepage: {e}")
            return None
    
    def analyze_homepage_for_login(self, response: requests.Response):
        """Analyze homepage for login links and forms"""
        logger.info("Analyzing homepage for login mechanisms...")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for login links
        login_links = soup.find_all('a', href=True)
        logger.info("Looking for login-related links...")
        for link in login_links:
            href = link.get('href', '')
            text = link.get_text(strip=True).lower()
            
            if any(keyword in text for keyword in ['login', 'sign in', 'signin', 'log in']):
                logger.info(f"Found potential login link: '{text}' -> {href}")
        
        # Look for any forms on homepage
        forms = soup.find_all('form')
        logger.info(f"Found {len(forms)} forms on homepage")
        
        for i, form in enumerate(forms):
            action = form.get('action', 'No action')
            method = form.get('method', 'GET')
            logger.info(f"Form {i+1}: Action={action}, Method={method}")
            
            # Check if this might be a login form
            inputs = form.find_all('input')
            input_types = [inp.get('type', 'text') for inp in inputs]
            if 'password' in input_types:
                logger.info(f"  -> This appears to be a login form (has password field)")
                self.analyze_login_form(response)
        
        # Look for JavaScript that might handle authentication
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string and any(keyword in script.string.lower() for keyword in ['login', 'authenticate', 'signin']):
                logger.info("Found JavaScript that might handle authentication")
                # Truncate script content for logging
                script_content = script.string[:200] + "..." if len(script.string) > 200 else script.string
                logger.info(f"Script content: {script_content}")
    
    def step2_get_login_page(self):
        """Step 2: Get the login page to analyze form structure"""
        logger.info("Step 2: Getting login page...")
        try:
            # Try common login URLs
            login_urls = [
                f"{self.base_url}/Account/Login",
                f"{self.base_url}/Login",
                f"{self.base_url}/auth/login",
                f"{self.base_url}/signin"
            ]
            
            for login_url in login_urls:
                logger.info(f"Trying login URL: {login_url}")
                response = self.session.get(login_url, timeout=self.timeout)
                self.log_response(response, f"Login Page - {login_url}")
                
                if response.status_code == 200:
                    return response
                    
            return None
        except Exception as e:
            logger.error(f"Error getting login page: {e}")
            return None
    
    def analyze_login_form(self, response: requests.Response):
        """Analyze the login form structure"""
        logger.info("Analyzing login form structure...")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all forms
        forms = soup.find_all('form')
        logger.info(f"Found {len(forms)} forms on the page")
        
        for i, form in enumerate(forms):
            logger.info(f"--- Form {i+1} ---")
            
            # Get form attributes
            action = form.get('action', 'No action')
            method = form.get('method', 'GET')
            logger.info(f"Action: {action}")
            logger.info(f"Method: {method}")
            
            # Find all input fields
            inputs = form.find_all('input')
            logger.info(f"Input fields ({len(inputs)}):")
            
            form_data = {}
            for inp in inputs:
                name = inp.get('name', 'No name')
                input_type = inp.get('type', 'text')
                value = inp.get('value', '')
                placeholder = inp.get('placeholder', '')
                
                logger.info(f"  - Name: {name}, Type: {input_type}, Value: {value}, Placeholder: {placeholder}")
                
                # Store for potential form submission
                if name and name != 'No name':
                    form_data[name] = value
            
            # Look for CSRF tokens
            csrf_inputs = form.find_all('input', attrs={'name': lambda x: x and 'token' in x.lower()})
            if csrf_inputs:
                logger.info("CSRF tokens found:")
                for csrf in csrf_inputs:
                    logger.info(f"  - {csrf.get('name')}: {csrf.get('value', '')}")
            
            logger.info(f"Form data structure: {form_data}")
            logger.info("-" * 30)
        
        return forms
    
    def step3_attempt_login(self, username: str, password: str):
        """Step 3: Attempt login with debug information"""
        logger.info("Step 3: Attempting login...")
        
        # Get a fresh homepage to extract current form tokens
        homepage_response = self.session.get(self.base_url, timeout=self.timeout)
        if not homepage_response or homepage_response.status_code != 200:
            logger.error("Could not get homepage")
            return None
        
        # Analyze the form to find the login form
        soup = BeautifulSoup(homepage_response.text, 'html.parser')
        forms = soup.find_all('form')
        
        # Find the login form (Form 1 from our analysis)
        login_form = None
        for form in forms:
            action = form.get('action', '')
            if '/Home/Login' in action:
                login_form = form
                break
        
        if not login_form:
            logger.error("Could not find login form")
            return None
        
        # Extract form data
        form_data = {}
        inputs = login_form.find_all('input')
        for inp in inputs:
            name = inp.get('name')
            value = inp.get('value', '')
            input_type = inp.get('type', 'text')
            
            if name:
                if name == 'LoginEmail':
                    form_data[name] = username
                elif name == 'LoginPassword':
                    form_data[name] = password
                elif input_type == 'checkbox' and name == 'RememberMe':
                    form_data[name] = 'true'  # Keep the checkbox checked
                else:
                    # Keep existing value (like hidden fields)
                    form_data[name] = value
        
        # Get form action
        action = login_form.get('action')
        if not action.startswith('http'):
            action = self.base_url + action
        
        logger.info(f"Login form action: {action}")
        logger.info(f"Login form data: {form_data}")
        
        # Update headers for form submission
        self.session.headers.update({
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': homepage_response.url
        })
        
        # Attempt login
        try:
            login_post_response = self.session.post(action, data=form_data, timeout=self.timeout, allow_redirects=False)
            self.log_response(login_post_response, "Login POST Response")
            
            # Check if login was successful
            if login_post_response.status_code in [302, 301]:
                logger.info("Login appears successful (redirect response)")
                
                # Follow the redirect
                if 'Location' in login_post_response.headers:
                    redirect_url = login_post_response.headers['Location']
                    if not redirect_url.startswith('http'):
                        redirect_url = self.base_url + redirect_url
                    
                    logger.info(f"Following redirect to: {redirect_url}")
                    redirect_response = self.session.get(redirect_url, timeout=self.timeout)
                    self.log_response(redirect_response, "Post-Login Redirect")
                    
                    return redirect_response
                    
            elif login_post_response.status_code == 200:
                # Check if we're still on login page (failed) or dashboard (success)
                if 'dashboard' in login_post_response.url.lower() or 'Dashboard' in login_post_response.text:
                    logger.info("Login appears successful (dashboard content)")
                    return login_post_response
                else:
                    logger.warning("Login may have failed (still on login page)")
                    return login_post_response
            
            return login_post_response
            
        except Exception as e:
            logger.error(f"Error during login attempt: {e}")
            return None
    
    def step4_test_authenticated_request(self):
        """Step 4: Test if we can make authenticated requests"""
        logger.info("Step 4: Testing authenticated request...")
        
        try:
            # Try to access the dashboard
            dashboard_response = self.session.get(f"{self.base_url}/Dashboard", timeout=self.timeout)
            self.log_response(dashboard_response, "Dashboard Access Test")
            
            # Try to access the data endpoints
            table_response = self.session.get(f"{self.base_url}/Dashboard/Table", timeout=self.timeout)
            self.log_response(table_response, "Dashboard Table Test")
            
            return dashboard_response, table_response
            
        except Exception as e:
            logger.error(f"Error testing authenticated requests: {e}")
            return None, None


def main():
    """Run complete login debugging process"""
    debugger = LoginDebugger()
    
    # Get credentials from environment
    username = os.getenv('UTILITY_USERNAME')
    password = os.getenv('UTILITY_PASSWORD')
    
    if not username or not password:
        logger.error("Please set UTILITY_USERNAME and UTILITY_PASSWORD in your .env file")
        return
    
    logger.info(f"Starting login debug for: {username}")
    
    # Step 1: Get homepage
    homepage = debugger.step1_get_homepage()
    
    # Step 2: Get login page (we know this will fail, but keep for completeness)
    login_page = debugger.step2_get_login_page()
    
    # Step 3: Attempt login (using homepage form)
    login_result = debugger.step3_attempt_login(username, password)
    
    # Step 4: Test authenticated requests
    if login_result:
        dashboard, table = debugger.step4_test_authenticated_request()
    
    logger.info("Login debugging complete. Check logs above for details.")


if __name__ == "__main__":
    main()