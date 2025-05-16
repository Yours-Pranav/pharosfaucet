# 🚰 Pharos Network Faucet Tool

<p align="center">
  <img src="https://img.shields.io/badge/Network-Pharos-blueviolet?style=for-the-badge&logo=ethereum" />
  <img src="https://img.shields.io/badge/Support-Telegram-blue?style=for-the-badge&logo=telegram" />
  <img src="https://img.shields.io/badge/Status-Active-brightgreen?style=for-the-badge&logo=vercel" />
</p>

> ✅ Automatically claim Pharos Network faucet for multiple wallets with proxy rotation and retry logic.
> 🛡️ Skips retries if the wallet already claimed (cooldown).
> 🧠 Built-in multithreading, signature-based login, and logging to `success.txt` / `failed.txt`.

---

## 🚀 Features

* 💧 Faucet claim automation for testnet
* 🔐 EVM wallet message signing using private keys
* 🔁 Smart retry (up to 5 attempts) with proxy rotation
* 🧾 Logging:

  * ✅ `success.txt` – `wallet:privateKey` format
  * ❌ `failed.txt` – privateKey only
* 🧠 Skips wallets if already claimed due to cooldown
* 🧵 Fast execution using multithreading (`THREADS = 100`)

---

## 🧰 Requirements

Install dependencies via:

```bash
pip install -r requirements.txt
```

**Python 3.10+ is recommended**

---

## 📁 Setup

### 📦 Clone this Repository

```bash
git clone https://github.com/RPC-Hubs/Faucet-Pharos-Network.git
cd Faucet-Pharos-Network
```

---

## 🖥️ OS-Specific Instructions

### 🐧 Linux/macOS

```bash
# Step 1: Create and activate a virtual environment (optional but recommended)
python3 -m venv env
source env/bin/activate

# Step 2: Install dependencies
pip install -r requirements.txt

# Step 3: Add your wallets and proxies
nano priv.txt     # Add one private key per line
nano proxies.txt  # Format: http://user:pass@ip:port

# Step 4: Run the script
python3 main.py
```

---

### 🪟 Windows

```bash
:: Step 1: (Optional) Create virtual environment
python -m venv env
env\Scripts\activate

:: Step 2: Install dependencies
pip install -r requirements.txt

:: Step 3: Add your private keys and proxies
notepad priv.txt     :: Add one private key per line
notepad proxies.txt  :: Format: http://user:pass@ip:port

:: Step 4: Run the script
python main.py
```
---

## 🧠 Configuration Tips

You can control the script's concurrency and retry behavior by editing these lines in `main.py`:

```python
THREADS = 100        # Line 13 - Number of parallel threads
MAX_RETRIES = 5      # Line 14 - Retry attempts per wallet
```

Adjust as needed depending on your system or proxy stability.

---

## 🔹 Menu Options Explained

```text
========= Pharos Network Faucet Menu =========
1. Faucet Pharos (RECOMMENDED)
2. Faucet USDC (Zenithswap)
3. Faucet both (Pharos then USDC)
4. Exit
```

---

## 🧡 Notes

* Each wallet will be signed using the phrase `pharos` and submitted to the login API.
* Proxies are rotated every retry attempt.
* `success.txt` contains both wallet address and private key.
* `failed.txt` logs private keys of wallets that failed all retries.

---

## 📸 Example Output

```
[15:03:22 16/05/2025] [1] [0xAb...Cd1234] Proxy: 103.1.1.2 [Retry 1/5]
[15:03:23 16/05/2025] [1] [0xAb...Cd1234] Login successful.
[15:03:25 16/05/2025] [1] [0xAb...Cd1234] Faucet claim successful!
```

---

## 🙋‍♂️ Community & Support

Join the team or get help here:

- 💬 [RPC Community Chat](https://t.me/chat_RPC_Community)  
- 📣 [RPC Hubs Channel](https://t.me/RPC_Hubs)  

---

> Made with ❤️ by RPC-Hubs
