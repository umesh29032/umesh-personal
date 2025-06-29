#!/usr/bin/env python
"""
Documentation Update Script

This script helps update the DOCUMENTATION.md file with new changes.
Run this script after making significant changes to the project.
"""

import os
import datetime
from datetime import date

def get_user_input():
    """Get user input for documentation update."""
    print("\n=== Documentation Update Tool ===\n")
    
    # Get date (default to today)
    today = date.today().strftime("%B %d, %Y")
    date_input = input(f"Date of changes (default: {today}): ")
    if not date_input:
        date_input = today
    
    # Get category of changes
    print("\nCategories:")
    print("1. UI Enhancements")
    print("2. Backend Development")
    print("3. Bug Fixes")
    print("4. Feature Additions")
    print("5. Security Updates")
    print("6. Performance Improvements")
    print("7. Documentation")
    print("8. Other (specify)")
    
    category_choice = input("\nSelect category number (1-8): ")
    categories = {
        "1": "UI Enhancements",
        "2": "Backend Development",
        "3": "Bug Fixes",
        "4": "Feature Additions",
        "5": "Security Updates",
        "6": "Performance Improvements",
        "7": "Documentation",
        "8": "Other"
    }
    
    category = categories.get(category_choice, "Other")
    if category == "Other":
        category = input("Specify category: ")
    
    # Get bullet points
    print("\nEnter bullet points for changes (one per line, blank line to finish):")
    bullet_points = []
    while True:
        point = input("- ")
        if not point:
            break
        bullet_points.append(point)
    
    return {
        "date": date_input,
        "category": category,
        "bullet_points": bullet_points
    }

def update_documentation(changes):
    """Update the DOCUMENTATION.md file with the new changes."""
    doc_path = "DOCUMENTATION.md"
    
    if not os.path.exists(doc_path):
        print(f"Error: {doc_path} not found.")
        return False
    
    with open(doc_path, 'r') as file:
        content = file.readlines()
    
    # Find the Changelog section
    changelog_index = -1
    for i, line in enumerate(content):
        if line.strip() == "## Changelog":
            changelog_index = i
            break
    
    if changelog_index == -1:
        print("Error: Changelog section not found in documentation.")
        return False
    
    # Format the new changes
    new_content = [
        f"\n### {changes['date']}\n",
        f"- **{changes['category']}**:\n"
    ]
    
    for point in changes['bullet_points']:
        new_content.append(f"  - {point}\n")
    
    # Insert the new changes after the Changelog heading
    content = content[:changelog_index + 1] + new_content + content[changelog_index + 1:]
    
    # Write the updated content back to the file
    with open(doc_path, 'w') as file:
        file.writelines(content)
    
    print(f"\nSuccessfully updated {doc_path} with new changes.")
    return True

def main():
    """Main function to run the script."""
    changes = get_user_input()
    
    # Confirm before updating
    print("\n=== Summary of Changes ===")
    print(f"Date: {changes['date']}")
    print(f"Category: {changes['category']}")
    print("Bullet Points:")
    for point in changes['bullet_points']:
        print(f"- {point}")
    
    confirm = input("\nUpdate documentation with these changes? (y/n): ")
    if confirm.lower() == 'y':
        update_documentation(changes)
    else:
        print("Update cancelled.")

if __name__ == "__main__":
    main() 