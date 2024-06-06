import requests
import json
import re
import time
from rich.console import Console
from concurrent.futures import ThreadPoolExecutor, as_completed
import datetime
import os
from keyauth import Keyauth
from keyauth import misc
import hashlib
import sys
import fade

os.system('title Potion Bot - Filter Deployers')

banner1 = """  
  ___  ___  ___  _  ___  _ _ 
 | . \| . ||_ _|| || . || \ |
 |  _/| | | | | | || | ||   |
 |_|  `___' |_| |_|`___'|_\_|\033[0;37m Deployer Filter v1.0.3"""
print(fade.pinkred(banner1))

# Read deployer addresses from a file
with open('deployer_addresses.txt', 'r') as file:
    deployer_addresses = [line.strip() for line in file.readlines()]

if not deployer_addresses:
    print("The deployer addresses file is empty. Please provide a valid file with deployer addresses.")
    input("Press enter to exit...")
    exit()

# Define global variables
checked_deployers = set()

http_proxy = input("Enter your HTTP proxy (e.g., http://username:password@proxyserver:port): ")
check_past_deployments = input("View deployers past deployments? (true/false): ").lower() == 'true'
min_market_cap = float(input("Enter the minimum market cap for atleast one of a deployers previous coins (e.g., 25000): "))
check_token_complete = input("Filter deployers that have had atleast one token hit raydium? (true/false): ").lower() == 'true'
completed_ratio_threshold = float(input("Enter the deployers needed raydium ratio threshold (e.g., 0.5): "))

# Define global variables
checked_deployers = set()

proxy = {
    "http": http_proxy,
    "https": http_proxy,
}

def should_exclude_token(token):
    keywords = ["TEST", "DONT BUY", "RUG", "DO NOT", "SNIPER", "SNIPERS", "BOTS", "BOT"]
    name = token.get('name', '').upper()
    description = token.get('description', '').upper()
    pattern = re.compile(r'\b(?:' + '|'.join(keywords) + r')\b')
    return bool(pattern.search(name) or pattern.search(description))

def fetch_previous_tokens(deployer_address):
    url = 'https://client-api-2-74b1891ee9f9.herokuapp.com/coins'
    params = {
        'offset': 0,
        'limit': 9999,
        'sort': 'created_timestamp',
        'order': 'DESC',
        'includeNsfw': 'false',
        'creator': deployer_address
    }
    response = requests.get(url, params=params, proxies=proxy)
    if response.status_code == 200:
        tokens = response.json()
        unique_tokens = {token['mint']: token for token in tokens}.values()
        return unique_tokens
    else:
        print(f"Failed to fetch previous tokens: {response.status_code}")
        return None

def filter_deployer(deployer_address):
    global checked_deployers
    if deployer_address in checked_deployers:
        return None

    checked_deployers.add(deployer_address)
    previous_tokens = fetch_previous_tokens(deployer_address)
    
    if not previous_tokens and check_past_deployments:
        return None

    if previous_tokens:
        any_completed = False
        valid_market_cap = False
        non_farm_tokens = 0
        completed_tokens = 0
        excluded_tokens = 0
        highest_market_cap = 0
        token_details = []

        for t in previous_tokens:
            if should_exclude_token(t):
                excluded_tokens += 1
                continue  # Skip excluded tokens
            non_farm_tokens += 1
            if t.get('complete', False):
                completed_tokens += 1

            previous_market_cap = t['usd_market_cap']
            if previous_market_cap > highest_market_cap:
                highest_market_cap = previous_market_cap
            if previous_market_cap >= min_market_cap:
                valid_market_cap = True

            if t.get('complete', False):
                any_completed = True

            token_details.append({
                'name': t['name'],
                'symbol': t.get('symbol', 'N/A'),
                'market_cap': previous_market_cap,
                'completed': t.get('complete', False)
            })

        completion_ratio = completed_tokens / non_farm_tokens if non_farm_tokens > 0 else 0

        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{current_time}] Deployer {deployer_address} | Tokens: {len(previous_tokens)} | Completed: {completed_tokens} | Ratio: {completion_ratio:.2f} | Highest Market Cap: ${highest_market_cap/1000:.2f}K | Excluded Tokens: {excluded_tokens}")

        for token in token_details:
            completed_text = "Completed" if token['completed'] else "Not Completed"
            print(f"    Token: {token['name']} ({token['symbol']}), Market Cap: ${token['market_cap']/1000:.2f}K, {completed_text}")

        if check_past_deployments and not valid_market_cap:
            return None

        if check_token_complete and not any_completed:
            return None

        if completion_ratio < completed_ratio_threshold:
            return None

        return {
            'deployer_address': deployer_address,
            'num_tokens': len(previous_tokens),
            'highest_market_cap': highest_market_cap,
            'completion_ratio': completion_ratio,
            'token_details': token_details,
            'excluded_tokens': excluded_tokens
        }

    return None

def process_deployer(deployer_address):
    result = filter_deployer(deployer_address)
    if result:
        with open('filtered-deployers.txt', 'a', encoding='utf-8') as file:
            file.write(f"Deployer: {result['deployer_address']}, Tokens Created: {result['num_tokens']}, Highest Market Cap: ${result['highest_market_cap']/1000:.2f}K, Completion Ratio: {result['completion_ratio']:.2f}, Excluded Tokens: {result['excluded_tokens']}\n")
            for token in result['token_details']:
                completed_text = "Completed" if token['completed'] else "Not Completed"
                file.write(f"    Token: {token['name']} ({token['symbol']}), Market Cap: ${token['market_cap']/1000:.2f}K, {completed_text}\n")

        with open('filtered_deployers_clean.txt', 'a', encoding='utf-8') as clean_file:
            clean_file.write(f"{result['deployer_address']}\n")

        print(f"\nDeployer: {result['deployer_address']}, Tokens Created: {result['num_tokens']}, Highest Market Cap: ${result['highest_market_cap']/1000:.2f}K, Completion Ratio: {result['completion_ratio']:.2f}, Excluded Tokens: {result['excluded_tokens']}")
        for token in result['token_details']:
            completed_text = "Completed" if token['completed'] else "Not Completed"
            print(f"    Token: {token['name']} ({token['symbol']}), Market Cap: ${token['market_cap']/1000:.2f}K, {completed_text}")

# Initialize the files
with open('filtered-deployers.txt', 'w', encoding='utf-8') as file:
    file.write('')
with open('filtered_deployers_clean.txt', 'w', encoding='utf-8') as clean_file:
    clean_file.write('')

# Use ThreadPoolExecutor to process deployer addresses concurrently
with ThreadPoolExecutor(max_workers=10) as executor:
    future_to_address = {executor.submit(process_deployer, address): address for address in deployer_addresses}
    for future in as_completed(future_to_address):
        deployer_address = future_to_address[future]
        try:
            future.result()  # We don't need to store result here as it is already handled in process_deployer
        except Exception as e:
            print(f"[red]Error processing {deployer_address}: {e}[/red]")

print("\nFiltered deployers have been saved to filtered-deployers.txt and filtered_deployers_clean.txt")
