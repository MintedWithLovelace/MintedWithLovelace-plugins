import json
import random
from datetime import datetime
from getopt import getopt
from os import mkdir
from os.path import isfile, join as osjoin
from requests import get as rget
from sys import exit, argv
from time import sleep


BF_BATCH_LIMIT = 100  # Default is 100
BF_ORDER = 'asc'  # Default is 'asc' - opt: 'desc'
ADDR_WHITELIST = [
    'addr_here'
]
CACHE_NAME = 'rafflecache'
TRACK_LOG = 'processed.log'


# Custom plugin-specific settings
def do_settings(campaign_name, campaign_root):
    # BEGIN Cusomize Static Setting or Prompt for Input
    cache_folder_name = CACHE_NAME
    # END custom
    cache_dir = osjoin(osjoin(osjoin(campaign_root, 'plugin'), cache_folder_name), '')
    try:
        mkdir(cache_dir)
    except OSError:
        pass
    return [
        'Enter Blockfrost ID on Mainnet:',
        'Enter Blockfrost ID on Testnet:',
        'Enter Filter-by-Asset on Mainnet:',
        'Enter Filter-by-Asset on Testnet:'
    ]


# Customize plugin code
def do_plugin(settings, is_test, payer_hash, payer_addr, payer_ada, payer_return_ada, payer_asset_string, policy_id, tx_meta_json, mint_qty_int):
    campaign_path = settings[0]
    bf_id_main = settings[2]
    bf_id_test = settings[3]
    asset_main = settings[4]
    asset_test = settings[5]
    err_catch = False
    nettype = 'mainnet'
    if is_test is True:
        nettype = 'preprod'
    campaign_path = osjoin(osjoin(campaign_path, nettype), '')
    cache_dir = osjoin(osjoin(osjoin(campaign_path, 'plugin'), CACHE_NAME), '')
    track_log = cache_dir + TRACK_LOG
    is_file = isfile(track_log)
    if not is_file:
        try:
            open(track_log, 'x')
        except OSError:
            pass

    def get_shuffled_time(seed, shuffle=True):
        time_now = int(str(datetime.now().time()).replace(':', '').replace('.', ''))
        if shuffle is False:
            return str(time_now)
        random.seed(time_now)
        time_now = list(str(time_now))
        random.shuffle(time_now)
        shuf_time = ''
        for L in time_now:
            shuf_time += L
        return shuf_time

    def blockfrost(bf_id, lookup_item, nettype, get_page=1):
        retry_limit = 100
        is_error = False
        while True:
            retry_limit -= 1
            if retry_limit == 0:
                is_error = True
                break
            headers = {'project_id': bf_id}
            if 'addr' in lookup_item:
                cmd = 'https://cardano-' + nettype + '.blockfrost.io/api/v0/addresses/' + lookup_item + '?order=desc'
            else:
                cmd = 'https://cardano-' + nettype + '.blockfrost.io/api/v0/assets/' + lookup_item + '/addresses?count=' + str(BF_BATCH_LIMIT) + '&order=' + BF_ORDER
                if get_page > 1:
                    cmd = cmd + '&page=' + str(get_page)
            api_pass = True
            try:
                tx_result = rget(cmd, headers=headers)
            except Exception:
                api_pass = False
            if api_pass is True:
                if 'status_code' not in tx_result.json():
                    break
            sleep(90)
        if is_error is True:
            return 'error'
        else:
            return tx_result
    mint_at_addr = ''
    tx_meta_json = ''
    mint_qty_int = 1
    get_page = 1
    addrs_owned = []
    cond_own_list = []
    total_assets = 0
    total_return_count = 0
    address_per_asset = []
    while True:
        bf_id = bf_id_main
        filter_asset = asset_main
        if is_test is True:
            bf_id = bf_id_test
            filter_asset = asset_test
        asset_data_list = list(blockfrost(bf_id, filter_asset, nettype, get_page).json())
        batch_return_count = 0
        for asset_item in asset_data_list:
            total_return_count += 1
            batch_return_count += 1
            address_per_asset += [asset_item]
        if batch_return_count < BF_BATCH_LIMIT:
            break
        else:
            get_page += 1

    # For each asset found add to list
    for addr in address_per_asset:
        if addr['address'] in ADDR_WHITELIST:
            addrs_owned += [[addr['address'], int(addr['quantity'])]]
    for cond_line in addrs_owned:
        proc_addr = False
        cond_addr = cond_line[0]
        cond_stake = cond_addr
        if len(cond_addr.strip()) == 103:
            cond_stake = cond_addr.strip()[52:-6]
        cond_qty = int(cond_line[1])
        addr_count = 0
        for addr_line in addrs_owned:
            addr_stake = addr_line[0]
            if len(addr_line[0].strip()) == 103:
                addr_stake = addr_line[0].strip()[52:-6]
            if cond_stake == addr_stake:
                proc_addr = True
                if addr_count > 0:
                    cond_qty += addr_line[1]
        if proc_addr is True:
            cond_own_list += [[cond_addr, int(cond_qty)]]
            total_assets += int(cond_qty)
    raffle_pot = []
    for holder in cond_own_list:
        held_calc = holder[1]
        while int(held_calc) > 0:
            raffle_pot += [holder[0]]
            held_calc -= 1
    random.shuffle(raffle_pot)
    find_winner = True
    while find_winner:
        mint_at_addr = random.choice(raffle_pot)
        if len(mint_at_addr) != 0 and 'addr' in mint_at_addr:
            with open(track_log, 'r') as read_track:
                tracker = read_track.readlines()
                read_track.close()
            mint_at_stake = mint_at_addr
            if len(mint_at_stake.strip()) == 103:
                mint_at_stake = mint_at_stake.strip()[52:-6]
            find_winner = False
            for mint_line in tracker:
                mint_line_stake = mint_line
                if len(mint_line_stake.strip()) == 103:
                    mint_line_stake = mint_line_stake.strip()[52:-6]
                if mint_at_stake == mint_line_stake:
                    find_winner = True
                    break
        if find_winner is False:
            break
    with open(track_log, 'a') as tracker:
        tracker.write(mint_at_addr + '\n')
        tracker.close()
    return err_catch, 'mint', mint_at_addr, tx_meta_json, mint_qty_int, 0, 0


