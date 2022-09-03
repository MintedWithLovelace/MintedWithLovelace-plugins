import bech32
import json
import numpy as np
import random
from getopt import getopt
from os import mkdir
from os.path import dirname, isfile, join as osjoin
from PIL import Image, ImageDraw, ImageFont
from sys import exit, argv
from time import sleep, strftime, gmtime


TOTAL_MINT = 1000
TKN_LIMIT = 400
MAX_PAY = 2000000000
MIN_PAY = 20000000
CACHE_NAME = 'dco_event_cache'
THE_COLOR = (0, 142, 146)
POS_V = 492
POS_H = 437
THE_POS = (POS_H, POS_V)


def do_settings(campaign_name, campaign_root):
    # BEGIN Cusomize Static Setting or Prompt for Input
    cache_folder_name = CACHE_NAME
    # END custom

    cache_dir = osjoin(osjoin(osjoin(campaign_root, 'plugin'), cache_folder_name), '')
    try:
        mkdir(cache_dir)
    except OSError:
        pass
    intlen = len(str(TOTAL_MINT))
    nftrange = [*range(1, (TOTAL_MINT + 1), 1)]
    for nftk, nfti in enumerate(nftrange):
        newi = str(nfti).zfill(intlen)
        nftrange[nftk] = newi
    nftnums = cache_dir + 'nftnumlist.log'
    is_nftnums = isfile(nftnums)
    if not is_nftnums:
        try:
            open(nftnums, 'x')
        except OSError:
            pass
    with open(nftnums, 'w') as instantiate_nftlist:
        instantiate_nftlist.write(','.join(nftrange))
        instantiate_nftlist.close()
    return [
        'Enter Asset Name:',
        'Enter Display Name:',
        'Enter Pinata API Key:',
        'Enter Pinata Secret:',
        'Enter Base Image Name (and paste into the plugin cache dir after setup)'
    ]


