#!/usr/bin/env python3
"""
Debug script to check page issues
"""

import requests
import os
from pathlib import Path

def check_page():
    """Check if the page is working"""
    print("🔍 Debugging Page Issues...")
    print("=" * 50)
    
    # Check if Django server is running
    try:
        response = requests.get("http://localhost:8000/accounts/home/", timeout=5)
        print(f"✅ Django server is running")
        print(f"📊 Status Code: {response.status_code}")
        print(f"📦 Content Length: {len(response.content):,} bytes")
        
        # Check for Tailwind CDN
        if "cdn.tailwindcss.com" in response.text:
            print("✅ Tailwind CDN is loading")
        else:
            print("❌ Tailwind CDN not found")
            
        # Check for local CSS
        if "theme/css/dist/styles.css" in response.text:
            print("✅ Local CSS file is referenced")
        else:
            print("❌ Local CSS file not found in HTML")
            
        # Check for custom colors
        if "primary" in response.text and "secondary" in response.text:
            print("✅ Custom colors are configured")
        else:
            print("❌ Custom colors not found")
            
    except requests.exceptions.ConnectionError:
        print("❌ Django server is not running")
        print("💡 Start it with: python manage.py runserver")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # Check CSS file
    css_path = Path("theme/static/css/dist/styles.css")
    if css_path.exists():
        size = css_path.stat().st_size
        print(f"✅ Local CSS file exists ({size:,} bytes)")
    else:
        print("❌ Local CSS file missing")
        print("💡 Run: python build_tailwind.py build")
    
    # Check static files
    static_path = Path("staticfiles/theme/css/dist/styles.css")
    if static_path.exists():
        size = static_path.stat().st_size
        print(f"✅ Static CSS file exists ({size:,} bytes)")
    else:
        print("❌ Static CSS file missing")
        print("💡 Run: python manage.py collectstatic --noinput")
    
    print("\n" + "=" * 50)
    print("📋 Quick Fix Commands:")
    print("1. python build_tailwind.py build")
    print("2. python manage.py collectstatic --noinput")
    print("3. python manage.py runserver")
    print("4. Visit: http://localhost:8000/accounts/test/")
    
    return True

if __name__ == "__main__":
    check_page() 