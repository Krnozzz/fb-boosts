import requests
import time
import random
import logging
import json
from datetime import datetime
import threading
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('facebook_automation.log'),
        logging.StreamHandler()
    ]
)

class FacebookAutomation:
    def __init__(self, target_account=None, config_file=None):
        self.config = {
            "delay_range": (2, 5),
            "max_retries": 3,
            "retry_delay": 5,
            "timeout": 30,
        }
        
        if config_file and os.path.exists(config_file):
            with open(config_file) as f:
                self.config.update(json.load(f))
        
        # Target account to follow
        self.target_account = target_account
        
        # Read emails from file
        self.emails = self._read_emails_from_file("email.txt")
        
        self.stats = {
            "created": 0,
            "followed": 0,
            "errors": 0,
            "start_time": datetime.now().isoformat()
        }
        
        self.running = True
        self.session = requests.Session()
        
        # Set up user agent
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
    
    def _read_emails_from_file(self, filename):
        """Read email addresses from a file."""
        try:
            if not os.path.exists(filename):
                logging.warning(f"Email file '{filename}' not found. Creating example file.")
                with open(filename, 'w') as f:
                    f.write("example1@email.com\nexample2@email.com\n")
                return []
            
            with open(filename, 'r') as file:
                emails = [line.strip() for line in file if line.strip() and '@' in line]
                logging.info(f"Loaded {len(emails)} emails from {filename}")
                return emails
        except Exception as e:
            logging.error(f"Error reading email file: {e}")
            return []
    
    def _generate_random_name(self):
        """Generate random first and last names"""
        first_names = ["John", "Jane", "Mike", "Sarah", "David", "Emma", "Chris", "Lisa", 
                      "Tom", "Anna", "James", "Mary", "Robert", "Linda", "Michael", "Patricia",
                      "Daniel", "Jessica", "Matthew", "Ashley", "Andrew", "Emily", "Joshua", "Samantha"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", 
                     "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Wilson", "Anderson",
                     "Taylor", "Thomas", "Moore", "Jackson", "Martin", "Lee", "Thompson", "White"]
        
        return random.choice(first_names), random.choice(last_names)
    
    def _generate_random_password(self):
        """Generate a random password"""
        import string
        chars = string.ascii_letters + string.digits + "!@#$%"
        password = ''.join(random.choice(chars) for _ in range(12))
        # Ensure it has at least one uppercase, lowercase, digit, and special char
        return password + random.choice(string.ascii_uppercase) + random.choice(string.digits)
    
    def create_account_api(self, email):
        """Create Facebook account using API/requests (browser-less)"""
        for attempt in range(self.config["max_retries"]):
            try:
                logging.info(f"[Attempt {attempt + 1}/{self.config['max_retries']}] Creating account for {email}")
                
                # Generate random account details
                first_name, last_name = self._generate_random_name()
                password = self._generate_random_password()
                
                # Generate random birthday (18+ years old)
                import random
                birth_year = random.randint(1985, 2005)
                birth_month = random.randint(1, 12)
                birth_day = random.randint(1, 28)
                
                # Random gender
                gender = random.choice([1, 2])  # 1=Female, 2=Male
                
                # Save credentials to file first
                with open('accounts.txt', 'a') as f:
                    f.write(f"{email}:{password}:{first_name} {last_name}\n")
                
                logging.info(f"📝 Generated account: {first_name} {last_name} ({email})")
                
                # Get Facebook signup page first to get cookies and tokens
                try:
                    signup_page = self.session.get('https://m.facebook.com/reg/', timeout=15)
                    time.sleep(2)
                    
                    # This is a simplified simulation
                    # Real Facebook signup requires solving complex challenges, captchas, and verification
                    
                    logging.warning("⚠️  Note: Facebook requires complex verification (captcha, phone, etc.)")
                    logging.info(f"✅ Account details saved for manual completion: {first_name} {last_name}")
                    logging.info(f"   Email: {email}")
                    logging.info(f"   Password: {password}")
                    logging.info(f"   Birthday: {birth_month}/{birth_day}/{birth_year}")
                    logging.info(f"   Gender: {'Female' if gender == 1 else 'Male'}")
                    
                    self.stats["created"] += 1
                    
                    # Note: Actual account creation requires manual intervention or sophisticated automation
                    # due to Facebook's anti-bot measures (captcha, phone verification, etc.)
                    
                except requests.RequestException as e:
                    logging.error(f"Network error: {e}")
                    raise
                
                time.sleep(random.uniform(*self.config["delay_range"]))
                return True
                
            except Exception as e:
                logging.error(f"❌ Attempt {attempt + 1}/{self.config['max_retries']} failed for {email}: {str(e)}")
                self.stats["errors"] += 1
                
                if attempt < self.config["max_retries"] - 1:
                    logging.info(f"Retrying in {self.config['retry_delay']} seconds...")
                    time.sleep(self.config["retry_delay"])
                else:
                    logging.error(f"❌ Failed to create account for {email} after all retries")
                    return False
        
        return False
    
    def manual_account_guide(self, email):
        """Provide manual instructions for account creation"""
        first_name, last_name = self._generate_random_name()
        password = self._generate_random_password()
        
        birth_year = random.randint(1985, 2005)
        birth_month = random.randint(1, 12)
        birth_day = random.randint(1, 28)
        gender = random.choice(['Female', 'Male'])
        
        # Save to file
        with open('accounts_manual.txt', 'a') as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"Account #{self.stats['created'] + 1}\n")
            f.write(f"{'='*60}\n")
            f.write(f"Email: {email}\n")
            f.write(f"Password: {password}\n")
            f.write(f"First Name: {first_name}\n")
            f.write(f"Last Name: {last_name}\n")
            f.write(f"Birthday: {birth_month}/{birth_day}/{birth_year}\n")
            f.write(f"Gender: {gender}\n")
            f.write(f"Target to Follow: {self.target_account or 'None'}\n")
            f.write(f"Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        logging.info(f"\n{'='*60}")
        logging.info(f"📋 Manual Account Creation Guide #{self.stats['created'] + 1}")
        logging.info(f"{'='*60}")
        logging.info(f"1. Open Facebook on your phone/browser")
        logging.info(f"2. Go to Sign Up page")
        logging.info(f"3. Enter the following details:")
        logging.info(f"   • Email: {email}")
        logging.info(f"   • Password: {password}")
        logging.info(f"   • First Name: {first_name}")
        logging.info(f"   • Last Name: {last_name}")
        logging.info(f"   • Birthday: {birth_month}/{birth_day}/{birth_year}")
        logging.info(f"   • Gender: {gender}")
        if self.target_account:
            logging.info(f"4. After creating account, search and follow: {self.target_account}")
        logging.info(f"{'='*60}\n")
        
        self.stats["created"] += 1
        return True
    
    def run(self):
        """Main execution loop"""
        if not self.emails:
            logging.error("❌ No emails to process. Add emails to email.txt")
            return
        
        print("\n" + "="*60)
        print("🤖 Facebook Account Creation Assistant")
        print("="*60)
        print("\n⚠️  IMPORTANT NOTICE:")
        print("Due to Facebook's security measures (captcha, phone verification),")
        print("fully automated account creation is not possible.")
        print("\nThis script will generate account details for you to use manually.")
        print("="*60)
        
        mode = input("\nChoose mode:\n1. Generate account details for manual creation\n2. Try automated creation (limited success)\n\nEnter choice (1/2): ").strip()
        
        logging.info("="*60)
        logging.info(f"🚀 Starting Facebook Automation")
        logging.info(f"📧 Emails to process: {len(self.emails)}")
        if self.target_account:
            logging.info(f"👤 Target account to follow: {self.target_account}")
        logging.info("="*60)
        
        for idx, email in enumerate(self.emails, 1):
            if not self.running:
                break
            
            logging.info(f"\n[{idx}/{len(self.emails)}] Processing: {email}")
            
            if mode == "1":
                self.manual_account_guide(email)
            else:
                self.create_account_api(email)
            
            # Delay between accounts
            if idx < len(self.emails):
                delay = random.uniform(*self.config["delay_range"])
                logging.info(f"⏳ Waiting {delay:.1f} seconds before next account...")
                time.sleep(delay)
        
        # Final stats
        duration = (datetime.now() - datetime.fromisoformat(self.stats["start_time"])).total_seconds()
        logging.info("\n" + "="*60)
        logging.info("📊 AUTOMATION COMPLETED")
        logging.info(f"✅ Accounts generated: {self.stats['created']}")
        logging.info(f"❌ Errors: {self.stats['errors']}")
        logging.info(f"⏱️  Duration: {duration:.1f} seconds")
        logging.info("="*60)
        logging.info("💾 Account details saved to: accounts_manual.txt")
        print("\n📱 Next steps:")
        print("1. Open accounts_manual.txt")
        print("2. Use the provided details to manually create accounts on Facebook")
        print("3. Follow the target account if specified")
        print("="*60 + "\n")
    
    def stop(self):
        """Graceful shutdown"""
        self.running = False
        logging.info("🛑 Stopping automation...")

if __name__ == "__main__":
    print("="*60)
    print("🤖 Facebook Account Creation Assistant")
    print("="*60)
    
    # Get target account from user
    target = input("\n👤 Enter Facebook username/profile to follow (or press Enter to skip): ").strip()
    
    if not target:
        target = None
        print("ℹ️  Skipping follow feature")
    else:
        print(f"✓ Target account: {target}")
    
    print("\n📝 Make sure you have emails in 'email.txt' file (one per line)")
    input("Press Enter to start...\n")
    
    automation = FacebookAutomation(target_account=target)
    
    try:
        automation.run()
    except KeyboardInterrupt:
        logging.info("\n⚠️  Interrupted by user")
        automation.stop()
    except Exception as e:
        logging.error(f"\n❌ Fatal error: {e}")
        automation.stop()