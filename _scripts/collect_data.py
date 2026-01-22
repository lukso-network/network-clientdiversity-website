import re
from typing import Sequence
import requests
import os
import math
import time
import json
import pprint
from datetime import datetime, timezone
from rlp.codec import decode
from web3 import Web3 
import rlp

current_time = round(time.time()) # seconds
date = datetime.now(timezone.utc).strftime('%Y-%m-%d') # yyyy-mm-dd
print(f"Epoch: {current_time}")
print(f"Date: {date}")

pp = pprint.PrettyPrinter(indent=4)
use_test_data = False
print_fetch_data = False
print_processed_data = True
pretty_print = True
exit_on_fetch_error = True
exit_on_save_error = True
exit_on_report_error = False

google_form_error_report_url = os.environ.get("")

node_ip = os.environ.get("RPC_NODE_IP") or '0.0.0.0'

# URLS
blockprint_api_addr = os.environ.get("BLOCKPRINT_API_BASE_URL") or f'http://{node_ip}:8000'
node_crawler_api_addr = os.environ.get("NODE_CRAWLER_API_BASE_URL") or f'http://{node_ip}:10000'
node_rpc_addr = os.environ.get("EXTRA_DATA_NODE_URL") or f'http://{node_ip}:8545'

# enter values for local testing
# rated_token = ""
# google_form_error_report_url = ""


def fetch_json(url, method="GET", payload={}, headers={}, retries=2):
  print(f"Fetch: {url}")
  response = {"status": 0, "attempts": 0, "data": None}
  try: 
    while response["attempts"] <= retries and (response["status"] != 200 or response["data"] == None):
      rate_limited_domains = ["rated.network"]
      rate_limited = any(domain in url for domain in rate_limited_domains)
      if (rate_limited or response["attempts"] > 0):
        time.sleep(1.05)
      response["attempts"] = response["attempts"] + 1
      r = requests.request(method, url, headers=headers, data=payload)
      response = {"status": r.status_code, "attempts": response["attempts"], "data": r.json()}
  except:
    error = f"Fetch failed: {url}"
    report_error(error)
    if exit_on_fetch_error:
      raise SystemExit(error)
    else:
      print(error)
  finally:
    print_data("fetch", response, label=None)
    return response

def save_to_file(rel_path, data):
  if not rel_path.startswith("/"):
    rel_path = "/" + rel_path
    abs_path = os.path.dirname(__file__) + rel_path
  # skip file save if using test data
  todays_data =  {
    "date":date,
    "timestamp":current_time,
    "data":data
  }
  # check if file exists yet
  if os.path.isfile(abs_path):
    try:
      with open(abs_path, 'r') as f:
        all_data = json.load(f)
        # check if there's already data for today
        if date != all_data[-1]['date'] and all_data[-1]['data'] != None:
          # append todays data to historical data and write to file
          all_data.append(todays_data)
          with open(abs_path, 'w') as f:
            json.dump(all_data, f, indent=None, separators=(',', ':'))
          f.close()
          print(f"{rel_path} data has been updated")
        # if the data was null then overwrite it
        elif date == all_data[-1]['date'] and all_data[-1]['data'] == None:
          del all_data[-1]
          # append todays data to historical data and write to file
          all_data.append(todays_data)
          with open(abs_path, 'w') as f:
            json.dump(all_data, f, indent=None, separators=(',', ':'))
          f.close()
          print(f"{rel_path} data has been updated")
        else:
          print(f"{rel_path} data for the current date was already recorded")
    except:
      # file is empty or malformed data
      error = f"ERROR: {rel_path} file read error"
      report_error(error)
      if exit_on_save_error:
        raise SystemExit(error)
      else:
        print(error)
  else:
    # create new file with today's data
    all_data = []
    all_data.append(todays_data)
    with open(abs_path, 'w') as f:
      json.dump(all_data, f, indent=None, separators=(',', ':'))
    f.close()
    print(f"{rel_path} data has been updated")

