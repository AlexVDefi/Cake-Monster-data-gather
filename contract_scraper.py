from web3 import Web3
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import json
import os
import requests
import csv
import re
from time import sleep


filepath = os.path.realpath(os.getcwd())
configFile = filepath + "\\config.json"
pcsABI = filepath + "\\psc_abi.json"
balanceABI = filepath + "\\balance_abi.json"
monstaV9ABI = filepath + "\\monsta_v9_abi.json"

with open(configFile) as f:
    config = json.load(f)
with open(pcsABI) as f:
    pcs_abi = json.load(f)
with open(balanceABI) as f:
    balance_abi = json.load(f)
with open(monstaV9ABI) as f:
    monsta_v9_abi = json.load(f)

monsta_vault_address = Web3.toChecksumAddress("0xc941fd84c8a466a6f51a6cac717cbd10871819c8")
monsta_token_address = Web3.toChecksumAddress("0x8a5d7fcd4c90421d21d30fcc4435948ac3618b2f")
syrupbar_address = Web3.toChecksumAddress("0x009cf7bc57584b7998236eff51b98a168dcea9b0")
cake_token_address = Web3.toChecksumAddress("0x0e09fabb73bd3ade0a17ecc321fd13a19e81ce82")
wbnb_token_address = Web3.toChecksumAddress("0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c")
monsta_lp_address = Web3.toChecksumAddress("0x55c49d1cd54126c69f22c2e9eebd1efef5e620fa")
dead_address = Web3.toChecksumAddress("0x0000000000000000000000000000000000000000")
pcs_router_address = Web3.toChecksumAddress("0x10ed43c718714eb63d5aa57b78b54704e256024e")

address_list = ["0xc941fd84c8a466a6f51a6cac717cbd10871819c8",
                "0x8a5d7fcd4c90421d21d30fcc4435948ac3618b2f",
                "0x009cf7bc57584b7998236eff51b98a168dcea9b0",
                "0x55c49d1cd54126c69f22c2e9eebd1efef5e620fa",
                "0x0000000000000000000000000000000000000000",
                "0x10ed43c718714eb63d5aa57b78b54704e256024e"]

rpc_url = "https://speedy-nodes-nyc.moralis.io/98c4d8801bec63c6fe7a2827/bsc/mainnet/archive"

for line in config:
    graphql_api = line['graphql_api']
    moralis_api = line['moralis_api']
    bscscan_api = line['bscscan_api']

w3 = Web3(Web3.HTTPProvider(rpc_url))


def update_holders(unix_timestamp):
    sleep(0.5)
    fromblock = get_block_at_timestamp(unix_timestamp)
    toblock = fromblock + 1000

    to_addresses = []
    from_addresses = []
    holder_list = []
    already_added = []

    query = ('https://deep-index.moralis.io/api/v2/' + monsta_lp_address + '/erc20/transfers?chain=bsc&from_block='
             + str(fromblock) + '&to_block=' + str(toblock))

    headers = {
        'x-api-key': moralis_api
    }

    query = requests.request("GET", query, headers=headers)

    response = query.json()

    for i in response["result"]:
        if i['to_address'] not in address_list and i['to_address'] not in to_addresses:
            to_addresses.append(i['to_address'])
        if i['from_address'] not in address_list and i['from_address'] not in from_addresses:
            from_addresses.append(i['from_address'])

    for to_addy in to_addresses:
        holder_list.append(to_addy)

    for from_addy in from_addresses:
        if from_addy not in holder_list:
            holder_list.append(from_addy)

    csv_write = open(filepath + "\\addresses.csv", 'a', newline='')
    csv_read = open(filepath + "\\addresses.csv", newline='')
    writer = csv.writer(csv_write)
    reader = csv.reader(csv_read)

    for row in reader:
        already_added.append(row)

    already_added = [item for sublist in already_added for item in sublist]

    for address in holder_list:
        if address not in already_added:
            writer.writerow([address])


