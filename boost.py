import random
import string
import requests
import os
from pystyle import Colors, Colorate
import time
from requests.exceptions import ProxyError, ConnectionError, Timeout

def ngl():
    def deviceId():
        characters = string.ascii_lowercase + string.digits
        return "-".join([
            ''.join(random.choices(characters, k=8)),
            ''.join(random.choices(characters, k=4)),
            ''.join(random.choices(characters, k=4)),
            ''.join(random.choices(characters, k=4)),
            ''.join(random.choices(characters, k=12))
        ])

    def UserAgent():
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
        ]
        return random.choice(user_agents)

    def fetch_proxies():
        proxies = []
        sources = [
            "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
            "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/https.txt",
            "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt"
        ]
        for url in sources:
            try:
                print(Colorate.Horizontal(Colors.blue_to_purple, f"[~] Fetching proxies from {url} ..."))
                r = requests.get(url, timeout=10)
                new_proxies = [p.strip() for p in r.text.splitlines() if p.strip() and ":" in p]
                proxies += new_proxies
                print(Colorate.Horizontal(Colors.green_to_blue, f"[+] Got {len(new_proxies)} proxies from {url}"))
            except Exception as e:
                print(Colorate.Horizontal(Colors.red_to_purple, f"[-] Failed to fetch from {url}: {e}"))
        print(Colorate.Horizontal(Colors.green_to_blue, f"[✓] Total proxies fetched: {len(proxies)}"))
        return proxies

    def Proxy():
        proxies_list = fetch_proxies()
        if not proxies_list:
            print("[-] No proxies fetched, using direct connection")
            return None

        # Prioritize SOCKS5 first
        socks5 = [p for p in proxies_list if "1080" in p or "socks5" in p]
        http_https = [p for p in proxies_list if not ("1080" in p or "socks5" in p)]
        proxies_list = socks5 + http_https
        random.shuffle(proxies_list)

        for proxy in proxies_list[:20]:  # test only first 20
            if proxy.startswith("socks5://"):
                test_proxy = {"http": proxy, "https": proxy}
            else:
                test_proxy = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
            print(Colorate.Horizontal(Colors.blue_to_purple, f"[~] Testing proxy: {proxy}"))
            try:
                r = requests.get("http://httpbin.org/ip", proxies=test_proxy, timeout=10)
                if r.status_code == 200:
                    print(Colorate.Horizontal(Colors.green_to_blue, f"[+] Using proxy: {proxy}"))
                    return test_proxy   # ✅ immediately return first working proxy
            except Exception:
                print(Colorate.Horizontal(Colors.red_to_purple, f"[-] Dead proxy skipped: {proxy}"))
                continue

        # Forced fallback: use first proxy anyway
        fallback = proxies_list[0]
        print(Colorate.Horizontal(Colors.red_to_purple, f"[!] No validated proxies, forcing use of: {fallback}"))
        return {"http": f"http://{fallback}", "https": f"http://{fallback}"}

    os.system('cls' if os.name == 'nt' else 'clear')

    # ASCII banner updated to ANOS
    print(Colorate.Vertical(Colors.blue_to_purple,""" 
        ░█████╗░███╗░░██╗░█████╗░░██████╗
        ██╔══██╗████╗░██║██╔══██╗██╔════╝
        ███████║██╔██╗██║██║░░██║╚█████╗░
        ██╔══██║██║╚████║██║░░██║░╚═══██╗
        ██║░░██║██║░╚███║╚█████╔╝██████╔╝
        ╚═╝░░╚═╝╚═╝░░╚══╝░╚════╝░╚═════╝░
    """))

    nglusername = input(Colorate.Vertical(Colors.blue_to_purple,"Username: "))
    message = input(Colorate.Vertical(Colors.blue_to_purple,"Message: "))
    Count = int(input(Colorate.Vertical(Colors.blue_to_purple,"Count: ")))
    delay = float(input(Colorate.Vertical(Colors.blue_to_purple,"Delay (seconds, 0 for fastest): ")))
    use_proxy = input(Colorate.Vertical(Colors.blue_to_purple, "Use proxy? (y/n): ")).lower()

    proxies = Proxy() if use_proxy == "y" else None

    sent_count = 0
    failed_count = 0

    print(Colorate.Vertical(Colors.green_to_blue,"**********************************************************"))
    print(Colorate.Horizontal(Colors.green_to_blue, f"[✓] Starting run with proxy: {proxies if proxies else 'Direct connection'}"))

    while sent_count < Count:
        headers = {
            'Host': 'ngl.link',
            'accept': '*/*',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'x-requested-with': 'XMLHttpRequest',
            'user-agent': UserAgent(),
            'origin': 'https://ngl.link',
            'referer': f'https://ngl.link/{nglusername}',
            'accept-language': 'en-US,en;q=0.9',
        }
        data = {
            'username': nglusername,
            'question': message,
            'deviceId': deviceId(),
            'gameSlug': '',
            'referrer': '',
        }

        try:
            response = requests.post(
                'https://ngl.link/api/submit',
                headers=headers,
                data=data,
                proxies=proxies,
                timeout=10
            )
            if response.status_code == 200:
                sent_count += 1
            else:
                failed_count += 1
            progress = f"{sent_count + failed_count}/{Count}"
            print(f"Sent: {sent_count}")
            print(f"Failed: {failed_count}")
            print(f"Progress: {progress}")
            time.sleep(delay)
        except (ProxyError, ConnectionError, Timeout):
            failed_count += 1
            progress = f"{sent_count + failed_count}/{Count}"
            print(f"Sent: {sent_count}")
            print(f"Failed: {failed_count}")
            print(f"Progress: {progress}")
            if use_proxy == "y":
                proxies = Proxy()  # fetch new proxy immediately
            continue

    print(Colorate.Horizontal(Colors.green_to_blue, f"[✓] Run complete — Sent: {sent_count}, Failed: {failed_count}, Progress: {sent_count+failed_count}/{Count}"))

ngl()