def report_error(error, context=""):
  data = {
    # "entry.2112281434": "name",    # text
    # "entry.1600556346": "option3", # dropdown
    # "entry.819260047": ["option2", "option3"], #checkbox multiple
    # "entry.1682233942": "option5"  # checkbox single
    "entry.76518486": error,
    "entry.943255668": context
  }
  try:
    requests.post(google_form_error_report_url, data)
    print("Error submitted")
  except:
    error = f"ERROR: {path} file read error"
    if exit_on_report_error:
      raise SystemExit(error)
    else:
      print(error)


def print_file(rel_path):
  # add leading / to relative path if not present
  if not rel_path.startswith("/"):
    rel_path = "/" + rel_path
  abs_path = os.path.dirname(__file__) + rel_path
  if os.path.isfile(abs_path):
    with open(abs_path, 'r') as f:
      contents = json.load(f)
      if pretty_print:
        pprint(contents)
      else:
        print(contents)
  else:
    print("not file")

def print_data(context, data, label=None):
  if context == "fetch" and print_fetch_data:
    if label:
      print(f"{label}:")
    if pretty_print:
      pp.pprint(data)
    else:
      print(data)
  if context == "processed" and print_processed_data:
    if label:
      print(f"{label}:")
    if pretty_print:
      pp.pprint(data)
    else:
      print(data)

def pprint(data):
  pp.pprint(data)


def get_blockprint_marketshare_data():  
  initial_timestamp = 1684856400
  initial_epoch = 0
  delta_timestamp = current_time - initial_timestamp # seconds
  current_epoch = math.floor(delta_timestamp / 384)

  # the Blockprint API caches results so fetching data based on an "epoch day" so 
  # everyone that loads the page on an "epoch day" will use the cached results and 
  # their backend doesn't get overloaded
  # Michael Sproul recommends using a 2-week period
  end_epoch = math.floor(current_epoch / 225) * 225
  start_epoch = end_epoch - 3150
  url = f"{blockprint_api_addr}/blocks_per_client/{start_epoch}/{end_epoch}"
  response = fetch_json(url)
  return response


def process_blockprint_marketshare_data(raw_marketshare_data):
  # example blockprint raw data:
  # raw_marketshare_data = {'status': 200, 'attempts': 1, 'data': {
  #   'Uncertain': 0, 
  #   'Grandine': 0, 
  #   'Lighthouse': 33411, 
  #   'Lodestar': 1145, 
  #   'Nimbus': 4862, 
  #   'Other': 0, 
  #   'Prysm': 45450, 
  #   'Teku': 15458
  #   }}

  main_clients = ["lighthouse", "nimbus", "teku", "prysm", "lodestar", "erigon", "grandine"]
  threshold_percentage = 0.5 # represented as a percent, not a decimal
  sample_size = 0
  reformatted_data = []
  filtered_data = [{"name": "other", "value": 0}]
  marketshare_data = []
  extra_data = {}
  final_data = {}

  # reformat data into a list of dicts
  for key, value in raw_marketshare_data["data"].items():
    reformatted_data.append({"name": key.lower(), "value": value})
    sample_size += value
  # pprint(["reformatted_data", reformatted_data])
  # pprint(["sample_size", sample_size])

  pprint(reformatted_data)
  # filter out items either under the threshold and not in the main_clients list
  for item in reformatted_data:
    if item["name"] in main_clients:
      filtered_data.append({"name": item["name"], "value": item["value"]})
    elif (item["value"] / sample_size * 100) >= threshold_percentage:
      filtered_data.append({"name": item["name"], "value": item["value"]})
    else:
      filtered_data[0]["value"] += item["value"]
  # pprint(["filtered_data", filtered_data])

  # calculate the marketshare for each client
  for item in filtered_data:
    marketshare = item["value"] / sample_size
    marketshare_data.append({"name": item["name"], "value": marketshare, "accuracy": "no data"})
  # pprint(["marketshare_data", marketshare_data])

  # sort the list by marketshare descending
  sorted_data = sorted(marketshare_data, key=lambda k : k['value'], reverse=True)
  # pprint(["sorted_data", sorted_data])

  # supplemental data
  extra_data["data_source"] = "blockprint"
  extra_data["has_majority"] = False
  extra_data["has_supermajority"] = False
  extra_data["danger_client"] = ""
  if sorted_data[0]["value"] >= .50:
    extra_data["has_majority"] = True
    extra_data["danger_client"] = sorted_data[0]["name"]
  if sorted_data[0]["value"] >= .66:
    extra_data["has_supermajority"] = True
  extra_data["top_client"] = sorted_data[0]["name"]
  # pprint(["extra_data", extra_data])

  # create final data dict
  final_data["distribution"] = sorted_data
  # final_data["accuracy"] = processed_accuracy_data
  final_data["other"] = extra_data
  print_data("processed", final_data, "final_data_blockprint")

  return final_data


