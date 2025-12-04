import requests
import random
import time
import json
import os
from datetime import datetime
import colorama
from colorama import Fore, Style

colorama.init(autoreset=True)

class NGLSpammer:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/json"
        }
        self.messages = self._load_messages()
        self.rate_limit = 60  # seconds between messages
        self.proxy_sources = [
            "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
            "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
            "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt"
        ]
        self.proxy_pool = self._fetch_proxies()
        self.success_count = 0
        self.failed_count = 0
        self.error_count = 0
    
    def _load_messages(self):
        """Load messages from text file or generate defaults"""
        try:
            with open("messages.txt") as f:
                return [line.strip() for line in f]
        except FileNotFoundError:
            return [
                "Hey!",
                "Hello there!",
                "What's up?",
                "How are you?",
                "Nice to meet you!",
                "I'm looking for someone to talk to."
            ]
    
    def _fetch_proxies(self):
        """Fetch proxies from external sources"""
        proxies = []
        for source in self.proxy_sources:
            try:
                response = requests.get(source, timeout=10)
                lines = response.text.splitlines()
                
                for line in lines:
                    if ":" in line:
                        ip, port = line.split(":")
                        proxy = {"http": f"http://{ip}:{port}"}
                        if self.validate_proxy(proxy):
                            proxies.append(proxy)
                
                print(f"Fetched {len(proxies)} valid proxies from {source}")
                
            except Exception as e:
                print(f"Failed to fetch proxies from {source}: {e}")
        
        print(f"Total valid proxies: {len(proxies)}")
        return proxies
    
    def validate_proxy(self, proxy):
        """Test if proxy works properly"""
        try:
            response = requests.get(
                "https://httpbin.org/ip", 
                proxies=proxy,
                timeout=5
            )
            return response.status_code == 200
        except:
            return False
    
    def get_random_proxy(self):
        """Get random proxy from pool"""
        if not self.proxy_pool:
            print("No proxies available, regenerating...")
            self.proxy_pool = self._fetch_proxies()
            if not self.proxy_pool:
                raise Exception("No available proxies")
        return random.choice(self.proxy_pool)
    
    def send_message(self, link, message):
        """Send message to NGL user via full link"""
        # Extract username from link
        username = link.split("/")[-1]
        
        # Prepare payload
        payload = {
            "question": message,
            "anonymous": "true"  # Send anonymously
        }
        
        # Add proxy if available
        proxies = self.get_random_proxy()
        
        try:
            response = self.session.post(
                link, 
                json=payload,
                headers=self.headers,
                proxies=proxies
            )
            
            if response.status_code == 200:
                self.success_count += 1
                return True
            else:
                self.failed_count += 1
                return False
                
        except Exception as e:
            self.error_count += 1
            print(f"Error sending message: {e}")
            return False
    
    def run(self, link, count=100):
        """Send multiple messages to a user via link"""
        start_time = datetime.now()
        print(f"{Fore.CYAN}Starting spamming {count} messages to {link}...")
        
        for i in range(count):
            message = random.choice(self.messages)
            success = self.send_message(link, message)
            
            if success:
                status = f"{Fore.GREEN}✓"
            else:
                status = f"{Fore.RED}✗"
            
            print(f"Message {i+1}/{count}: {status} Sent")
            
            # Rate limiting
            if i < count - 1:  # Don't sleep after last message
                time.sleep(self.rate_limit)
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        # Print summary
        print("\n" + "="*50)
        print(f"{Fore.GREEN}Success: {self.success_count}")
        print(f"{Fore.RED}Failed: {self.failed_count}")
        print(f"{Fore.YELLOW}Errors: {self.error_count}")
        print(f"{Fore.BLUE}Total: {count}")
        print(f"{Fore.MAGENTA}Duration: {duration.total_seconds():.2f} seconds")
        print("="*50)

if __name__ == "__main__":
    # Get target link from command line or prompt
    import sys
    if len(sys.argv) > 1:
        link = sys.argv[1]
    else:
        link = input("Enter NGL link: ")
    
    # Optional: specify message count
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    
    spammer = NGLSpammer()
    spammer.run(link, count)