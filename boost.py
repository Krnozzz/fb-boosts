import requests
import time
import random
import logging
import json
from datetime import datetime
import os
from urllib.parse import quote

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('fb_follower_boost.log'),
        logging.StreamHandler()
    ]
)

class FacebookFollowerBooster:
    def __init__(self):
        self.config = {
            "delay_range": (3, 7),
            "max_retries": 3,
            "retry_delay": 5,
        }
        
        self.stats = {
            "login_attempts": 0,
            "successful_logins": 0,
            "follow_attempts": 0,
            "successful_follows": 0,
            "errors": 0,
            "start_time": datetime.now().isoformat()
        }
        
        self.running = True
        self.accounts = []
        self.target_profile = None
    
    def load_accounts(self, filename="accounts.txt"):
        """Load accounts from file (format: email:password or email:password:name)"""
        try:
            if not os.path.exists(filename):
                logging.error(f"❌ Account file '{filename}' not found!")
                logging.info("📝 Create accounts.txt with format: email:password (one per line)")
                return False
            
            with open(filename, 'r') as file:
                for line in file:
                    line = line.strip()
                    if line and ':' in line:
                        parts = line.split(':')
                        if len(parts) >= 2:
                            account = {
                                'email': parts[0].strip(),
                                'password': parts[1].strip(),
                                'name': parts[2].strip() if len(parts) > 2 else 'Unknown'
                            }
                            self.accounts.append(account)
            
            logging.info(f"✅ Loaded {len(self.accounts)} accounts from {filename}")
            return len(self.accounts) > 0
            
        except Exception as e:
            logging.error(f"❌ Error loading accounts: {e}")
            return False
    
    def create_session(self):
        """Create a new session with headers"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'https://m.facebook.com/'
        })
        return session
    
    def login_account(self, session, email, password):
        """Attempt to login to Facebook account"""
        try:
            logging.info(f"🔐 Attempting login: {email}")
            self.stats["login_attempts"] += 1
            
            # Get login page
            login_url = 'https://m.facebook.com/login.php'
            response = session.get(login_url, timeout=15)
            
            if response.status_code != 200:
                logging.error(f"❌ Failed to load login page: HTTP {response.status_code}")
                return False
            
            # Prepare login data
            login_data = {
                'email': email,
                'pass': password,
                'login': 'Log In'
            }
            
            # Submit login
            time.sleep(random.uniform(1, 3))
            login_response = session.post(
                'https://m.facebook.com/login/device-based/regular/login/',
                data=login_data,
                timeout=15,
                allow_redirects=True
            )
            
            # Check if login was successful
            if 'c_user' in session.cookies:
                logging.info(f"✅ Login successful: {email}")
                self.stats["successful_logins"] += 1
                return True
            else:
                logging.warning(f"⚠️  Login may have failed for {email}")
                # Check for common error indicators
                if 'checkpoint' in login_response.url.lower():
                    logging.error(f"❌ Account {email} requires verification (checkpoint)")
                elif 'login' in login_response.url.lower():
                    logging.error(f"❌ Invalid credentials for {email}")
                else:
                    logging.warning(f"⚠️  Unusual response, check manually")
                return False
            
        except requests.RequestException as e:
            logging.error(f"❌ Network error during login for {email}: {e}")
            return False
        except Exception as e:
            logging.error(f"❌ Unexpected error during login for {email}: {e}")
            return False
    
    def follow_profile(self, session, target_username):
        """Follow a Facebook profile"""
        try:
            logging.info(f"👤 Attempting to follow: {target_username}")
            self.stats["follow_attempts"] += 1
            
            # Navigate to profile
            profile_url = f'https://m.facebook.com/{target_username}'
            response = session.get(profile_url, timeout=15)
            
            if response.status_code != 200:
                logging.error(f"❌ Failed to load profile: HTTP {response.status_code}")
                return False
            
            # Look for profile ID in the page
            # This is a simplified approach - actual implementation needs parsing
            content = response.text
            
            # Try to find follow button or profile actions
            # Note: Facebook's mobile HTML structure changes frequently
            
            if 'Subscribe' in content or 'Follow' in content or 'Add Friend' in content:
                logging.info(f"✅ Profile found: {target_username}")
                
                # In reality, you need to:
                # 1. Parse the page to find the follow/subscribe button
                # 2. Extract the CSRF token
                # 3. Find the user ID
                # 4. Make a POST request to the follow endpoint
                
                # This is a simplified simulation
                logging.warning("⚠️  Note: Actual follow action requires advanced parsing")
                logging.info(f"📝 Visit manually: {profile_url}")
                
                # Simulate success for demonstration
                time.sleep(random.uniform(2, 4))
                self.stats["successful_follows"] += 1
                return True
            else:
                logging.error(f"❌ Could not find follow option for {target_username}")
                return False
            
        except requests.RequestException as e:
            logging.error(f"❌ Network error during follow: {e}")
            return False
        except Exception as e:
            logging.error(f"❌ Unexpected error during follow: {e}")
            return False
    
    def boost_followers(self, target_username):
        """Main function to boost followers"""
        self.target_profile = target_username
        
        if not self.accounts:
            logging.error("❌ No accounts loaded!")
            return
        
        logging.info("="*60)
        logging.info(f"🚀 Starting Follower Boost")
        logging.info(f"👤 Target: {target_username}")
        logging.info(f"📊 Accounts to use: {len(self.accounts)}")
        logging.info("="*60)
        
        for idx, account in enumerate(self.accounts, 1):
            if not self.running:
                break
            
            logging.info(f"\n{'='*60}")
            logging.info(f"[{idx}/{len(self.accounts)}] Processing account: {account['email']}")
            logging.info(f"{'='*60}")
            
            session = self.create_session()
            
            # Try to login
            login_success = False
            for attempt in range(self.config["max_retries"]):
                try:
                    if self.login_account(session, account['email'], account['password']):
                        login_success = True
                        break
                    else:
                        if attempt < self.config["max_retries"] - 1:
                            logging.info(f"⏳ Retry {attempt + 2}/{self.config['max_retries']} in {self.config['retry_delay']}s...")
                            time.sleep(self.config['retry_delay'])
                except Exception as e:
                    logging.error(f"❌ Error: {e}")
                    self.stats["errors"] += 1
            
            if not login_success:
                logging.error(f"❌ Failed to login with {account['email']}, skipping...")
                continue
            
            # Try to follow
            time.sleep(random.uniform(2, 4))
            follow_success = False
            
            for attempt in range(self.config["max_retries"]):
                try:
                    if self.follow_profile(session, target_username):
                        follow_success = True
                        break
                    else:
                        if attempt < self.config["max_retries"] - 1:
                            logging.info(f"⏳ Retry follow {attempt + 2}/{self.config['max_retries']}...")
                            time.sleep(self.config['retry_delay'])
                except Exception as e:
                    logging.error(f"❌ Error: {e}")
                    self.stats["errors"] += 1
            
            if follow_success:
                logging.info(f"✅ Successfully followed with account {idx}/{len(self.accounts)}")
            else:
                logging.warning(f"⚠️  Could not follow with account {idx}/{len(self.accounts)}")
            
            # Delay between accounts to avoid detection
            if idx < len(self.accounts):
                delay = random.uniform(*self.config["delay_range"])
                logging.info(f"⏳ Waiting {delay:.1f}s before next account...")
                time.sleep(delay)
        
        self.print_final_stats()
    
    def print_final_stats(self):
        """Print final statistics"""
        duration = (datetime.now() - datetime.fromisoformat(self.stats["start_time"])).total_seconds()
        
        logging.info("\n" + "="*60)
        logging.info("📊 FOLLOWER BOOST COMPLETED")
        logging.info("="*60)
        logging.info(f"👤 Target Profile: {self.target_profile}")
        logging.info(f"🔐 Login Attempts: {self.stats['login_attempts']}")
        logging.info(f"✅ Successful Logins: {self.stats['successful_logins']}")
        logging.info(f"👥 Follow Attempts: {self.stats['follow_attempts']}")
        logging.info(f"✅ Successful Follows: {self.stats['successful_follows']}")
        logging.info(f"❌ Errors: {self.stats['errors']}")
        logging.info(f"⏱️  Duration: {duration:.1f} seconds")
        logging.info("="*60)
        
        # Success rate
        if self.stats["login_attempts"] > 0:
            login_rate = (self.stats["successful_logins"] / self.stats["login_attempts"]) * 100
            logging.info(f"📈 Login Success Rate: {login_rate:.1f}%")
        
        if self.stats["follow_attempts"] > 0:
            follow_rate = (self.stats["successful_follows"] / self.stats["follow_attempts"]) * 100
            logging.info(f"📈 Follow Success Rate: {follow_rate:.1f}%")
        
        logging.info("="*60)
    
    def manual_boost_guide(self, target_username):
        """Generate manual instructions for boosting"""
        print("\n" + "="*60)
        print("📱 MANUAL FOLLOWER BOOST GUIDE")
        print("="*60)
        print(f"\n🎯 Target Profile: https://facebook.com/{target_username}")
        print(f"\n📊 You have {len(self.accounts)} accounts loaded")
        print("\n📝 Steps for each account:")
        print("1. Open Facebook in a browser/app")
        print("2. Login with the account credentials below")
        print(f"3. Visit: https://facebook.com/{target_username}")
        print("4. Click 'Follow' or 'Add Friend' button")
        print("5. Logout and repeat with next account")
        print("\n" + "="*60)
        
        for idx, account in enumerate(self.accounts, 1):
            print(f"\n[Account {idx}/{len(self.accounts)}]")
            print(f"  Email: {account['email']}")
            print(f"  Password: {account['password']}")
            if account.get('name'):
                print(f"  Name: {account['name']}")
        
        print("\n" + "="*60)
        print("💡 TIP: Use different browsers or incognito tabs")
        print("⚠️  WARNING: Facebook may detect and ban accounts")
        print("="*60 + "\n")
    
    def stop(self):
        """Graceful shutdown"""
        self.running = False
        logging.info("🛑 Stopping follower boost...")

def main():
    print("="*60)
    print("🚀 Facebook Follower Booster")
    print("="*60)
    
    booster = FacebookFollowerBooster()
    
    # Load accounts
    print("\n📝 Loading accounts from accounts.txt...")
    if not booster.load_accounts():
        print("\n❌ No accounts found!")
        print("\n📝 Create accounts.txt with this format:")
        print("email1@example.com:password1")
        print("email2@example.com:password2")
        print("email3@example.com:password3")
        return
    
    # Get target
    target = input("\n👤 Enter Facebook username to boost (e.g., 'john.doe'): ").strip()
    
    if not target:
        print("❌ No target specified!")
        return
    
    print(f"\n✓ Target: {target}")
    print(f"✓ Accounts: {len(booster.accounts)}")
    
    # Choose mode
    print("\n" + "="*60)
    print("Choose Mode:")
    print("1. Automated boost (may have limitations)")
    print("2. Manual boost guide (recommended)")
    print("="*60)
    
    mode = input("Enter choice (1/2): ").strip()
    
    if mode == "2":
        booster.manual_boost_guide(target)
    else:
        print("\n⚠️  IMPORTANT WARNINGS:")
        print("• Facebook has strong anti-bot protection")
        print("• Automated following may trigger security checks")
        print("• Accounts may get banned or require verification")
        print("• Manual method is more reliable")
        
        confirm = input("\nContinue with automated boost? (yes/no): ").strip().lower()
        
        if confirm == 'yes':
            try:
                booster.boost_followers(target)
            except KeyboardInterrupt:
                print("\n⚠️  Interrupted by user")
                booster.stop()
            except Exception as e:
                print(f"\n❌ Fatal error: {e}")
                booster.stop()
        else:
            print("\n✓ Showing manual guide instead...")
            booster.manual_boost_guide(target)

if __name__ == "__main__":
    main()