def blockprint_marketshare():
  raw_marketshare_data = get_blockprint_marketshare_data()
  save_to_file("../_data/raw/blockprint_raw.json", raw_marketshare_data)
  processed_marketshare_data = process_blockprint_marketshare_data(raw_marketshare_data)
  save_to_file("../_data/blockprint.json", processed_marketshare_data)


########################################


def get_node_crawler_marketshare_data():
  url = f'{node_crawler_api_addr}/v1/dashboard?filter=[["name:geth"],["name:erigon"],["name:nethermind"],["name:besu"]]'
  response = fetch_json(url)
  pprint(response)
  return response


def process_node_crawler_marketshare_data(raw_data):
  # {
  #   "clients": [
  #     {
  #       "name": "geth",
  #       "count": 32
  #     },
  #     {
  #       "name": "erigon",
  #       "count": 2
  #     },
  #   ],
  # } 

  main_clients = ["geth", "erigon", "nethermind", "besu", "reth"]
  threshold_percentage = 0.5 # represented as a percent, not a decimal
  sample_size = 0
  reformatted_data = []
  filtered_data = [{"name": "other", "value": 0}]
  marketshare_data = []
  extra_data = {}
  final_data = {}

  pprint(raw_data)
  # reformat data into a list of dicts
  for item in raw_data["data"]["clients"]:
    pprint(item)
    reformatted_data.append({"name": item["name"].lower(), "value": item["count"]})
    sample_size += item["count"]
  # pprint(["reformatted_data", reformatted_data])
  # pprint(["sample_size", sample_size])

  # filter out items either under the threshold and not in the main_clients list
  for item in reformatted_data:
    if item["name"] in main_clients:
      filtered_data.append({"name": item["name"], "value": item["value"]})
    elif (item["value"] / sample_size * 100) >= threshold_percentage:
      filtered_data.append({"name": item["name"], "value": item["value"]})
    else:
      filtered_data[0]["value"] += item["value"]
  # pprint(["filtered_data", filtered_data])

  # calculate the marketshare for each client
  for item in filtered_data:
    marketshare = item["value"] / sample_size
    marketshare_data.append({"name": item["name"], "value": marketshare, "accuracy": "no data"})
  # pprint(["marketshare_data", marketshare_data])

  # sort the list by marketshare descending
  sorted_data = sorted(marketshare_data, key=lambda k : k['value'], reverse=True)
  # pprint(["sorted_data", sorted_data])

  # supplemental data
  extra_data["data_source"] = "node_crawler"
  extra_data["has_majority"] = False
  extra_data["has_supermajority"] = False
  extra_data["danger_client"] = ""
  if sorted_data[0]["value"] >= .50:
    extra_data["has_majority"] = True
    extra_data["danger_client"] = sorted_data[0]["name"]
  if sorted_data[0]["value"] >= .66:
    extra_data["has_supermajority"] = True
  extra_data["top_client"] = sorted_data[0]["name"]
  # pprint(["extra_data", extra_data])

  # create final data dict
  final_data["distribution"] = sorted_data
  final_data["other"] = extra_data
  print_data("processed", final_data, "final_data_node_crawler")

  return final_data


