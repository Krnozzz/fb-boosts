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

    def Proxy():
        # Load proxies from proxies.txt
        try:
            with open("proxies.txt", "r") as file:
                proxies_list = [p.strip() for p in file.readlines() if p.strip()]
        except FileNotFoundError:
            print("[-] proxies.txt not found, using direct connection")
            return None

        random.shuffle(proxies_list)

        for proxy in proxies_list:
            # Detect protocol automatically
            if proxy.startswith("socks5://"):
                test_proxy = {"http": proxy, "https": proxy}
            elif proxy.startswith("https://") or proxy.startswith("http://"):
                test_proxy = {"http": proxy, "https": proxy}
            else:
                # If no scheme provided, assume http://
                test_proxy = {"http": f"http://{proxy}", "https": f"http://{proxy}"}

            try:
                r = requests.get("https://httpbin.org/ip", proxies=test_proxy, timeout=5)
                if r.status_code == 200:
                    print(f"[+] Valid proxy found: {proxy}")
                    return test_proxy
            except Exception:
                print(f"[-] Dead proxy skipped: {proxy}")
                continue

        print("[-] No working proxies available, using direct connection")
        return None

    R = '\033[31m'
    G = '\033[32m'
    W = '\033[0m'

    os.system('cls' if os.name == 'nt' else 'clear')

    # Updated ASCII banner to ANOS
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

    print(Colorate.Vertical(Colors.green_to_blue,"**********************************************************"))

    value = 0
    notsend = 0
    while value < Count:
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
                notsend = 0
                value += 1
                print(G + "[+]" + W + f" Send => {value}")
            else:
                notsend += 1
                print(R + "[-]" + W + " Not Sent")

            if notsend >= 3:
                print(R + "[!]" + W + " Rotating info...")
                if use_proxy == "y":
                    proxies = Proxy()
                notsend = 0

            time.sleep(delay)

        except (ProxyError, ConnectionError, Timeout):
            print(R + "[-]" + W + " Proxy/Connection failed, rotating...")
            if use_proxy == "y":
                proxies = Proxy()

ngl()