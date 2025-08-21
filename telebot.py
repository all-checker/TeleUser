import requests
from bs4 import BeautifulSoup
import os
import time
import json
from datetime import datetime

HEADER_TEXT = "Telegram Username Checker Coded by https://t.me/malwaredot\n"

def check_username_availability(username):
    """Check if a Telegram username is available"""
    url = f"https://fragment.com/username/{username}"
    try:
        # Add headers to avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Check different status indicators
        status_div = soup.find("div", class_="table-cell-value tm-value tm-status-unavail")
        status_span_avail = soup.find("span", class_="tm-section-header-status tm-status-avail")
        status_span_taken = soup.find("span", class_="tm-section-header-status tm-status-taken")
        
        if status_span_avail:
            return "On auction"
        elif status_span_taken:
            return "taken"
        elif status_div:
            return "available"
        else:
            return "available"
    except requests.exceptions.RequestException as e:
        print(f"Error checking {username}: {e}")
        return f"Error: {e}"

def ensure_file_with_header(file_path):
    """Ensure file exists with header"""
    if not os.path.exists(file_path):
        with open(file_path, "w") as file:
            file.write(HEADER_TEXT)

def load_checked_usernames(checked_file):
    """Load already checked usernames to avoid duplicates"""
    checked_usernames = set()
    if os.path.exists(checked_file):
        with open(checked_file, "r") as file:
            lines = file.read().splitlines()
            # Skip header line if it exists
            if lines and lines[0].startswith("Telegram Username Checker"):
                checked_usernames = set(lines[1:])
            else:
                checked_usernames = set(lines)
    return checked_usernames

def process_usernames(input_file="usernames.txt", checked_file="checked_usernames.txt", 
                     unused_file="unused_usernames.txt", available_file="available_usernames.txt"):
    """Process usernames and check their availability"""
    
    # Ensure output files exist with headers
    ensure_file_with_header(checked_file)
    ensure_file_with_header(unused_file)
    ensure_file_with_header(available_file)
    
    # Load already checked usernames
    checked_usernames = load_checked_usernames(checked_file)
    
    try:
        with open(input_file, "r") as file:
            usernames = [line.strip() for line in file.readlines() if line.strip()]
        
        total_usernames = len(usernames)
        processed_count = 0
        available_count = 0
        
        print(f"Starting to process {total_usernames} usernames...")
        print(f"Already checked: {len(checked_usernames)} usernames")
        
        for username in usernames:
            if username in checked_usernames:
                print(f"Skipping {username}, already checked.")
                processed_count += 1
                continue
            
            print(f"Checking {username}... ({processed_count + 1}/{total_usernames})")
            status = check_username_availability(username)
            
            # Log the result
            if status == "available":
                print(f"✓ {username}: AVAILABLE")
                with open(available_file, "a") as available:
                    available.write(f"{username}\n")
                available_count += 1
            else:
                print(f"✗ {username}: {status}")
            
            # Add to checked list
            with open(checked_file, "a") as checked:
                checked.write(f"{username}\n")
            
            processed_count += 1
            
            # Add delay to avoid rate limiting
            time.sleep(1)
            
            # Progress update
            progress = (processed_count / total_usernames) * 100
            print(f"Progress: {processed_count}/{total_usernames} ({progress:.2f}%)")
        
        # Final summary
        print(f"\n=== SUMMARY ===")
        print(f"Total processed: {processed_count}")
        print(f"Available usernames found: {available_count}")
        print(f"Results saved to: {available_file}")
        
        # Create summary JSON
        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_processed": processed_count,
            "available_found": available_count,
            "checked_file": checked_file,
            "available_file": available_file
        }
        
        with open("summary.json", "w") as f:
            json.dump(summary, f, indent=2)
        
    except FileNotFoundError:
        print(f"Error: {input_file} not found.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    print("Telegram Username Checker")
    print("=" * 50)
    process_usernames()