def do_plugin(settings, is_test, payer_hash, payer_addr, payer_ada, payer_return_ada, payer_asset_string, policy_id, tx_meta_json, mint_qty_int, current_tip):
    if len(payer_asset_string) > TKN_LIMIT:
        return False, 'refund', tx_meta_json, mint_qty_int

    def get_bech32(s):
        pre = 'e1'
        keytype = s[1]
        if s[2] is True:
            pre = 'e0'
            keytype = keytype + '_test'
        return bech32.bech32_encode(keytype, bech32.convertbits(bytes.fromhex(pre + ''.join([f'{c:04x}' for c in bech32.convertbits(bech32.bech32_decode(s[0])[1], 5, 16)])[-58:-2]), 8, 5))
    seed = payer_addr
    record_addr = payer_addr
    if len(payer_addr) >= 103:
        record_addr = get_bech32([payer_addr, 'stake', is_test])
    nftbasename = settings[2]
    nftlongname = settings[3]
    pn_key = settings[4]
    pn_sec = settings[5]
    img_name = settings[6]
    weigted_ada = payer_ada
    if payer_ada > MIN_PAY:
        if payer_ada > MAX_PAY:
            weigted_ada = MAX_PAY
    mint_weight = (weigted_ada / MAX_PAY)
    random.seed(seed + strftime("%Y-%m-%d_%H-%M-%S", gmtime()))
    err_bool = False
    nettype = 'mainnet'
    if is_test is True:
        nettype = 'testnet'
    campaign_path = osjoin(osjoin(settings[0], nettype), '')
    queued = osjoin(osjoin(osjoin(osjoin(osjoin(campaign_path, 'minting'), ''), 'auto'), 'queued'), '')
    cache_dir = osjoin(osjoin(osjoin(dirname(dirname(dirname(dirname(campaign_path)))), 'plugins'), 'dco_event_cache'), '')
    BASE_IMG = cache_dir + img_name
    THE_FONT = ImageFont.truetype(cache_dir + 'LiberationMono-Regular.ttf', 33)
    nftnum_list = cache_dir + 'nftnumlist.log'
    is_nftnums = isfile(nftnum_list)
    if not is_nftnums:
        intlen = len(str(TOTAL_MINT))
        nftrange = [*range(1, (TOTAL_MINT + 1), 1)]
        for nftk, nfti in enumerate(nftrange):
            newi = str(nfti).zfill(intlen)
            nftrange[nftk] = newi
        with open(nftnum_list, 'w') as instantiate_nftlist:
            instantiate_nftlist.write(','.join(nftrange))
            instantiate_nftlist.close()
    with open(nftnum_list, 'r') as numlistfile:
        nft_list_ini = numlistfile.read().split(',')
        numlistfile.close()
    if len(nft_list_ini) == 0:
        return True, '', tx_meta_json, mint_qty_int
    if len(nft_list_ini) < mint_qty_int:
        mint_qty_int = len(nft_list_ini)

    def pinnata(pn_key, pn_sec, file):
        from requests import post as rpost, models
        errors = [False]
        ipfs_url = 'https://api.pinata.cloud/pinning/pinFileToIPFS'
        ipfs_data, ipfs_content_type = models.RequestEncodingMixin._encode_files(file, {})
        ipfs_headers = {"Content-Type": ipfs_content_type, "pinata_api_key": pn_key, "pinata_secret_api_key": pn_sec}
        limit = 0
        wait_for_api = True
        while wait_for_api:
            ipfs_ret = rpost(ipfs_url, data=ipfs_data, headers=ipfs_headers)
            if 'status_code' in ipfs_ret.json():
                sleep(3)
                # status_code = ipfs_ret.json()['status_code']
                limit += 1
                if limit == 10:
                    wait_for_api = False
                    errors = [True, 'Timed Out Trying to Connect to Pinata API!']
            else:
                wait_for_api = False
                pinned_hash = ipfs_ret.json()['IpfsHash']
        if errors[0] is True:
            return errors, ''
        return errors, pinned_hash

    # DCO Seat Mould
    mint_loop = mint_qty_int
    while mint_loop > 0:
        with open(nftnum_list, 'r') as numlistfile:
            nft_list = numlistfile.read().split(',')
            numlistfile.close()
        nft_num = nft_list.pop(0)
        with open(nftnum_list, 'w') as update_numlist:
            update_numlist.write(','.join(nft_list))
            update_numlist.close()
        nftname = nftbasename + nft_num
        over_num = nft_num
        nftlongname_display = nftlongname + ' #' + nft_num
        mint_loop -= 1
        unique_log = ''
        nft_rarity = ''
        bg = (0, 0, 0, 0)
        out_canvass = Image.open(BASE_IMG)
        out_image = ImageDraw.Draw(out_canvass)
        out_image.text(THE_POS, over_num, fill=THE_COLOR, font=THE_FONT, align='right')
        imgfile = cache_dir + nftname + '.png'
        out_canvass.save(imgfile)
        while True:
            pinerr, ipfs_hash = pinnata(pn_key, pn_sec, {'file': open(imgfile, 'rb')})
            if pinerr[0] is False:
                ipfs_hash = 'ipfs://' + ipfs_hash
                break
        json_template = '{"721": {"' + policy_id.strip() + '": {"' + nftname.strip() + '": {"name": "' + nftlongname_display.strip() + '", "image": "' + ipfs_hash.strip() + '", "Seat Minter": "' + record_addr.strip() + '", "Seat Slot": "' + str(current_tip).strip() + '", "Seat Size": "' + str(mint_weight).strip() + '"}}}}'
        with open(queued + nftname + '.json', 'w') as jsonfileout:
            jsonfileout.write(json_template)
            jsonfileout.close()
    return err_bool, 'mint', tx_meta_json, mint_qty_int


# DO NOT MODIFY BELOW
if __name__ == "__main__":
    # Get user options
    arguments = argv[1:]
    shortopts = "sd"
    longopts = ["setup=", "data="]

    # Setting behaviour for options
    input_data = ''
    input_setup = ''
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
        current_tip = input_data['current_tip']

        # Data in & can return:
        tx_meta_json = input_data['payer_txmeta']
        mint_qty_int = input_data['qty_to_mint']

        # Process main plugin function
        return_err, action, return_txmeta, return_mintqty = do_plugin(settings, is_test, payer_hash, payer_addr, payer_ada, payer_return_ada, payer_asset_string, policy_id, tx_meta_json, mint_qty_int, current_tip)
        return_data = {"err": return_err, "action": action, "tx_meta": return_txmeta, "mint_qty": return_mintqty}

    exit(json.dumps(return_data))
