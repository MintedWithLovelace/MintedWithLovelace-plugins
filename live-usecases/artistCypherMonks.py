import json
import numpy as np
import random
from getopt import getopt
from os import mkdir
from os.path import isfile, join as osjoin
from PIL import Image
from requests import post as rpost
from sys import exit, argv
from time import sleep, strftime, gmtime


USE_PINATA = False
USE_INFURA = True
NFT_ALT_NAME = 'CypherSpy'
NFT_ALT_LONG = 'Cypher Spy'
LIMIT_TKNS = False
TKN_LIMIT = 400
TOTAL_TO_MINT = 5000
USE_STAKE = False
RAFFLE = True
RAFFLE_ASSET = ''
MINT_RESEED = 4
ALT_LEAD_ZEROS = 2

CACHE_NAME = 'cyphermonkcache'
NUM_LIST_FILE = 'nftnumlist.log'
ALT_COUNT_FILE = 'altnumcount.log'
COL_LOG = 'colours.log'
SHUF_LOG = 'shuffle.log'
DEBUG_LOG = ''


# Add-on Function for Debug
def debug_log(out):
    with open(DEBUG_LOG, 'a') as debuglog:
        debuglog.write(str(out) + '\n')
        debuglog.close()


# Add-on Function
def init_file(file_ini):
    is_file = isfile(file_ini)
    if not is_file:
        try:
            open(file_ini, 'x')
        except OSError:
            pass
        if NUM_LIST_FILE in file_ini:
            intlen = len(str(TOTAL_TO_MINT))
            nftrange = [*range(1, (TOTAL_TO_MINT + 1), 1)]
            for nftk, nfti in enumerate(nftrange):
                newi = str(nfti).zfill(intlen)
                nftrange[nftk] = newi
            with open(file_ini, 'w') as instantiate_nftlist:
                instantiate_nftlist.write(','.join(nftrange))
                instantiate_nftlist.close()


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
        'Enter Asset Name:',
        'Enter Display Name:',
        'Enter Pinata API Key:',
        'Enter Pinata Secret:'
    ]


