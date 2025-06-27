#!/usr/bin/env python3
"""
Debug script to test why login form can't be found during refresh.
"""

import os
import sys
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv
from my_meter_data.scraper import UtilityDataScraper
from bs4 import BeautifulSoup

# Load environment variables
load_dotenv()


def analyze_homepage(scraper):
    """Analyze the homepage structure to understand why login form isn't found."""
    print("\n🔍 Analyzing Homepage Structure...")
    
    try:
        # Get homepage
        response = scraper.session.get(scraper.base_url, timeout=scraper.timeout)
        print(f"Homepage response status: {response.status_code}")
        print(f"Homepage URL: {response.url}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code != 200:
            print(f"❌ Failed to get homepage: {response.status_code}")
            return
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for all forms
        forms = soup.find_all('form')
        print(f"\n📋 Found {len(forms)} forms on page:")
        
        for i, form in enumerate(forms):
            action = form.get('action', 'No action')
            method = form.get('method', 'GET')
            form_id = form.get('id', 'No ID')
            form_class = form.get('class', 'No class')
            
            print(f"\nForm {i+1}:")
            print(f"  Action: {action}")
            print(f"  Method: {method}")
            print(f"  ID: {form_id}")
            print(f"  Class: {form_class}")
            
            # Check inputs
            inputs = form.find_all('input')
            print(f"  Inputs ({len(inputs)}):")
            for inp in inputs:
                name = inp.get('name', 'No name')
                input_type = inp.get('type', 'text')
                placeholder = inp.get('placeholder', '')
                print(f"    - {name} ({input_type}) {placeholder}")
            
            # Check if this looks like a login form
            has_email = any(inp.get('name') in ['LoginEmail', 'email', 'username'] for inp in inputs)
            has_password = any(inp.get('type') == 'password' for inp in inputs)
            has_login_action = '/Home/Login' in action or '/login' in action.lower()
            
            if has_email or has_password or has_login_action:
                print(f"  🎯 This looks like a login form!")
                if '/Home/Login' in action:
                    print(f"  ✅ Has expected action: {action}")
                else:
                    print(f"  ⚠️  Action doesn't match expected '/Home/Login': {action}")
        
        # Look for login-related links
        print(f"\n🔗 Looking for login-related links:")
        links = soup.find_all('a', href=True)
        login_links = []
        for link in links:
            href = link.get('href', '')
            text = link.get_text(strip=True).lower()
            if any(keyword in text for keyword in ['login', 'sign in', 'log in']) or 'login' in href.lower():
                login_links.append((text, href))
                print(f"  - '{text}' -> {href}")
        
        if not login_links:
            print("  No login links found")
        
        # Look for any JavaScript that might be loading forms dynamically
        print(f"\n🔧 Checking for dynamic content...")
        scripts = soup.find_all('script')
        dynamic_indicators = ['document.createElement', 'innerHTML', 'ajax', 'fetch', 'XMLHttpRequest']
        
        for script in scripts:
            if script.string:
                script_content = script.string.lower()
                for indicator in dynamic_indicators:
                    if indicator.lower() in script_content:
                        print(f"  Found dynamic content indicator: {indicator}")
                        break
        
        # Check for redirect meta tags
        meta_redirects = soup.find_all('meta', attrs={'http-equiv': 'refresh'})
        if meta_redirects:
            print(f"\n🔄 Found meta redirects:")
            for meta in meta_redirects:
                print(f"  - {meta.get('content', '')}")
        
        # Save the homepage for inspection
        with open('debug_homepage.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print(f"\n💾 Homepage saved to debug_homepage.html for manual inspection")
        
        return forms
        
    except Exception as e:
        print(f"❌ Error analyzing homepage: {e}")
        return []


def test_session_behavior(scraper, username, password):
    """Test if session behavior changes after successful login."""
    print("\n🧪 Testing Session Behavior...")
    
    # First, try a fresh login
    print("1. Testing fresh login...")
    fresh_scraper = UtilityDataScraper()
    
    if fresh_scraper.login(username, password):
        print("✅ Fresh login successful")
        
        # Now test if we can access the homepage again with the same session
        print("2. Testing homepage access after login...")
        time.sleep(2)  # Wait a bit
        
        response = fresh_scraper.session.get(fresh_scraper.base_url, timeout=fresh_scraper.timeout)
        print(f"Post-login homepage status: {response.status_code}")
        print(f"Post-login URL: {response.url}")
        
        # Check if we're redirected or if the page structure changed
        soup = BeautifulSoup(response.text, 'html.parser')
        forms = soup.find_all('form')
        print(f"Forms after login: {len(forms)}")
        
        # Look for logout links or authenticated state indicators
        logout_links = soup.find_all('a', string=lambda text: text and 'logout' in text.lower())
        if logout_links:
            print("✅ Found logout links - we're logged in")
        else:
            print("⚠️  No logout links found")
        
        # Test if login form is still present
        login_forms = []
        for form in forms:
            action = form.get('action', '')
            if '/Home/Login' in action:
                login_forms.append(form)
        
        if login_forms:
            print("⚠️  Login form still present after login")
        else:
            print("✅ Login form removed after successful login")
        
        # Try getting data
        print("3. Testing data retrieval...")
        dashboard_data = fresh_scraper.get_dashboard_data()
        if dashboard_data:
            print("✅ Data retrieval successful")
        else:
            print("❌ Data retrieval failed")
    
    else:
        print("❌ Fresh login failed")


def main():
    """Debug login refresh issues."""
    print("🔧 Login Refresh Debug Tool")
    print("=" * 50)
    
    # Get credentials
    username = os.getenv('UTILITY_USERNAME')
    password = os.getenv('UTILITY_PASSWORD')
    
    if not username or not password:
        print("❌ Error: Please set UTILITY_USERNAME and UTILITY_PASSWORD in your .env file")
        return
    
    print(f"🔐 Testing with username: {username}")
    
    # Create a fresh scraper instance
    scraper = UtilityDataScraper()
    
    # Analyze homepage structure
    forms = analyze_homepage(scraper)
    
    # Test session behavior
    test_session_behavior(scraper, username, password)
    
    print(f"\n🎯 Debugging Summary:")
    print(f"1. Check the homepage analysis above")
    print(f"2. Look at debug_homepage.html to see actual page content")
    print(f"3. Check if forms are dynamically loaded")
    print(f"4. Verify if session state affects form availability")
    
    print(f"\n💡 Common Issues:")
    print(f"- Website may detect automation and change behavior")
    print(f"- Login form might be loaded dynamically via JavaScript")
    print(f"- Session cookies might expire or be invalidated")
    print(f"- Website might have rate limiting or CAPTCHA")
    print(f"- Form structure might change based on login state")


if __name__ == "__main__":
    main()