import requests
import threading
from concurrent.futures import ThreadPoolExecutor
from web3.auto import w3
from eth_account.messages import encode_defunct
import time
from colorama import Fore, Style, init as colorama_init
from banner import display_banner

colorama_init(autoreset=True)

# ========== CONFIG ==========
THREADS = 100
MAX_RETRIES = 5

PRIV_FILE = "priv.txt"
PROXIES_FILE = "proxies.txt"
GET_IP_URL = "https://api64.ipify.org?format=json"

LOGIN_URL = "https://api.pharosnetwork.xyz/user/login"
FAUCET_PHAROS_URL = "https://api.pharosnetwork.xyz/faucet/daily"

ZENITH_FAUCET_URL = "https://testnet-router.zenithswap.xyz/api/v1/faucet"
ZENITH_TOKEN_ADDRESS = "0xAD902CF99C2dE2f1Ba5ec4D642Fd7E49cae9EE37"

SIGN_MESSAGE = "pharos"
PHAROS_SUCCESS_FILE = "pharos_success.txt"
PHAROS_FAILED_FILE = "pharos_failed.txt"
USDC_SUCCESS_FILE = "usdc_success.txt"
USDC_FAILED_FILE = "usdc_failed.txt"
# ============================

print_lock = threading.Lock()

def now_str():
    return time.strftime("[%H:%M:%S %d/%m/%Y]")

def short_addr(address):
    return f"{address[:4]}...{address[-6:]}"

def load_lines(path):
    with open(path, "r") as f:
        return [line.strip() for line in f if line.strip()]

def get_proxy_session(proxy):
    session = requests.Session()
    session.proxies = {
        "http": proxy,
        "https": proxy,
    }
    return session

def get_current_ip(session):
    try:
        r = session.get(GET_IP_URL, timeout=10)
        return r.json().get("ip", "???")
    except Exception:
        return "???"

def sign_message(privkey, message):
    acct = w3.eth.account.from_key(privkey)
    msg = encode_defunct(text=message)
    signed = acct.sign_message(msg)
    return acct.address, signed.signature.hex()