def node_crawler_marketshare():
  raw_data = get_node_crawler_marketshare_data()
  save_to_file("../_data/raw/node_crawler_raw.json", raw_data)
  processed_data = process_node_crawler_marketshare_data(raw_data)
  save_to_file("../_data/node_crawler.json", processed_data)


########################################


def get_extra_data_marketshare_data():
  w3 = Web3(Web3.HTTPProvider(node_rpc_addr))
  head = w3.eth.get_block_number()
  block_range = 60 * 60 * 2 * 7 # a week range of blocks (2 == 24 hours / 12 seconds-per-block)

  results = [];
  
  for i in range(head - block_range, head):
    block = w3.eth.get_block(i)
    extra_data = block.get('extraData')
    if extra_data is None:
      continue
    else:
      try:
        decoded = rlp.decode(extra_data)
        decoded_str = '';
        for sect in decoded:
          decoded_str += re.sub('^[\x00-\x1f]+', '', sect.decode()) + '/'

        results.append(decoded_str.lower())

      except:
        decoded = extra_data.decode()
        results.append(decoded.lower())

  return results


def process_extra_data_marketshare_data(raw_data: Sequence[str]):
  # [ '...geth...', '...besu...', '...nethermind...' ] etc.

  main_clients = ["geth", "erigon", "nethermind", "besu", "reth"]
  threshold_percentage = 0.5 # represented as a percent, not a decimal
  sample_size = 0
  reformatted_data = dict.fromkeys(main_clients, 0)

  filtered_data = [{"name": "other", "value": 0}]
  marketshare_data = []
  extra_data = {}
  final_data = {}

  pprint(raw_data)
  # reformat data into a list of dicts
  for item in raw_data:
    for client in main_clients:
      if item.find(client) >= 0:
        reformatted_data[client] += 1
        sample_size += 1 

  # filter out items either under the threshold and not in the main_clients list
  for client, count in reformatted_data.items():
    if client in main_clients:
      filtered_data.append({"name": client, "value": count})
    elif (count / sample_size * 100) >= threshold_percentage:
      filtered_data.append({"name": client, "value": count})
    else:
      filtered_data[0]["value"] += count
  # pprint(["filtered_data", filtered_data])

  # calculate the marketshare for each client
  for item in filtered_data:
    marketshare = item["value"] / sample_size
    marketshare_data.append({"name": item["name"], "value": marketshare, "accuracy": "no data"})
  # pprint(["marketshare_data", marketshare_data])

  # sort the list by marketshare descending
  sorted_data = sorted(marketshare_data, key=lambda k : k['value'], reverse=True)
  # pprint(["sorted_data", sorted_data])

  # supplemental data
  extra_data["data_source"] = "node_crawler"
  extra_data["has_majority"] = False
  extra_data["has_supermajority"] = False
  extra_data["danger_client"] = ""
  if sorted_data[0]["value"] >= .50:
    extra_data["has_majority"] = True
    extra_data["danger_client"] = sorted_data[0]["name"]
  if sorted_data[0]["value"] >= .66:
    extra_data["has_supermajority"] = True
  extra_data["top_client"] = sorted_data[0]["name"]
  # pprint(["extra_data", extra_data])

  # create final data dict
  final_data["distribution"] = sorted_data
  final_data["other"] = extra_data
  print_data("processed", final_data, "final_data_node_crawler")

  return final_data


def extra_data_marketshare():
  raw_data = get_extra_data_marketshare_data()
  save_to_file("../_data/raw/extra_data_raw.json", raw_data)
  processed_data = process_extra_data_marketshare_data(raw_data)
  save_to_file("../_data/extra_data.json", processed_data)


def get_data():
  # node_crawler_marketshare()
  extra_data_marketshare()
  # blockprint_marketshare()


get_data()

