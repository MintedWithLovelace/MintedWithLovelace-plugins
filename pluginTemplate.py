import json
from getopt import getopt
from sys import exit, argv


"""
NOTES:
This template is used to generate a MintedWithLovelace Plugin for use with the Minted dapp. To use, rename to whatever custom name you would like and add your main plugin code to the function "do_plugin" - you can also modify the function "do_settings" if you would like to add any custom configuration prompts which will save those settings and they will be accessible to your do_plugin function via the same order although in dictionary format.
"""


# Custom plugin-specific settings
def do_settings(campaign_name, campaign_root):
    cache_folder_name = 'my_plugin_cache'
    cache_dir = osjoin(osjoin(osjoin(campaign_root, 'plugin'), cache_folder_name), '')
    try:
        mkdir(cache_dir)
    except OSError:
        pass
    """
        Modify the following settings list by adding any custom setting prompt entries for saving settings for this plugin. They will be returned during operation in the same format as saved here. Passed in from Minted are the campaign name and root folder for Minted

        return [
            'Enter the number of NFTs for this custom setting:',
            'Enter the phrase to use for this custom setting:'
        ]
    """
    return []

# Customize plugin code
def do_plugin(settings, is_test, payer_hash, payer_addr, payer_ada, payer_return_ada, payer_asset_string, policy_id, tx_meta_json, mint_qty_int):
    err_bool = False
    action = 'mint'
    nettype = 'mainnet'
    if is_test is True:
        nettype = 'testnet'
    campaign_path = osjoin(osjoin(settings[0], nettype), '')
    queued = osjoin(osjoin(osjoin(osjoin(osjoin(campaign_path, 'minting'), ''), 'auto'), 'queued'), '')
    cache_dir = osjoin(osjoin(osjoin(dirname(dirname(dirname(dirname(campaign_path)))), 'plugins'), '_cache' + settings[1]), '')
    scripts_dir = osjoin(osjoin(dirname(dirname(dirname(dirname(campaign_path)))), 'scripts'), '')
    """
        Your custom plugin code goes here, you must return the data (either modified or unmodified depending on your plugin functionality): tx_meta_json and mint_qty_int...take note of the expected type of each variable. In addition Minted expects to find resultant JSON files in the queued folder, named according to the normal standard for Minted (e.g. MyNFT008.json .. or .. MyNFT8.json..etc depending on your naming schema)
    """
    return err_bool, action, payer_addr, tx_meta_json, mint_qty_int

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
        return_err, action, return_mint_at_addr, return_txmeta, return_mintqty = do_plugin(settings, is_test, payer_hash, payer_addr, payer_ada, payer_return_ada, payer_asset_string, policy_id, tx_meta_json, mint_qty_int)
        return_data = {"err": return_err, "action": action, "mint_at_addr": return_mint_at_addr, "tx_meta": return_txmeta, "mint_qty": return_mintqty}

    exit(json.dumps(return_data))