def get_monsta_holders(unix_timestamp):
    sleep(0.5)
    holder_list = []
    hold_count = 0

    fromblock = get_block_at_timestamp(unix_timestamp)

    csv_read = open(filepath + "\\addresses.csv", newline='')
    reader = csv.reader(csv_read)

    with ThreadPoolExecutor(max_workers=9) as executor:
        for row in reader:
            holders = executor.submit(process_holder_line, row, fromblock)
            holder_list.append(holders)

        for holder in holder_list:
            if holder.result(timeout=60) == "Hold":
                hold_count += 1

    return hold_count


def process_holder_line(address_list, fromblock):
    sleep(0.5)
    balance_check_contract = w3.eth.contract(
        address=monsta_token_address, abi=balance_abi)

    for address in address_list:
        balance_at_timestamp = balance_check_contract.functions.balanceOf(Web3.toChecksumAddress(address)).call(
            {'from': monsta_token_address}, block_identifier=fromblock)
        if balance_at_timestamp != 0:
            print("Holding: "+str(address))
            return "Hold"
        elif balance_at_timestamp == 0:
            print("Not Holding: " + str(address))
            return "Not holding"


def get_monsta_price(unix_timestamp):
    sleep(0.5)
    block = get_block_at_timestamp(unix_timestamp)

    price_now = 'https://deep-index.moralis.io/api/v2/erc20/' + monsta_token_address + '/price?chain=bsc'
    price_at_timestamp = 'https://deep-index.moralis.io/api/v2/erc20/' + monsta_token_address + '/price?chain=bsc&to_block=' + str(block)

    headers = {
        'x-api-key': moralis_api
    }

    price_now = requests.request("GET", price_now, headers=headers)
    price_at_timestamp = requests.request("GET", price_at_timestamp, headers=headers)

    price_at_timestamp = price_at_timestamp.json()
    price_now = price_now.json()

    monsta_in_BNB = price_at_timestamp['nativePrice']
    monsta_in_BNB = monsta_in_BNB['value']
    monsta_in_BNB = w3.fromWei(int(monsta_in_BNB), "ether")
    monsta_in_BNB = "{:0.10f}".format(monsta_in_BNB)

    return "USD", price_at_timestamp['usdPrice'], "BNB", monsta_in_BNB


def get_cake_price(unix_timestamp):
    sleep(0.5)
    block = get_block_at_timestamp(unix_timestamp)

    price_now = 'https://deep-index.moralis.io/api/v2/erc20/' + cake_token_address + '/price?chain=bsc'
    price_at_timestamp = 'https://deep-index.moralis.io/api/v2/erc20/' + cake_token_address + '/price?chain=bsc&to_block=' + str(block)

    headers = {
        'x-api-key': moralis_api
    }

    price_now = requests.request("GET", price_now, headers=headers)
    price_at_timestamp = requests.request("GET", price_at_timestamp, headers=headers)

    price_at_timestamp = price_at_timestamp.json()
    price_now = price_now.json()

    return price_at_timestamp


def get_wbnb_price(unix_timestamp):
    sleep(0.5)
    block = get_block_at_timestamp(unix_timestamp)

    price_now = 'https://deep-index.moralis.io/api/v2/erc20/' + wbnb_token_address + '/price?chain=bsc'
    price_at_timestamp = 'https://deep-index.moralis.io/api/v2/erc20/' + wbnb_token_address + '/price?chain=bsc&to_block=' + str(block)

    headers = {
        'x-api-key': moralis_api
    }

    price_now = requests.request("GET", price_now, headers=headers)
    price_at_timestamp = requests.request("GET", price_at_timestamp, headers=headers)

    price_at_timestamp = price_at_timestamp.json()
    price_now = price_now.json()

    return price_at_timestamp


def get_monsta_supply(unix_timestamp):
    sleep(0.5)
    contract = w3.eth.contract(address=monsta_token_address, abi=monsta_v9_abi)

    block = get_block_at_timestamp(unix_timestamp)

    supply_now = contract.functions.totalSupply().call()
    supply_at_timestamp = contract.functions.totalSupply().call(block_identifier=block)

    supply_now = w3.fromWei(supply_now, "ether")
    supply_at_timestamp = w3.fromWei(supply_at_timestamp, "ether")
    supply_at_timestamp = "{:0.2f}".format(supply_at_timestamp)

    return supply_at_timestamp