def faucet_zenith_usdc_with_retry(address, privkey, proxies, idx):
    n_proxy = len(proxies)
    retry = 0
    success = False
    prefix = ""
    session = None
    while retry < MAX_RETRIES and not success:
        proxy = proxies[(idx + retry - 1) % n_proxy]
        session = get_proxy_session(proxy)
        prefix = f"{Fore.CYAN}{now_str()} [{idx}] [{Fore.YELLOW}{short_addr(address)}{Fore.CYAN}]"
        with print_lock:
            print(f"{prefix} USDC faucet [Retry {retry + 1}/{MAX_RETRIES}] Proxy: {Fore.GREEN}{get_current_ip(session)}")
        headers = {
            "Accept": "*/*",
            "Content-Type": "application/json",
            "Origin": "https://testnet.zenithswap.xyz",
            "Referer": "https://testnet.zenithswap.xyz/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
        }
        payload = {
            "tokenAddress": ZENITH_TOKEN_ADDRESS,
            "userAddress": address
        }
        try:
            resp = session.post(ZENITH_FAUCET_URL, headers=headers, json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            status = data.get("status")
            message = data.get("message", "")
            if status == 200 and message == "ok":
                with print_lock:
                    print(f"{prefix} {Fore.GREEN}USDC faucet via Zenithswap successful!")
                with open(USDC_SUCCESS_FILE, "a", encoding="utf-8") as f:
                    f.write(f"{address}:{privkey}\n")
                success = True
                break
            elif "has already got token today" in message:
                with print_lock:
                    print(f"{prefix} {Fore.YELLOW}USDC faucet already claimed today. Skipping retries.")
                with open(USDC_SUCCESS_FILE, "a", encoding="utf-8") as f:
                    f.write(f"{address}:{privkey}\n")
                success = True
                break
            else:
                with print_lock:
                    print(f"{prefix} {Fore.RED}USDC faucet failed: {data}")
                retry += 1
        except Exception as e:
            with print_lock:
                print(f"{prefix} {Fore.RED}USDC faucet request error: {e}")
            retry += 1

    if not success:
        with print_lock:
            print(f"{prefix} {Fore.RED}USDC faucet FAILED after {MAX_RETRIES} retries. Logging to usdc_failed.txt.")
        with open(USDC_FAILED_FILE, "a", encoding="utf-8") as f:
            f.write(f"{address}:{privkey}\n")


def faucet_pharos(idx, privkey, proxies):
    n_proxy = len(proxies)
    retry = 0
    faucet_success = False
    acct_addr = ""
    jwt = ""
    session = None
    prefix = ""
    while retry < MAX_RETRIES and not faucet_success:
        proxy = proxies[(idx + retry - 1) % n_proxy]
        session = get_proxy_session(proxy)
        ip = get_current_ip(session)
        acct_addr, signature = sign_message(privkey, SIGN_MESSAGE)
        prefix = f"{Fore.CYAN}{now_str()} [{idx}] [{Fore.YELLOW}{short_addr(acct_addr)}{Fore.CYAN}]"
        with print_lock:
            print(f"{prefix} Proxy: {Fore.GREEN}{ip} [Retry {retry + 1}/{MAX_RETRIES}]")
        login_params = {
            "address": acct_addr,
            "signature": signature
        }
        headers_login = {
            "Accept": "application/json, text/plain, */*",
            "Authorization": "Bearer null",
            "Origin": "https://testnet.pharosnetwork.xyz",
            "Referer": "https://testnet.pharosnetwork.xyz/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
        }
        try:
            r_login = session.post(LOGIN_URL, headers=headers_login, params=login_params, timeout=30)
            r_login.raise_for_status()
            data_login = r_login.json()
            jwt = data_login.get("data", {}).get("jwt", "")
            if not jwt:
                raise Exception("No jwt returned")
            with print_lock:
                print(f"{prefix} {Fore.GREEN}Login successful.")
        except Exception as e:
            with print_lock:
                print(f"{prefix} {Fore.RED}Login failed: {e}")
            retry += 1
            continue

        headers_faucet = headers_login.copy()
        headers_faucet["Authorization"] = f"Bearer {jwt}"
        faucet_params = {
            "address": acct_addr
        }
        try:
            r_faucet = session.post(FAUCET_PHAROS_URL, headers=headers_faucet, params=faucet_params, timeout=30)
            r_faucet.raise_for_status()
            data_faucet = r_faucet.json()
            msg = data_faucet.get("msg", "")
            if msg == "ok":
                with print_lock:
                    print(f"{prefix} {Fore.GREEN}Pharos faucet claim successful!")
                with open(PHAROS_SUCCESS_FILE, "a", encoding="utf-8") as sf:
                    sf.write(f"{acct_addr}:{privkey}\n")
                faucet_success = True
            elif msg == "faucet did not cooldown":
                with print_lock:
                    print(f"{prefix} {Fore.YELLOW}Pharos faucet already claimed (cooldown). Skipping retries, marking as success.")
                with open(PHAROS_SUCCESS_FILE, "a", encoding="utf-8") as sf:
                    sf.write(f"{acct_addr}:{privkey}\n")
                faucet_success = True
                break
            else:
                with print_lock:
                    print(f"{prefix} {Fore.RED}Pharos faucet claim failed: {data_faucet}")
                retry += 1
        except Exception as e:
            with print_lock:
                print(f"{prefix} {Fore.RED}Pharos faucet request failed: {e}")
            retry += 1

    if not faucet_success:
        with print_lock:
            print(f"{prefix} {Fore.RED}FAILED after {MAX_RETRIES} retries. Logging to pharos_failed.txt.")
        with open(PHAROS_FAILED_FILE, "a", encoding="utf-8") as ff:
            ff.write(f"{acct_addr}:{privkey}\n")
    return faucet_success, acct_addr, privkey, session, prefix

def faucet_both(idx, privkey, proxies):
    success, acct_addr, privkey, session, prefix = faucet_pharos(idx, privkey, proxies)
    if acct_addr == "":
        acct_addr, _ = sign_message(privkey, SIGN_MESSAGE)
    faucet_zenith_usdc_with_retry(acct_addr, privkey, proxies, idx)

def faucet_usdc(idx, privkey, proxies):
    acct_addr, _ = sign_message(privkey, SIGN_MESSAGE)
    faucet_zenith_usdc_with_retry(acct_addr, privkey, proxies, idx)


def menu():
    print(Fore.CYAN + "\n========= Pharos Network Faucet Menu =========")
    print(Fore.YELLOW + "1. Faucet Pharos")
    print(Fore.YELLOW + "2. Faucet USDC (Zenithswap)")
    print(Fore.YELLOW + "3. Faucet both (Pharos then USDC)")
    print(Fore.YELLOW + "4. Exit")
    print(Fore.CYAN + "==========================================")

    while True:
        try:
            choice = input(Fore.GREEN + "Enter your choice (1/2/3/4): ").strip()
        except EOFError:
            choice = "4"
        if choice in ["1", "2", "3", "4"]:
            return choice
        else:
            print(Fore.RED + "Invalid choice! Please enter 1, 2, 3, or 4.")

def main():
    privs = load_lines(PRIV_FILE)
    proxies = load_lines(PROXIES_FILE)
    if not proxies:
        print(f"{Fore.RED}No proxies found, exiting!")
        return


    while True:
        display_banner() 
        choice = menu()
        if choice == "4":
            print(Fore.YELLOW + "Exit. Goodbye!")
            break

        with ThreadPoolExecutor(max_workers=THREADS) as executor:
            futures = []
            for idx, priv in enumerate(privs, 1):
                if choice == "1":
                    futures.append(executor.submit(faucet_pharos, idx, priv, proxies))
                elif choice == "2":
                    futures.append(executor.submit(faucet_usdc, idx, priv, proxies))
                elif choice == "3":
                    futures.append(executor.submit(faucet_both, idx, priv, proxies))
            for f in futures:
                f.result()

if __name__ == "__main__":
    main()
