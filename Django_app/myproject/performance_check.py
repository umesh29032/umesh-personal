#!/usr/bin/env python3
"""
Simple performance checker for the Django application.
This script helps monitor page load times and performance metrics.
"""

import time
import requests
import sys
from urllib.parse import urljoin

def check_page_performance(base_url, page_path="/"):
    """Check the performance of a specific page."""
    url = urljoin(base_url, page_path)
    
    print(f"🔍 Checking performance for: {url}")
    print("-" * 50)
    
    # Measure response time
    start_time = time.time()
    try:
        response = requests.get(url, timeout=10)
        end_time = time.time()
        
        response_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        print(f"✅ Status Code: {response.status_code}")
        print(f"⏱️  Response Time: {response_time:.2f}ms")
        print(f"📦 Content Length: {len(response.content):,} bytes")
        
        # Check for external resources
        content = response.text
        external_resources = []
        
        if "cdn.tailwindcss.com" in content:
            external_resources.append("❌ Still using Tailwind CDN")
        else:
            external_resources.append("✅ Using local Tailwind CSS")
            
        if "googleapis.com" in content:
            external_resources.append("ℹ️  Using Google Fonts (external)")
            
        if "cdnjs.cloudflare.com" in content:
            external_resources.append("ℹ️  Using Font Awesome CDN (external)")
        
        print("\n📊 External Resources:")
        for resource in external_resources:
            print(f"  {resource}")
            
        # Performance recommendations
        print("\n💡 Performance Recommendations:")
        if response_time > 1000:
            print("  ⚠️  Response time is slow (>1s). Consider:")
            print("     - Database query optimization")
            print("     - Caching implementation")
            print("     - Static file optimization")
        elif response_time > 500:
            print("  ⚠️  Response time is moderate (>500ms). Consider:")
            print("     - Database indexing")
            print("     - Template optimization")
        else:
            print("  ✅ Response time is good (<500ms)")
            
        if len(response.content) > 100000:
            print("  ⚠️  Page size is large (>100KB). Consider:")
            print("     - Image optimization")
            print("     - CSS/JS minification")
            print("     - Lazy loading")
        else:
            print("  ✅ Page size is reasonable")
            
        return response_time, len(response.content)
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
        return None, None

def main():
    """Main function to run performance checks."""
    print("🚀 Django Performance Checker")
    print("=" * 50)
    
    # Default to localhost:8000
    base_url = "http://localhost:8000"
    
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    
    print(f"Target server: {base_url}")
    print()
    
    # Check home page
    home_time, home_size = check_page_performance(base_url, "/")
    
    print("\n" + "=" * 50)
    print("📈 Performance Summary")
    print("=" * 50)
    
    if home_time:
        print(f"🏠 Home Page:")
        print(f"   Response Time: {home_time:.2f}ms")
        print(f"   Page Size: {home_size:,} bytes")
        
        if home_time < 300:
            print("   Performance: 🟢 Excellent")
        elif home_time < 500:
            print("   Performance: 🟡 Good")
        elif home_time < 1000:
            print("   Performance: 🟠 Moderate")
        else:
            print("   Performance: 🔴 Needs Improvement")
    else:
        print("❌ Could not measure performance")
    
    print("\n💡 Tips for better performance:")
    print("1. Use local Tailwind CSS (✅ Done)")
    print("2. Optimize images and use WebP format")
    print("3. Implement caching (Redis/Memcached)")
    print("4. Use database indexing")
    print("5. Minimize external HTTP requests")
    print("6. Enable Gzip compression")
    print("7. Use CDN for static files in production")

if __name__ == "__main__":
    main() 