def total_burned(unix_timestamp):
    sleep(0.5)
    initial_supply = 10000000000

    supply_at_timestamp = get_monsta_supply(unix_timestamp)

    burned = float(initial_supply) - float(supply_at_timestamp)
    burned_pct = float(burned) / float(initial_supply) * 100
    burned_pct = "{:0.2f}".format(burned_pct)

    return "Tokens", burned, "Pct %", burned_pct


def get_vault_reserves(unix_timestamp):
    sleep(0.5)
    balance_check_contract = w3.eth.contract(
        address=syrupbar_address, abi=balance_abi)

    block = get_block_at_timestamp(unix_timestamp)

    balance_now = balance_check_contract.functions.balanceOf(monsta_vault_address).call({'from': syrupbar_address})
    balance_at_timestamp = balance_check_contract.functions.balanceOf(monsta_vault_address).call({'from': syrupbar_address}, block_identifier=block)

    balance_now = w3.fromWei(balance_now, "ether")
    balance_at_timestamp = w3.fromWei(balance_at_timestamp, "ether")

    balance_at_timestamp = "{:0.2f}".format(balance_at_timestamp)

    cake_price = get_cake_price(unix_timestamp)

    cake_in_BNB = cake_price['nativePrice']
    cake_in_BNB = cake_in_BNB['value']
    cake_in_BNB = w3.fromWei(int(cake_in_BNB), "ether")

    reserves_in_BNB = float(balance_at_timestamp) * float(cake_in_BNB)

    reserves_in_USD = float(balance_at_timestamp) * float(cake_price['usdPrice'])

    return "Syrup bars", balance_at_timestamp, "In USD", reserves_in_USD, "In BNB", reserves_in_BNB


def get_liquidity(unix_timestamp):
    sleep(0.5)
    balance_check_contract = w3.eth.contract(
        address=wbnb_token_address, abi=balance_abi)

    block = get_block_at_timestamp(unix_timestamp)

    balance_now = balance_check_contract.functions.balanceOf(monsta_lp_address).call({'from': wbnb_token_address})
    balance_at_timestamp = balance_check_contract.functions.balanceOf(monsta_lp_address).call(
        {'from': wbnb_token_address}, block_identifier=block)

    liquidity = w3.fromWei(balance_at_timestamp, "ether")
    liquidity = "{:0.2f}".format(liquidity)

    wbnb_price = get_wbnb_price(unix_timestamp)

    liquidity_in_USD = float(liquidity) * float(wbnb_price['usdPrice'])

    return "BNB", float(liquidity), "In USD", liquidity_in_USD


def get_trade_volume(unix_timestamp):
    sleep(0.5)
    date = datetime.fromtimestamp(int(unix_timestamp)).isoformat()
    format_time = re.findall("(.*)T", date)
    wbnb_price = get_wbnb_price(unix_timestamp)

    query = """
        query{
            ethereum(network: bsc) {
                dexTrades(
                    options: {limit: 24, desc: "timeInterval.hour"}
                    date: {since: """+'"'+format_time[0]+'"'+""", till: """+'"'+format_time[0]+'"'+"""}
                    exchangeName: {is: "Pancake v2"}
                    baseCurrency: {is: "0x8a5d7fcd4c90421d21d30fcc4435948ac3618b2f"}
                    ) {
                    count
                    tradeAmount(in: USD)
                    timeInterval {
                        hour(count: 24)
                        }
                    }
                }
            }
        """
    headers = {'X-API-KEY': graphql_api}
    request = requests.post('https://graphql.bitquery.io/',
                            json={'query': query}, headers=headers)

    trade_data = request.json()
    data = trade_data['data']['ethereum']['dexTrades']
    for trade in data:
        usd_volume = trade['tradeAmount']
        bnb_volume = float(usd_volume) / float(wbnb_price['usdPrice'])
        return "Trades", trade['count'], "In USD", usd_volume, "In BNB", bnb_volume


def get_block_at_timestamp(unix_timestamp):
    sleep(0.5)
    block = requests.get("https://api.bscscan.com/api?module=block&action=getblocknobytime&timestamp="
                         +str(unix_timestamp)+"&closest=before&apikey="+bscscan_api)
    block = json.loads(block.content)
    block = block["result"]
    return int(block)