# Customize plugin code
def do_plugin(settings, is_test, payer_hash, payer_addr, payer_ada, payer_return_ada, payer_asset_string, policy_id, tx_meta_json, mint_qty_int):
    if LIMIT_TKNS is True and len(payer_asset_string) > TKN_LIMIT:
        return False, 'refund', tx_meta_json, mint_qty_int
    # payer_assets_tx = payer_asset_string.split('+mwl+')[0]
    # payer_assets_own = payer_asset_string.split('+mwl+')[1]
    # BEGIN Customize Vars/Setting Assignments
    payer_stake = payer_addr
    if USE_STAKE is True:
        if len(payer_addr.strip()) == 103:
            payer_stake = payer_addr.strip()[52:-6]
        if len(payer_addr.strip()) == 108:
            payer_stake = payer_addr.strip()[57:-6]
    seed = payer_stake
    campaign_path = settings[0]
    nftbasename = settings[2]
    nftlongname = settings[3]
    pn_key = settings[4]
    pn_sec = settings[5]
    # static settings
    enable_html = False
    # END custom vars

    # Random seed based on Wallet, Addr, or Wallet + Time
    random.seed(seed + strftime("%Y-%m-%d_%H-%M-%S", gmtime()))
    # random.seed(seed)

    err_bool = False
    nettype = 'mainnet'
    if is_test is True:
        nettype = 'testnet'
    campaign_path = osjoin(osjoin(campaign_path, nettype), '')
    queued = osjoin(osjoin(osjoin(osjoin(osjoin(campaign_path, 'minting'), ''), 'auto'), 'queued'), '')
    cache_dir = osjoin(osjoin(osjoin(campaign_path, 'plugin'), CACHE_NAME), '')
    colour_wheel_src = cache_dir + COL_LOG
    shufflelog_file = cache_dir + SHUF_LOG
    nftnum_list = cache_dir + NUM_LIST_FILE
    altnum_count = cache_dir + ALT_COUNT_FILE
    file_ini_list = []
    file_ini_list += [colour_wheel_src]
    file_ini_list += [shufflelog_file]
    file_ini_list += [nftnum_list]
    file_ini_list += [altnum_count]
    for fileini in file_ini_list:
        init_file(fileini)
    if enable_html is True:
        JSON_TEMP = '{"721": {"POLICY_ID": {"NFT_NAME": {"name": "NFT_LONG_NAME", "artist": "CypherMonks.com", "footnotes": "Cypherdelic Monks of Cardano", "spectrum": SPECTRUM, "attributes": [ATT_LIST],NFT_RARITY"image": "IPFS_HASH", "files": [{"mediaType": "text/html", "src": HTML_DATA}]}}}}'
    else:
        JSON_TEMP = '{"721": {"POLICY_ID": {"NFT_NAME": {"name": "NFT_LONG_NAME", "artist": "CypherMonks.com", "footnotes": "Cypherdelic Monks of Cardano", "spectrum": SPECTRUM, "attributes": [ATT_LIST],NFT_RARITY"image": "IPFS_HASH"}}}}'
    with open(nftnum_list, 'r') as numlistfile:
        nft_list_ini = numlistfile.read().split(',')
        numlistfile.close()
    if len(nft_list_ini) == 0:
        return True, 'zero', tx_meta_json, mint_qty_int
    if len(nft_list_ini) < mint_qty_int:
        mint_qty_int = len(nft_list_ini)

    def encode_to_base64(file_path, type, chunkify=True):
        from base64 import b64encode
        if type == 'html':
            pre = 'data:text/html;base64,'
        if type == 'svg':
            pre = 'data:image/svg+xml;base64,'
        with open(file_path, 'r') as html:
            html_string = html.read()
            html_result = pre + b64encode(bytes(html_string, 'utf-8')).decode('utf-8').strip()
            if chunkify:
                x = 64
                html_result = [html_result[y - x:y] for y in range(x, len(html_result) + x, x)]
        return html_result

    def pinnata(pn_key, pn_sec, file):
        from requests import models
        pinned_hash = 'Unknown Error'
        errors = False
        ipfs_url = 'https://api.pinata.cloud/pinning/pinFileToIPFS'
        ipfs_data, ipfs_content_type = models.RequestEncodingMixin._encode_files(file, {})
        ipfs_headers = {"Content-Type": ipfs_content_type, "pinata_api_key": pn_key, "pinata_secret_api_key": pn_sec}
        limit = 0
        wait_for_api = True
        while wait_for_api:
            ipfs_ret = rpost(ipfs_url, data=ipfs_data, headers=ipfs_headers)
            if 'Response [200]' not in str(ipfs_ret):
                sleep(3)
                limit += 1
                if limit == 10:
                    wait_for_api = False
                    errors = True
                    pinned_hash = 'Error trying to pin to Pinata API: ' + str(ipfs_ret)
            else:
                wait_for_api = False
                pinned_hash = ipfs_ret.json()['IpfsHash']
        return errors, pinned_hash

    def infura(pid, psec, file):
        ipfs_url = 'https://ipfs.infura.io:5001/api/v0/add'
        pinned_hash = 'Unknown Error'
        errors = False
        limit = 0
        wait_for_api = True
        while wait_for_api:
            ipfs_ret = rpost(ipfs_url, files=file, auth=(pid, psec))
            if 'Response [200]' not in str(ipfs_ret):
                sleep(3)
                limit += 1
                if limit == 10:
                    wait_for_api = False
                    errors = True
                    pinned_hash = 'Error trying to pin to Infura API: ' + str(ipfs_ret)
            else:
                wait_for_api = False
                pinned_hash = ipfs_ret.text.split(',')[1].split(':')[1].replace('"', '')
        # debug_log(pinned_hash)
        return errors, pinned_hash

    # CypherMonk Artist
    mint_loop = mint_qty_int
    mint_count = 0
    while mint_loop > 0:
        if mint_count == MINT_RESEED:
            seed = strftime("%Y-%m-%d_%H-%M-%S", gmtime()) + payer_stake
            mint_count = 0
        mint_count += 1
        sleep(7)
        with open(nftnum_list, 'r') as numlistfile:
            nft_list = numlistfile.read().split(',')
            numlistfile.close()
        nft_to_pop = random.randrange(len(nft_list))
        mint_loop -= 1
        unique_log = ''
        nft_rarity = ''

        # Tuning Nobs
        tune_each_colour_unique = False  # False means each set of colours is unique to its address/seed
        tune_sm_force = False  # Enforce smoke
        tune_sm_alpha = False  # Enforce alpha for fire
        tune_sg_force = False  # Enforce sunglasses
        tune_sg_alpha = True  # Allow for multicolour glasses / Disables multicolour background - convert to derived option
        tune_sg_alpha_prob = 8  # Probability of multicolour glasses
        tune_canvass_inner_row_a = 2  # Good: Row repeat count
        tune_canvass_count = 6 #''  # Override for automated canvass generator
        tune_canvass_min = 4 #3
        # TODO : do away with alpha global after background colours are all selected
        tune_global_alpha = ''  # 200  # Global transparency of all colours
        tune_alpha_min = 240
        tune_out_wh = 640  # Pixel Width/Height for output image
        tune_pixel_set1 = 64
        tune_pixel_set2 = 520
        tune_pixel_set3 = 128
        tune_pixel_set4 = 744
        tune_canvass_seeded = True
        tune_canvass_row_uniqueness = False  # Randomizes later, this is an override. Set to '' to disable override
        tune_colour_pallette = 12 #0
        tune_canvass_shift_colours = True
        tune_bg_force_colour = ''
        tune_bg_prelist = True
        tune_bg_alt_rand = True
        tune_allow_sg_bg_alt = True  # allow shades for back of alt winter monk
        tune_colour_deviation_at_random = 90  #30 Minimum is 3%

        if tune_colour_deviation_at_random < 3:
            tune_colour_deviation_at_random = 3
        adj_colour = int(255 * (tune_colour_deviation_at_random / 100))

        # Colour Presets
        ada_blue = (0, 51, 173, 255)
        ada_blue_alpha = (0, 51, 173, 190)
        eth_blue = (28, 28, 225, 255)
        eth_blue_alpha = (28, 28, 225, 190)
        btc_gold = (247, 147, 26, 255)
        btc_gold_alpha = (247, 147, 26, 190)
        cm_original = (136, 61, 212, 255)
        cm_original_alpha = (136, 61, 212, 190)
        diamond = (76, 208, 246, 255)
        diamond_alpha = (76, 208, 246, 190)
        silver = (192, 192, 192, 255)
        gold = (255, 215, 0, 255)
        slate = (25, 25, 25, 255)
        slate_alpha = (25, 25, 25, 190)
        slate_alpha_light = (25, 25, 25, 20)
        white_alpha = (255, 255, 255, 255, 190)

        # Other Backgrounds
        radioactive = (7, 249, 139, 255)
        darkpurple = (78, 198, 94, 255)
        skyblue = (4, 202, 198, 255)
        limegreen = (129, 234, 92, 255)
        cloudyday = (29, 93, 121, 255)
        blue_dawn = (115, 148, 204, 255)
        middayblue = (142, 208, 224, 255)
        hazyblue = (157, 162, 190, 255)
        rich_blue = (1, 145, 223, 255)
        copper = (62, 6, 77, 255)
        teal = (32, 181, 119, 255)
        rich_pink = (233, 24, 107, 255)
        faded_pink = (200, 51, 127, 255)
        radioactive_alpha = (7, 249, 139, random.randint(190, 250))
        darkpurple_alpha = (78, 198, 94, random.randint(190, 250))
        skyblue_alpha = (4, 202, 198, random.randint(190, 250))
        limegreen_alpha = (129, 234, 92, random.randint(190, 250))
        cloudyday_alpha = (29, 93, 121, random.randint(190, 250))
        blue_dawn_alpha = (115, 148, 204, random.randint(190, 250))
        middayblue_alpha = (142, 208, 224, random.randint(190, 250))
        hazyblue_alpha = (157, 162, 190, random.randint(190, 250))
        rich_blue_alpha = (1, 145, 223, random.randint(190, 250))
        copper_alpha = (62, 6, 77, random.randint(190, 250))
        teal_alpha = (32, 181, 119, random.randint(190, 250))
        rich_pink_alpha = (233, 24, 107, random.randint(190, 250))
        faded_pink_alpha = (200, 51, 127, random.randint(190, 250))

        # Variants Set
        variants = [
            [(142, 139, 139, 255), (116, 116, 116, 255)],  # frock primary colour
            [(58, 58, 58, 255)],  # frock highlight colour
            [(96, 96, 96, 255), (58, 58, 58, 255)],  # frock shadow colour
            [],  # skin colour
            [],  # eyebrow colour
            [],  # eyewhites colour
            [],  # eye pupil colour
            [],  # mouth colour
        ]
        variant_count = len(variants)
        if tune_colour_pallette < (variant_count + 1):
            tune_colour_pallette = (variant_count + 1)

        # Individual Sets
        bd = (0, 0, 0, 255)  # Body Outline
        bg_opts = []
        bg_opts_alt = []
        if tune_bg_prelist is True:
            bg_opts = [ada_blue, eth_blue, btc_gold, cm_original, diamond, radioactive, darkpurple, skyblue, limegreen, cloudyday, blue_dawn, middayblue, hazyblue, rich_blue, copper, teal, rich_pink, faded_pink, ada_blue_alpha, eth_blue_alpha, btc_gold_alpha, cm_original_alpha, diamond_alpha, radioactive_alpha, darkpurple_alpha, skyblue_alpha, limegreen_alpha, cloudyday_alpha, blue_dawn_alpha, middayblue_alpha, hazyblue_alpha, rich_blue_alpha, copper_alpha, teal_alpha, rich_pink_alpha, faded_pink_alpha]
        sg_opts = [btc_gold_alpha, ada_blue_alpha, diamond_alpha, cm_original_alpha, eth_blue_alpha, slate_alpha_light, slate_alpha, white_alpha]  # Sunglasses
        # sm_opts = [(148, 92, 16, 255)]
        # sf_opts = [(231, 71, 0, 255), (0, 0, 0, 0)]
        er_opts = [diamond, diamond_alpha, silver, gold, slate, slate_alpha, slate_alpha_light, ada_blue, ada_blue_alpha, eth_blue, eth_blue_alpha, btc_gold, btc_gold_alpha, cm_original, cm_original_alpha]
        white_opac = (255, 255, 255, 255)
        transparent = (0, 0, 0, 0)
        bg = transparent

        # Begin Processing
        random.seed(seed + strftime("%Y-%m-%d_%H-%M-%S", gmtime()))
        if tune_global_alpha == '':
            tune_global_alpha = random.choice([random.randint(tune_alpha_min, 254), 255])
        if tune_canvass_count == '':
            if tune_global_alpha != 255:
                tune_canvass_count = tune_canvass_min  # random.randint(3, 8)
            else:
                tune_canvass_count = tune_canvass_min
        random.seed(seed)
        randmaster = []
        swatch = []
        count_colours = 0
        if not bg_opts:
            bg_opts += [(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), tune_global_alpha)]
        while count_colours < tune_colour_pallette:
            while True:
                if count_colours == 0:
                    colour_list = [random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)]
                else:
                    for colourkey, colour_item in enumerate(colour_list):
                        minus = False
                        adj_num = random.randint(4, adj_colour)
                        if int(colour_item - adj_colour) >= 0:
                            if int(colour_item + adj_colour) > 255:
                                minus = True
                            else:
                                minus = random.choice([True, False])
                        if minus is True:
                            colour_list[colourkey] = (colour_item - adj_num)
                        else:
                            colour_list[colourkey] = (colour_item + adj_num)
                colour_chosen = (colour_list[0], colour_list[1], colour_list[2], tune_global_alpha)
                if colour_chosen != white_opac:
                    unique_is = True
                    with open(colour_wheel_src, 'r') as colour_wheel:
                        for line in colour_wheel:
                            if (str(colour_chosen) in line) and (seed not in line):
                                unique_is = False
                                break
                        colour_wheel.close()
                    if unique_is is True:
                        break
            if tune_each_colour_unique is True:
                with open(colour_wheel_src, 'a') as colour_wheel_add:
                    colour_wheel_add.write(str(colour_chosen) + '\n')
                    colour_wheel_add.close()
            randmaster += [colour_chosen]
            swatch += [colour_chosen]
            count_colours += 1
        if tune_each_colour_unique is False:
            count_spect = 0
            for randc in randmaster:
                add_pipe = ''
                if count_spect > 0:
                    add_pipe = '|'
                unique_log += add_pipe + str(randc)
                count_spect += 1
            with open(colour_wheel_src, 'a') as colour_wheel_add:
                colour_wheel_add.write(seed + unique_log + '\n')
                colour_wheel_add.close()

        # Unique Colour Canvass
        random.seed(seed + strftime("%Y-%m-%d_%H-%M-%S", gmtime()))
        if tune_canvass_row_uniqueness == '':
            tune_canvass_row_uniqueness = random.choice([True, False])
        while True:
            reshuffle = False
            random.shuffle(randmaster)
            stringified = str(randmaster)
            with open(shufflelog_file, 'r') as shufflelog:
                for shuffleline in shufflelog:
                    if stringified == shuffleline:
                        reshuffle = True
                        break
            if reshuffle is False:
                with open(shufflelog_file, 'a') as shufflelog:
                    shufflelog.write(stringified + '\n')
                break
        pixel_range_a = random.randint(tune_pixel_set1, tune_pixel_set2)
        pixel_range_b = random.randint(tune_pixel_set3, tune_pixel_set4)
        pixel_range_lo = pixel_range_a
        pixel_range_hi = pixel_range_b
        if pixel_range_a > pixel_range_b:
            pixel_range_hi = pixel_range_a
            pixel_range_lo = pixel_range_b

        # Reestablish seed directive
        canvass_count = 0
        canvass_x = ''
        canvass_y = ''
        out_canvass = ''
        original = ''
        if tune_canvass_seeded is True:
            random.seed(seed)
        else:
            random.seed(seed + strftime("%Y-%m-%d_%H-%M-%S", gmtime()))
        while True:
            num_hi = random.randint(pixel_range_lo, pixel_range_hi)
            count_i = num_hi
            canvass = []
            while count_i > 0:
                canvass += [list(range(1, num_hi))]
                count_i -= 1
            prev_colour = 0
            prev_colour_a = 0
            prev_colour_b = 0
            prev_colour_c = 0
            prev_colour_d = 0
            row_count = 0
            colour_zero = []
            for row, line in enumerate(canvass):
                if row_count == 0:
                    if tune_canvass_row_uniqueness is False:
                        prev_colour = random.choice(randmaster)
                        prev_colour_a = random.choice(randmaster)
                        prev_colour_b = random.choice(randmaster)
                        prev_colour_c = random.choice(randmaster)
                        prev_colour_d = random.choice(randmaster)
                    else:
                        prev_colour_a = prev_colour_b = prev_colour_c = prev_colour_d = prev_colour = random.choice(randmaster)
                if row_count == 1 or row_count == 2:
                    prev_colour_b = random.choice(randmaster)
                    if tune_canvass_shift_colours is True:
                        prev_colour_a = prev_colour_b
                if row_count == 3 or row_count == 4:
                    prev_colour_c = random.choice(randmaster)
                    if tune_canvass_shift_colours is True:
                        prev_colour_b = prev_colour_c
                if row_count == 5 or row_count == 6:
                    prev_colour_d = random.choice(randmaster)
                    if tune_canvass_shift_colours is True:
                        prev_colour_c = prev_colour_d
                row_count += 1
                if row_count < tune_canvass_inner_row_a:
                    colour_zero.append(random.choice(sg_opts))
                coin_one = [prev_colour_d, prev_colour_d, prev_colour_d, prev_colour_d, prev_colour_d, prev_colour_a, prev_colour_a, prev_colour_a, prev_colour_a, prev_colour_a, prev_colour, prev_colour, prev_colour, prev_colour, prev_colour, prev_colour_b, prev_colour_b, prev_colour_b, prev_colour_b, prev_colour_b, prev_colour_c, prev_colour_c, prev_colour_c, prev_colour_c, prev_colour_c, prev_colour_c, prev_colour_c, prev_colour_c, prev_colour_c, prev_colour_c]
                coin_two = [prev_colour_d, prev_colour_d, prev_colour_d, prev_colour_d, prev_colour_d, prev_colour_a, prev_colour_a, prev_colour_a, prev_colour_a, prev_colour_a, prev_colour, prev_colour, prev_colour, prev_colour, prev_colour, prev_colour_c, prev_colour_c, prev_colour_b, prev_colour_b, prev_colour_b, prev_colour_b, prev_colour_b, prev_colour_b, prev_colour_b, prev_colour_b, prev_colour_b, prev_colour_b]
                coin_three = [prev_colour_d, prev_colour_d, prev_colour_a, prev_colour_a, prev_colour_a, prev_colour_a, prev_colour_a, prev_colour_a, prev_colour_a, prev_colour_a, prev_colour_a, prev_colour_a, prev_colour, prev_colour, prev_colour, prev_colour, prev_colour, prev_colour_b, prev_colour_b, prev_colour_b, prev_colour_b, prev_colour_b, prev_colour_c, prev_colour_c, prev_colour_c, prev_colour_c, prev_colour_c, prev_colour_c]
                coin_four = [prev_colour_d, prev_colour_d, prev_colour_d, prev_colour_d, prev_colour_d, prev_colour_d, prev_colour_d, prev_colour_d, prev_colour_d, prev_colour_d, prev_colour_a, prev_colour_a, prev_colour_a, prev_colour_a, prev_colour_a, prev_colour, prev_colour, prev_colour, prev_colour, prev_colour, prev_colour, prev_colour, prev_colour, prev_colour, prev_colour, prev_colour_b, prev_colour_b, prev_colour_b, prev_colour_b, prev_colour_b, prev_colour_c, prev_colour_c, prev_colour_c, prev_colour_c, prev_colour_c, prev_colour_c]
                coin_five = [prev_colour_d, prev_colour_d, prev_colour_d, prev_colour_d, prev_colour_d, prev_colour_d, prev_colour_d, prev_colour_d, prev_colour_d, prev_colour_d, prev_colour_a, prev_colour_a, prev_colour_a, prev_colour_a, prev_colour_a, prev_colour, prev_colour, prev_colour, prev_colour, prev_colour, prev_colour_b, prev_colour_b, prev_colour_b, prev_colour_b, prev_colour_b, prev_colour_c, prev_colour_c, prev_colour_c, prev_colour_c, prev_colour_c, prev_colour_c]
                coin_toss = [[colour_zero, coin_one, coin_two], [coin_three, coin_four, coin_five]]
                coin_toss = random.choice(coin_toss)
                coin_toss = random.choice(coin_toss)
                for pixel, column in enumerate(line):
                    canvass[row][pixel] = prev_colour = random.choice([random.choice(coin_toss)])

            # Generate canvass image
            random.seed(seed + strftime("%Y-%m-%d_%H-%M-%S", gmtime()))
            canvass_gen = True
            rotate_canvass = 0
            size_canvass = tune_out_wh
            if canvass_count > 0:
                if (canvass_count + 2) == tune_canvass_count:
                    size_canvass = int(tune_out_wh * 0.3)
                    tune_main_rotate = random.randint(1, 100)
                    if tune_main_rotate > 89 and tune_global_alpha != 255:
                        rotate_canvass = 0
                    else:
                        rotate_canvass = 45  # random.choice([90, 45, 0])
                        size_canvass = int(tune_out_wh * 0.28)
                elif (canvass_count + 1) == tune_canvass_count:
                    rotate_canvass = 0
                    size_canvass = int(tune_out_wh * 0.12)
                else:
                    break
                #    rotate_canvass = random.randint(0, 270)
                #    size_canvass = random.randint(int(tune_out_wh * 0.05), int(tune_out_wh * 0.75))
            try:
                canvass_array = np.array(canvass, dtype=np.uint8)
                canvass_image = Image.fromarray(canvass_array, mode='RGBA')
                canvass_image = canvass_image.resize((size_canvass, size_canvass), resample=Image.NEAREST).rotate(rotate_canvass)
            except Exception:
                canvass_gen = False
            if canvass_gen is True:
                if canvass_count > 0:
                    # x1 = int(.5 * canvass_image.size[0]) - int(.5 * canvass_image.size[0])
                    # y1 = int(.5 * canvass_image.size[1]) - int(.5 * canvass_image.size[1])
                    # x2 = int(.5 * canvass_image.size[0]) + int(.5 * canvass_image.size[0])
                    # y2 = int(.5 * canvass_image.size[1]) + int(.5 * canvass_image.size[1])
                    w, h = canvass_image.size
                    out_w, out_h = out_canvass.size
                    y_coord = (out_w - w)
                    ratio = random.randint(1, 80)
                    if not canvass_x:
                        canvass_x = random.randint(0, int(y_coord))
                        canvass_y = random.randint(0, int(y_coord))
                    else:
                        canvass_x = int(canvass_x / ratio)
                        canvass_y = int(canvass_y / ratio)
                    if (canvass_count + 1) == tune_canvass_count:
                        canvass_x, canvass_y = int(tune_out_wh * 0.68), int(tune_out_wh * 0.6)
                    if (canvass_count + 2) == tune_canvass_count:
                        last_coords = int(tune_out_wh * 0.3625)
                        canvass_x, canvass_y = last_coords, last_coords
                    if rotate_canvass == 45:
                        canvass_x, canvass_y = canvass_x + int(tune_out_wh * 0.03), canvass_y - int(tune_out_wh * 0.02)
                    try:
                        out_canvass.paste(canvass_image, (canvass_x, canvass_y), mask=canvass_image)  # box=(x1, y1, x2, y2)
                    except Exception:
                        continue
                    out_canvass.convert(original.mode)
                else:
                    original = out_canvass = canvass_image
                canvass_count += 1
            if canvass_count == tune_canvass_count:
                break
        # out_canvass.show()
        # exit(0)

        # Reset seed for unique datetimestring
        while True:
            for variant in variants:
                try:
                    variant.append(randmaster.pop())
                except Exception:
                    continue
            fc = random.choice(variants[0])
            fh = random.choice(variants[1])
            fs = random.choice(variants[2])
            sk = random.choice(variants[3])
            if sk[3] != 255:
                sk = (sk[0], sk[1], sk[2], 255)
            eb = random.choice(variants[4])
            ew = random.choice(variants[5])
            ep = random.choice(variants[6])
            mt = random.choice(variants[7])
            sm = bd
            sf = bd
            ss = bd
            sz = bg
            er_opts.append(sk)
            er = random.choice(er_opts)

            if tune_sm_force is True:
                sm_active = True
            else:
                sm_active = random.choice([True, False, False, False]) # 25% Chance of smoke

            if sm_active is True:
                # TODO : Return to opts and do work there
                sm = random.choice(variants[4])  # sm_opts)
                sf = random.choice(variants[6])  # sf_opts)
                ss = sz = random.choice(variants[5])  # white_opac
                if tune_sm_alpha is True:
                    sf = transparent

            if tune_sg_alpha is True:
                if tune_bg_force_colour:
                    bg = tune_bg_force_colour
                else:
                    bg = random.choice(bg_opts)
                if sm_active is False:
                    sz = bg
                sg_add_count = 0
                while sg_add_count < tune_sg_alpha_prob:
                    sg_opts.append(transparent)
                    sg_add_count += 1
            if tune_sg_force is True:
                sg = random.choice(sg_opts)
            else:
                sg = random.choice([random.choice(sg_opts), sk, sk]) # 33% chance of shades
            # Eyes if no shades
            if sk != sg:
                ep = ew = eb = sg

            # Construct JSON Values
            att_list = ''
            att_list += '{"Background": "' + str(bg) + '"}'
            att_list += ',{"Frock": "' + str(fc) + '/' + str(fh) + '/' + str(fs) + '"}'
            att_list += ',{"Skin": "' + str(sk) + '"}'
            att_list += ',{"Mouth": "' + str(mt) + '"}'
            att_list += ',{"Shades": "' + str(sg) + '"}'
            if er != sk:
                att_list += ',{"Earring": "' + str(er) + '"}'
            if sm_active is True:
                att_list += ',{"420": "' + str(sm) + '/' + str(sf) + '/' + str(sz) + '"}'
            if not nft_rarity:
                nft_rarity = ' '

            # Check if minted
            # Monk Templates
            cm_orig = [
                [bg, bg, bg, bg, bg, bg, bg, bg, bg, bg, bg, bg, bg, bg, bg, bg, bg, bg, bg, bg, bg, bg, bg, bg, bg, bg, bg, bg, bg, bg, bg, bg],
                [bg, bg, bg, bg, bg, bg, bg, bg, bg, bd, bd, bd, bd, bd, bd, bg, bg, bg, bg, bg, bg, bg, bg, bg, sz, bg, bg, bg, bg, bg, bg, bg],
                [bg, bg, bg, bg, bg, bg, bg, bg, bd, fc, fc, fc, fc, fc, fc, bd, bd, bd, bg, bg, bg, bg, bg, bg, bg, bg, bg, bg, bg, bg, bg, bg],
                [bg, bg, bg, bg, bg, bg, bg, bg, bd, fs, fc, fc, fc, fc, fc, fc, fc, fc, bd, bd, bg, bg, bg, bg, bg, bg, bg, bg, bg, bg, bg, bg],
                [bg, bg, bg, bg, bg, bg, bg, bg, bd, fs, fs, fc, fc, fc, fc, fc, fc, fc, fc, fc, bd, bg, bg, bg, sz, bg, bg, bg, bg, bg, bg, bg],
                [bg, bg, bg, bg, bg, bg, bg, bg, bd, fs, fs, fs, fc, fc, fc, fc, fc, fc, fc, fc, fc, bd, bg, bg, bg, bg, bg, bg, bg, bg, bg, bg],
                [bg, bg, bg, bg, bg, bg, bg, bg, bd, fs, fs, fc, fc, fc, fc, fc, fc, fc, fc, fc, fc, fc, bd, bg, bg, bg, bg, bg, bg, bg, bg, bg],
                [bg, bg, bg, bg, bg, bg, bg, bg, bd, fs, fc, fc, fc, fc, fc, fs, fs, fs, fs, fs, fc, fc, fc, bd, sz, bg, bg, bg, bg, bg, bg, bg],
                [bg, bg, bg, bg, bg, bg, bg, bg, bd, fc, fc, fc, fc, fs, fs, bd, bd, bd, bd, bd, fs, fs, fc, bd, bg, bg, bg, bg, bg, bg, bg, bg],
                [bg, bg, bg, bg, bg, bg, bg, bd, fc, fc, fc, fc, fs, bd, bd, bd, bd, bd, bd, bd, bd, bd, fs, fc, bd, bg, bg, bg, bg, bg, bg, bg],
                [bg, bg, bg, bg, bg, bg, bg, bd, fc, fc, fc, fc, fs, bd, bd, sk, sk, sk, sk, bd, bd, bd, bd, fs, ss, bg, bg, bg, bg, bg, bg, bg],
                [bg, bg, bg, bg, bg, bg, bd, fs, fc, fc, fc, fs, bd, bd, sk, sk, sk, sk, sk, sk, sk, bd, bd, bd, bd, bg, bg, bg, bg, bg, bg, bg],
                [bg, bg, bg, bg, bg, bg, bd, fs, fc, fc, fc, fs, bd, sk, sk, sk, sk, sk, sk, sk, sk, bd, bd, bd, ss, bg, bg, bg, bg, bg, bg, bg],
                [bg, bg, bg, bg, bg, bg, bd, fs, fc, fc, fs, fs, bd, sg, sg, eb, eb, sg, sg, eb, eb, bd, bd, bd, ss, bg, bg, bg, bg, bg, bg, bg],
                [bg, bg, bg, bg, bg, bd, fs, fs, fs, fc, fs, fs, bd, sk, sg, ew, ep, sg, sk, ew, ep, bd, bd, bd, ss, bg, bg, bg, bg, bg, bg, bg],
                [bg, bg, bg, bg, bd, fs, fs, fs, fs, fs, fs, fs, bd, sk, sk, sg, sg, sg, sk, sk, sg, bd, bd, bd, ss, bd, bg, bg, bg, bg, bg, bg],
                [bg, bg, bg, bg, bd, fs, fs, fs, fs, fs, fs, bd, bd, sk, sk, sk, sk, sk, sk, sk, sk, sk, bd, bd, ss, bd, bg, bg, bg, bg, bg, bg],
                [bg, bg, bg, bg, bd, fs, fs, fs, fs, fs, fs, bd, sk, sk, sk, sk, sk, sk, sk, sk, sk, sk, bd, bd, ss, bd, bg, bg, bg, bg, bg, bg],
                [bg, bg, bg, bd, fs, fs, fs, fs, fs, fs, bd, bd, er, sk, sk, sk, sk, sk, sk, sk, sk, bd, bd, bd, bd, bd, bg, bg, bg, bg, bg, bg],
                [bg, bg, bg, bd, fs, fs, fs, bd, fs, fs, bd, bd, bd, sk, sk, sk, sk, sk, sk, sk, sk, bd, bd, bd, bd, bd, bg, bg, bg, bg, bg, bg],
                [bg, bg, bg, bd, fs, bd, bd, bd, fs, fs, bd, bd, bd, sk, sk, sk, sk, sk, mt, mt, sm, sm, sm, sm, sf, bd, bg, bg, bg, bg, bg, bg],
                [bg, bg, bg, bd, bd, bd, fs, fs, fs, fs, bd, bd, bd, bd, sk, sk, sk, sk, sk, sk, bd, bd, bd, bd, bd, bd, bd, bg, bg, bg, bg, bg],
                [bg, bg, bd, bd, fs, fs, fs, fc, fs, bd, bd, bd, bd, bd, bd, sk, sk, sk, sk, bd, bd, bd, bd, bd, bd, bd, bd, bg, bg, bg, bg, bg],
                [bd, bd, fs, fs, fc, fc, fc, fc, fs, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bg, bg, bg, bg, bg],
                [bd, fs, fc, fc, fc, fc, fc, fc, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bg, bg, bg, bg, bg],
                [bd, fs, fs, fs, fc, fc, fc, fc, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bg, bg, bg, bg],
                [bd, bd, bd, bd, bd, fc, fc, fc, fc, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, fs, bd, bg, bg, bg],
                [bd, fs, fs, fc, bd, bd, fc, fc, fc, fs, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, fs, fs, bd, bd, bg, bg],
                [fs, fs, fc, fc, fc, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, fs, fs, fs, fs, fs, fs, fs, bd, bd, bg],
                [fs, fc, fc, fc, fc, fc, fc, fc, fc, fc, fs, fs, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, fs, fc, fc, fc, fs, fs, fs, fs, bd, bd],
                [fs, fc, fc, fc, fc, fc, fc, fc, fc, fc, fc, fc, fs, fs, fs, fs, fs, bd, bd, bd, fs, fs, fc, fc, fc, fc, fc, fc, fs, fs, fs, bd],
                [fs, fc, fc, fc, fc, fc, fc, fc, fc, fc, fc, fc, fc, fs, fs, fs, fs, fs, fs, fs, fc, fc, fc, fc, fc, fc, fc, fc, fc, fs, fs, fs],
            ]
            random_monk = range(1, 100)
            # Create images
            chosen_list = cm_orig
            get_random_monk = random.choice(random_monk)
            if get_random_monk == 1 or get_random_monk == 47:
                if tune_bg_alt_rand is True:
                    alt_bg_color_grid = [[],[],[],[],[],[],[],[],[]]
                    for ck, color_chosen in enumerate(alt_bg_color_grid):
                        alt_bg_color_grid[ck] = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), tune_global_alpha)
                    bg_opts_alt = random.choice(alt_bg_color_grid)
                if not bg_opts_alt:
                    _g = bg
                else:
                    _g = bg_opts_alt
                _g = bg
                # Override tweak for shades to be winger back
                if tune_allow_sg_bg_alt is True and sk == sg:
                    _g = sg
                cm_winter = [
                    [_g, _g, _g, _g, _g, _g, _g, _g, _g, _g, _g, _g, _g, _g, _g, _g, _g, _g, _g, _g, _g, _g, _g, _g, _g, _g, _g, _g, _g, _g, _g, _g],
                    [_g, _g, _g, _g, _g, _g, _g, _g, _g, bd, bd, bd, bd, bd, bd, _g, _g, _g, _g, _g, _g, _g, _g, _g, _g, _g, _g, _g, _g, _g, _g, _g],
                    [_g, _g, _g, _g, _g, _g, _g, _g, bd, fs, fh, fh, fh, fh, fh, bd, bd, bd, _g, _g, _g, _g, _g, _g, _g, _g, _g, _g, _g, _g, _g, _g],
                    [_g, _g, _g, _g, _g, _g, _g, _g, bd, fs, fs, fs, fh, fh, fh, fh, fh, fh, bd, bd, _g, _g, _g, _g, _g, _g, _g, _g, _g, _g, _g, _g],
                    [_g, _g, _g, _g, _g, _g, _g, _g, bd, fs, fs, fs, fs, fs, fh, fh, fh, fh, fh, fs, bd, _g, _g, _g, _g, _g, _g, _g, _g, _g, _g, _g],
                    [_g, _g, _g, _g, _g, _g, _g, _g, bd, fs, fs, fs, fs, fs, fs, fs, fs, fh, fh, fh, fs, bd, _g, _g, _g, _g, _g, _g, _g, _g, _g, _g],
                    [_g, _g, _g, _g, _g, _g, _g, _g, bd, fs, fs, fs, fs, fs, fs, fs, fh, fh, fh, fh, fs, fs, _g, _g, _g, _g, _g, _g, _g, _g, _g, _g],
                    [_g, _g, _g, _g, _g, _g, _g, _g, bd, fs, fs, fs, fs, fs, fs, fh, fh, fh, fh, fh, fh, fs, fs, _g, _g, _g, _g, _g, _g, _g, _g, _g],
                    [_g, _g, _g, _g, _g, _g, _g, _g, bd, fs, fs, fs, fs, fs, fh, fh, fh, fh, fh, fh, fh, fh, bd, _g, _g, _g, _g, _g, _g, _g, _g, _g],
                    [_g, _g, _g, _g, _g, _g, _g, bd, fs, fs, fs, fs, fh, fh, fh, fh, fh, fh, fh, fh, fs, fs, bd, bd, _g, _g, _g, _g, _g, _g, _g, _g],
                    [_g, _g, _g, _g, _g, _g, _g, bd, fs, fs, fh, fh, fh, fh, fh, fh, fh, fh, fs, fs, fs, fs, bd, bd, _g, _g, _g, _g, _g, _g, _g, _g],
                    [_g, _g, _g, _g, _g, _g, bd, fs, fs, fh, fh, fh, fh, fh, fh, fh, fs, fs, fs, fs, fs, bd, bd, bd, _g, _g, _g, _g, _g, _g, _g, _g],
                    [_g, _g, _g, _g, _g, _g, bd, fs, fh, fh, fh, fh, fh, fh, fs, fs, fs, fs, fs, fs, bd, bd, bd, bd, _g, _g, _g, _g, _g, _g, _g, _g],
                    [_g, _g, _g, _g, _g, _g, bd, fs, fh, fh, fh, fs, fs, fs, fs, fs, fs, fs, fs, fs, fs, fs, bd, bd, bd, _g, _g, _g, _g, _g, _g, _g],
                    [_g, _g, _g, _g, _g, bd, fs, fs, fs, fh, fs, fs, fs, fs, fs, fs, bd, bd, bd, bd, bd, fs, fs, bd, bd, _g, _g, _g, _g, _g, _g, _g],
                    [_g, _g, _g, _g, bd, fs, fs, fs, fs, fs, fs, fs, fs, fs, fs, bd, bd, sk, sk, sk, bd, bd, fs, fs, bd, _g, _g, _g, _g, _g, _g, _g],
                    [_g, _g, _g, _g, bd, fs, fs, fs, fs, fs, fs, fs, fs, fs, bd, bd, sk, sk, sk, sk, sk, bd, bd, fs, bd, _g, _g, _g, _g, _g, _g, _g],
                    [_g, _g, _g, _g, bd, fs, fs, fs, fs, fs, fs, fs, fs, bd, bd, sk, sk, sk, sk, sk, sk, sk, bd, bd, bd, _g, _g, _g, _g, _g, _g, _g],
                    [_g, _g, _g, bd, fs, fs, fs, fs, fs, fs, fs, fs, bd, bd, sk, sk, sk, sk, sk, sk, sk, bd, bd, bd, bd, bd, _g, _g, _g, _g, _g, _g],
                    [_g, _g, _g, bd, fs, fs, fs, bd, fs, fs, fs, bd, bd, sk, sk, sk, sk, sk, sk, sk, sk, bd, bd, bd, bd, bd, _g, _g, _g, _g, _g, _g],
                    [_g, _g, _g, bd, fs, bd, bd, bd, fs, fs, fs, bd, bd, sk, sk, sk, sk, sk, bd, bd, bd, bd, bd, bd, bd, bd, _g, _g, _g, _g, _g, _g],
                    [_g, _g, _g, bd, bd, bd, fs, fs, fs, fs, fs, bd, bd, bd, sk, sk, sk, sk, sk, sk, bd, bd, bd, bd, bd, bd, bd, _g, _g, _g, _g, _g],
                    [_g, _g, bd, bd, fs, fs, fs, fc, fs, fs, bd, bd, bd, bd, bd, sk, sk, sk, sk, bd, bd, bd, bd, bd, bd, bd, bd, _g, _g, _g, _g, _g],
                    [bd, bd, fs, fs, fc, fc, fc, fc, fs, fs, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, _g, _g, _g, _g, _g],
                    [bd, fs, fc, fc, fc, fc, fc, fc, fs, fs, fs, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, _g, _g, _g, _g, _g],
                    [bd, fs, fs, fs, fc, fc, fc, fc, fs, fs, fs, fs, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, _g, _g, _g, _g],
                    [bd, bd, bd, bd, bd, fc, fc, fc, fc, fs, fs, fs, fs, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, fs, bd, _g, _g, _g],
                    [bd, fs, fs, fc, bd, bd, fc, fc, fc, fs, fs, fs, fs, fs, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, bd, fs, fs, bd, bd, _g, _g],
                    [fs, fs, fc, fc, fc, bd, bd, bd, bd, bd, bd, bd, bd, fs, fs, bd, bd, bd, bd, bd, bd, bd, fs, fs, fs, fs, fs, fs, fs, bd, bd, _g],
                    [fs, fc, fc, fc, fc, fc, fc, fc, fc, fc, fs, fs, bd, bd, fs, fs, bd, bd, bd, bd, bd, bd, fs, fc, fc, fc, fs, fs, fs, fs, bd, bd],
                    [fs, fc, fc, fc, fc, fc, fc, fc, fc, fc, fc, fc, fs, fs, bd, fs, fs, bd, bd, bd, fs, fs, fc, fc, fc, fc, fc, fc, fs, fs, fs, bd],
                    [fs, fc, fc, fc, fc, fc, fc, fc, fc, fc, fc, fc, fc, fs, fs, fs, fs, fs, fs, fs, fc, fc, fc, fc, fc, fc, fc, fc, fc, fs, fs, fs],
                ]
                chosen_list = cm_winter
                with open(altnum_count, 'r') as alt_count:
                    alt_cnt = alt_count.readline()
                    alt_count.close()
                if alt_cnt == '':
                    alt_cnt = '0'
                nft_num = str(alt_cnt).zfill(ALT_LEAD_ZEROS)
                num_out = str(int(alt_cnt) + 1)
                with open(altnum_count, 'w') as alt_cupd:
                    alt_cupd.write(num_out)
                    alt_cupd.close()
                nftname = NFT_ALT_NAME + nft_num
                nftlongname_display = NFT_ALT_LONG + ' #' + nft_num
            else:
                nft_num = nft_list.pop(nft_to_pop)
                with open(nftnum_list, 'w') as update_numlist:
                    update_numlist.write(','.join(nft_list))
                    update_numlist.close()
                nftname = nftbasename + nft_num
                nftlongname_display = nftlongname + ' #' + nft_num
            monk_gen = True
            try:
                monk_array = np.array(chosen_list, dtype=np.uint8)
                monk = Image.fromarray(monk_array, mode='RGBA')
                monk = monk.resize((tune_out_wh, tune_out_wh), resample=Image.NEAREST)
            except Exception:
                monk_gen = False
            if monk_gen is True:
                break

        # Create final output image
        out_image = Image.alpha_composite(out_canvass, monk)
        out_image = out_image.convert('RGB')
        imgfile = cache_dir + nftname + '.png'
        out_image.save(imgfile)

        # Pin image
        while True:
            if USE_PINATA is True:
                pinerr, ipfs_hash = pinnata(pn_key, pn_sec, {'file': open(imgfile, 'rb')})
            if USE_INFURA is True:
                pinerr, ipfs_hash = False, 'TESTHASH' #infura(pn_key, pn_sec, {'file': imgfile})
            if pinerr is False:
                ipfs_hash = 'ipfs://' + ipfs_hash
                break

        # Colour Swatch
        swatch_orig = list(swatch)
        for key, dab in enumerate(swatch):
            dl = list(dab)
            dl[3] = round(float(dl[3] / 255), 2)
            swatch[key] = tuple(dl)
        html = '<div style="margin:0 auto;width:380px;height:420px;text-align:center;background-color:rgba' + str(bg) + ';border-radius:32px;overflow:hidden;max-width:380px;min-height:420px;"><div style="height:320px;width:auto;margin:12px 4px 0 4px;position:relative;"><div class="nft"><img src="https://nftstorage.link/ipfs/' + ipfs_hash.split('://')[1] + '"></div><div class="swatch"><div style="display:block;width:100%;height:10%;background:#3e3e3e;font-family:arial;font-weight:bold;color:#d3d3d3;min-height:40px;line-height:40px;">CypherSwatch</div>'
        swatch_css = '<style>.swatch{display:block;width:90%;height:90%;min-height:320px;position:absolute;top:31px;left:19px;opacity:0;box-shadow:0 0 20px 3px #272727;transition:opacity 0.4s ease-in-out}.swatch:hover{opacity:1;transition:opacity 0.4s ease-in-out}[id^=swatch_colour]{display:block;width:33.33%;height:93.33px;float:left}[id^=swatch_colour]:hover{color:red}.nft>img{display:block;position:absolute;top:24px;left:5%;max-width:90%;}'
        for skey, si in enumerate(swatch):
            swatch_css += '#swatch_colour' + str(skey) + '{background:rgba' + str(si) + '}'
            html += '<div id="swatch_colour' + str(skey) + '" title="rgba' + str(swatch_orig[skey]) + '"></div>'
        swatch_css += '</style>'
        html += '</div></div></div>'
        html = swatch_css + html
        with open(cache_dir + 'htmlcache.html', 'w') as html_doc:
            html_doc.write(html)
            html_doc.close()
        encoded_html_json = json.dumps(encode_to_base64(cache_dir + 'htmlcache.html', 'html'))
        json_template = JSON_TEMP.replace('POLICY_ID', ' '.join(policy_id.split()))
        json_template = json_template.replace('NFT_NAME', ' '.join(nftname.split()))
        json_template = json_template.replace('NFT_LONG_NAME', ' '.join(nftlongname_display.split()))
        json_template = json_template.replace('ATT_LIST', ' '.join(att_list.split()))
        json_template = json_template.replace('NFT_RARITY', ' '.join(nft_rarity.split()))
        json_template = json_template.replace('IPFS_HASH', ' '.join(ipfs_hash.split()))
        if enable_html is True:
            json_template = json_template.replace('HTML_DATA', ' '.join(encoded_html_json.split()))
        # spectrum_list = [unique_log]
        if '|' in unique_log:
            unique_log_list = unique_log.split('|')
            out_spectrum = []
            for sitem in unique_log_list:
                out_spectrum += [str(sitem)]
        out_spectrum = json.dumps(out_spectrum)
        json_template = json_template.replace('SPECTRUM', ' '.join(out_spectrum.split()))
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

        # Data in & can return:
        tx_meta_json = input_data['payer_txmeta']
        mint_qty_int = input_data['qty_to_mint']

        # Process main plugin function
        return_err, action, return_txmeta, return_mintqty = do_plugin(settings, is_test, payer_hash, payer_addr, payer_ada, payer_return_ada, payer_asset_string, policy_id, tx_meta_json, mint_qty_int)
        return_data = {"err": return_err, "action": action, "tx_meta": return_txmeta, "mint_qty": return_mintqty}

    exit(json.dumps(return_data))
