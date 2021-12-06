from datetime import datetime
import re
import contract_scraper as scraper
import csv
import os
from time import sleep


def compile_date(unix_timestamp):
    filepath = os.path.realpath(os.getcwd())
    date = datetime.fromtimestamp(int(unix_timestamp)).isoformat()
    format_time = re.findall("(.*)T", date)

    cake_price = scraper.get_cake_price(unix_timestamp)
    wbnb_price = scraper.get_wbnb_price(unix_timestamp)
    monsta_price = scraper.get_monsta_price(unix_timestamp)
    circ_supply = scraper.get_monsta_supply(unix_timestamp)
    burned = scraper.total_burned(unix_timestamp)
    vault = scraper.get_vault_reserves(unix_timestamp)
    liquidity = scraper.get_liquidity(unix_timestamp)
    trade_volume = scraper.get_trade_volume(unix_timestamp)

    try:
        open(filepath + "\\stats.csv")
        write_headers = False
    except:
        write_headers = True

    csv_write = open(filepath + "\\stats.csv", 'a', newline='')
    csv_read = open(filepath + "\\stats.csv", newline='')
    writer = csv.writer(csv_write)
    reader = csv.reader(csv_read)

    already_added = []
    stats = []
    headers = ['date', 'monsta usd', 'monsta bnb', 'cake price', 'bnb price', 'circ. supply', 'burned tokens',
               'burned %', 'vault syrup bars', 'vault usd', 'vault bnb', 'liquidity usd',
               'liquidity bnb', 'trades', 'trade volume usd', 'trade volume bnb']

    for row in reader:
        already_added.append(row)
        sleep(0.5)

    already_added = [item for sublist in already_added for item in sublist]

    stats.append(format_time[0])
    stats.append(monsta_price[1])
    stats.append(monsta_price[3])
    stats.append(cake_price['usdPrice'])
    stats.append(wbnb_price['usdPrice'])
    stats.append(circ_supply)
    stats.append(burned[1])
    stats.append(burned[3])
    stats.append(vault[1])
    stats.append(vault[3])
    stats.append(vault[5])
    stats.append(liquidity[3])
    stats.append(liquidity[1])
    try:
        stats.append(trade_volume[1])
        stats.append(trade_volume[3])
        stats.append(trade_volume[5])
    except:
        stats.append(0)
        stats.append(0)
        stats.append(0)

    if write_headers:
        writer.writerow(headers)

    if stats[0] in already_added:
        print("already in CSV")
        pass
    else:
        writer.writerow(stats)


compile_date(1638666000)
#from_timestamp = 1636419600
#to_timestamp = 1636506000

#while from_timestamp < to_timestamp:
#    print(datetime.fromtimestamp(int(from_timestamp)).isoformat())
#    compile_date(from_timestamp)
#    from_timestamp += 86400