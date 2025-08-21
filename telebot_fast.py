#!/usr/bin/env python3
"""
High-Speed Telegram Username Checker with Concurrency
Coded by https://t.me/malwaredot
"""
import asyncio
import aiohttp
import os
import time
import json
from datetime import datetime
import glob
from concurrent.futures import ThreadPoolExecutor
import threading
from collections import defaultdict

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

HEADER_TEXT = "Telegram Username Checker Coded by https://t.me/malwaredot\n"

class TelegramChecker:
    def __init__(self, max_concurrent=50, delay_between_requests=0.1):
        self.max_concurrent = max_concurrent
        self.delay_between_requests = delay_between_requests
        self.session = None
        self.stats = defaultdict(int)
        self.stats_lock = threading.Lock()
        
    async def create_session(self):
        """Create aiohttp session with proper headers"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        timeout = aiohttp.ClientTimeout(total=10)
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=50)
        self.session = aiohttp.ClientSession(
            headers=headers, 
            timeout=timeout, 
            connector=connector
        )
    
    async def close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
    
    async def check_username_availability(self, username):
        """
        Check if a Telegram username is available
        
        Fragment.com behavior:
        - TAKEN usernames: Stay on original URL and contain 'tm-status-taken'
        - AVAILABLE usernames: Redirect to search query (?query=username)
        - UNAVAILABLE usernames: Stay on original URL and contain 'tm-status-unavail'
        """
        url = f"https://fragment.com/username/{username}"
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    # Check if we were redirected to a search query
                    # This happens when the username is available
                    final_url = str(response.url)
                    if "query=" in final_url:
                        return "available"
                    
                    # If not redirected, check the page content for status indicators
                    text = await response.text()
                    
                    # Check different status indicators
                    if 'tm-status-taken' in text:
                        return "taken"
                    elif 'tm-status-avail' in text:
                        return "available"
                    elif 'tm-status-unavail' in text:
                        return "unavailable"
                    else:
                        # If no clear status and no redirect, assume taken
                        # (this is safer than defaulting to available)
                        return "taken"
                else:
                    return f"HTTP {response.status}"
                    
        except asyncio.TimeoutError:
            return "timeout"
        except Exception as e:
            return f"error: {str(e)[:50]}"
    
    async def process_username(self, username, semaphore, available_file, checked_file):
        """Process a single username with semaphore control"""
        async with semaphore:
            status = await self.check_username_availability(username)
            
            # Update stats
            with self.stats_lock:
                self.stats['total_checked'] += 1
                if status == "available":
                    self.stats['available'] += 1
                elif status == "taken":
                    self.stats['taken'] += 1
                else:
                    self.stats['errors'] += 1
            
            # Log result with colors
            if status == "available":
                print(f"{Colors.GREEN}✓ {username}: AVAILABLE{Colors.END}")
                # Write to available file
                with open(available_file, "a") as f:
                    f.write(f"{username}\n")
            else:
                print(f"{Colors.RED}✗ {username}: {status.upper()}{Colors.END}")
            
            # Write to checked file
            with open(checked_file, "a") as f:
                f.write(f"{username}\n")
            
            # Small delay to avoid overwhelming the server
            await asyncio.sleep(self.delay_between_requests)
            
            return username, status
    
    def load_checked_usernames(self, checked_file):
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
    
    def ensure_file_with_header(self, file_path):
        """Ensure file exists with header"""
        if not os.path.exists(file_path):
            with open(file_path, "w") as file:
                file.write(HEADER_TEXT)
    
    def get_username_files(self):
        """Get all username files in current directory"""
        # Look for all .txt files that could contain usernames
        username_files = []
        
        # Priority order: usernames.txt first, then others
        if os.path.exists("usernames.txt"):
            username_files.append("usernames.txt")
        
        # Add other numbered files
        for pattern in ["5letter.txt", "6letter.txt", "7letter.txt"]:
            if os.path.exists(pattern):
                username_files.append(pattern)
        
        # Add any other .txt files (except output files)
        exclude_files = {"available_usernames.txt", "checked_usernames.txt", "unused_usernames.txt"}
        for txt_file in glob.glob("*.txt"):
            if txt_file not in username_files and txt_file not in exclude_files:
                username_files.append(txt_file)
        
        return username_files
    
    def load_usernames_from_files(self, username_files):
        """Load usernames from multiple files"""
        all_usernames = []
        
        for file_path in username_files:
            try:
                print(f"{Colors.CYAN}Loading usernames from: {file_path}{Colors.END}")
                with open(file_path, "r") as file:
                    usernames = [line.strip() for line in file.readlines() if line.strip()]
                    all_usernames.extend(usernames)
                    print(f"{Colors.CYAN}Loaded {len(usernames):,} usernames from {file_path}{Colors.END}")
            except Exception as e:
                print(f"{Colors.RED}Error loading {file_path}: {e}{Colors.END}")
        
        return all_usernames
    
    async def process_usernames_batch(self, usernames, checked_usernames, 
                                    checked_file="checked_usernames.txt", 
                                    available_file="available_usernames.txt"):
        """Process usernames in concurrent batches"""
        
        # Filter out already checked usernames
        unchecked_usernames = [u for u in usernames if u not in checked_usernames]
        
        if not unchecked_usernames:
            print(f"{Colors.YELLOW}All usernames have already been checked!{Colors.END}")
            return
        
        print(f"{Colors.BOLD}Processing {len(unchecked_usernames):,} unchecked usernames...{Colors.END}")
        print(f"{Colors.BOLD}Concurrency level: {self.max_concurrent}{Colors.END}")
        print(f"{Colors.BOLD}Target speed: 1000+ usernames per minute{Colors.END}")
        
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        # Create session
        await self.create_session()
        
        try:
            # Create tasks for all usernames
            tasks = []
            for username in unchecked_usernames:
                task = self.process_username(username, semaphore, available_file, checked_file)
                tasks.append(task)
            
            # Process in batches to avoid memory issues
            batch_size = 1000
            start_time = time.time()
            
            for i in range(0, len(tasks), batch_size):
                batch = tasks[i:i + batch_size]
                batch_start = time.time()
                
                print(f"\n{Colors.MAGENTA}Processing batch {i//batch_size + 1}/{(len(tasks)-1)//batch_size + 1} ({len(batch)} usernames)...{Colors.END}")
                
                # Execute batch
                await asyncio.gather(*batch, return_exceptions=True)
                
                batch_time = time.time() - batch_start
                batch_rate = len(batch) / batch_time * 60  # per minute
                
                print(f"{Colors.BLUE}Batch completed in {batch_time:.2f}s (Rate: {batch_rate:.0f}/min){Colors.END}")
                
                # Progress update
                total_processed = min(i + batch_size, len(tasks))
                overall_time = time.time() - start_time
                overall_rate = total_processed / overall_time * 60
                
                print(f"{Colors.BOLD}Overall Progress: {total_processed:,}/{len(tasks):,} ({total_processed/len(tasks)*100:.1f}%){Colors.END}")
                print(f"{Colors.BOLD}Overall Rate: {overall_rate:.0f} usernames/minute{Colors.END}")
                print(f"{Colors.GREEN}Available: {self.stats['available']}{Colors.END} | {Colors.RED}Taken: {self.stats['taken']}{Colors.END} | {Colors.YELLOW}Errors: {self.stats['errors']}{Colors.END}")
        
        finally:
            await self.close_session()
    
    async def run(self):
        """Main execution function"""
        print(f"{Colors.BOLD}{Colors.CYAN}=== HIGH-SPEED TELEGRAM USERNAME CHECKER ==={Colors.END}")
        print(f"{Colors.CYAN}Coded by https://t.me/malwaredot{Colors.END}\n")
        
        # Setup output files
        checked_file = "checked_usernames.txt"
        available_file = "available_usernames.txt"
        
        self.ensure_file_with_header(checked_file)
        self.ensure_file_with_header(available_file)
        
        # Load already checked usernames
        checked_usernames = self.load_checked_usernames(checked_file)
        print(f"{Colors.YELLOW}Already checked: {len(checked_usernames):,} usernames{Colors.END}")
        
        # Get all username files
        username_files = self.get_username_files()
        
        if not username_files:
            print(f"{Colors.RED}No username files found! Please ensure you have .txt files with usernames.{Colors.END}")
            return
        
        print(f"{Colors.CYAN}Found username files: {', '.join(username_files)}{Colors.END}")
        
        # Load usernames from all files
        all_usernames = self.load_usernames_from_files(username_files)
        
        if not all_usernames:
            print(f"{Colors.RED}No usernames loaded from files!{Colors.END}")
            return
        
        print(f"{Colors.BOLD}Total usernames loaded: {len(all_usernames):,}{Colors.END}")
        
        # Remove duplicates while preserving order
        unique_usernames = list(dict.fromkeys(all_usernames))
        print(f"{Colors.BOLD}Unique usernames: {len(unique_usernames):,}{Colors.END}")
        
        # Start processing
        start_time = time.time()
        await self.process_usernames_batch(unique_usernames, checked_usernames, checked_file, available_file)
        
        # Final summary
        total_time = time.time() - start_time
        total_rate = self.stats['total_checked'] / total_time * 60 if total_time > 0 else 0
        
        print(f"\n{Colors.BOLD}{Colors.GREEN}=== FINAL SUMMARY ==={Colors.END}")
        print(f"{Colors.BOLD}Total processed: {self.stats['total_checked']:,}{Colors.END}")
        print(f"{Colors.GREEN}Available usernames: {self.stats['available']:,}{Colors.END}")
        print(f"{Colors.RED}Taken usernames: {self.stats['taken']:,}{Colors.END}")
        print(f"{Colors.YELLOW}Errors: {self.stats['errors']:,}{Colors.END}")
        print(f"{Colors.BOLD}Total time: {total_time:.2f} seconds{Colors.END}")
        print(f"{Colors.BOLD}Average rate: {total_rate:.0f} usernames/minute{Colors.END}")
        
        # Save summary
        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_processed": self.stats['total_checked'],
            "available_found": self.stats['available'],
            "taken_found": self.stats['taken'],
            "errors": self.stats['errors'],
            "total_time_seconds": total_time,
            "rate_per_minute": total_rate,
            "files_processed": username_files
        }
        
        with open("summary.json", "w") as f:
            json.dump(summary, f, indent=2)
        
        print(f"{Colors.CYAN}Results saved to: {available_file}{Colors.END}")
        print(f"{Colors.CYAN}Summary saved to: summary.json{Colors.END}")

async def main():
    """Main function"""
    # Create checker with optimized settings for speed
    checker = TelegramChecker(
        max_concurrent=100,  # High concurrency for speed
        delay_between_requests=0.05  # Minimal delay
    )
    
    await checker.run()

if __name__ == "__main__":
    asyncio.run(main())