# DO NOT MODIFY BELOW
if __name__ == "__main__":
    # Get user options
    arguments = argv[1:]
    shortopts = "sd"
    longopts = ["setup=", "data="]

    # Setting behaviour for options
    s_data = ''
    input_setup = ''
    input_data = ''
    options, args = getopt(arguments, shortopts, longopts)
    for opt, val in options:
        if opt in ("-s", "--setup"):
            input_setup = str(val)
        elif opt in ("-d", "--data"):
            input_data = str(val)

    if len(input_setup) > 0:
        input_setup = json.loads(input_setup)
        settings = do_settings(input_setup['campaign_name'], input_setup['campaign_root'])
        return_data = {"err": False, "data": settings}

    if len(input_data) > 0:
        input_data = json.loads(input_data)

        # Data in:
        settings = input_data['settings']
        is_test = input_data['is_test']
        payer_hash = input_data['payer_hash']
        payer_addr = input_data['payer_addr']
        payer_ada = input_data['payer_ada']
        payer_return_ada = input_data['ada_to_return']
        payer_asset_string = input_data['payer_asset_string']
        policy_id = input_data['policy_id']

        # Data in & can return:
        tx_meta_json = input_data['payer_txmeta']
        mint_qty_int = input_data['qty_to_mint']

        # Process main plugin function
        return_err, action, return_mint_at_addr, return_txmeta, return_mintqty, modified_per_price, modified_return = do_plugin(settings, is_test, payer_hash, payer_addr, payer_ada, payer_return_ada, payer_asset_string, policy_id, tx_meta_json, mint_qty_int)
        return_data = {"err": return_err, "action": action, "mint_at_addr": return_mint_at_addr, "tx_meta": return_txmeta, "mint_qty": return_mintqty, "modified_price": modified_per_price, "modified_return": modified_return}

    exit(json.dumps(return_data))
