import json
from getopt import getopt
from sys import exit, argv


"""
NOTES:
This template is used to generate a MintedWithLovelace Plugin for use with the Minted dapp. To use, rename to whatever custom name you would like and add your main plugin code to the function "do_plugin" - you can also modify the function "do_settings" if you would like to add any custom configuration prompts which will save those settings and they will be accessible to your do_plugin function via the same order although in dictionary format.
"""


# Custom plugin-specific settings
def do_settings(campaign_name, minted_root):
    """
        Modify the following settings list by adding any custom setting prompt entries for saving settings for this plugin. They will be returned during operation in the same format as saved here. Passed in from Minted are the campaign name and root folder for Minted

        return [
            'Enter the number of NFTs for this custom setting:',
            'Enter the phrase to use for this custom setting:'
        ]
    """
    return []

# Customize plugin code
def do_plugin(settings, payer_hash, payer_addr, payer_ada, payer_return_ada, payer_asset_string, tx_meta_json, mint_qty_int):
    err_bool = False
    campaign_path = settings['mwl_path']
    json_file_list = []

    """
        Your custom plugin code goes here, you must return the data (either modified or unmodified depending on your plugin functionality): tx_meta_json, mint_qty_int, and json_file_list...take note of the expected type of each variable

        The file list returned must coincide with actual json files by those names within the Minted queueud folder for the campaign and network type.  For example, a return list for 4 json files named MyNFT01.json through MyNFT04.json, would expect those files to be in the campaign_path + 'minting/queued/' folder, and the return list would be: ['MyNFT01.json', 'MyNFT02.json', 'MyNFT03.json', 'MyNFT04.json']
    """
    return err_bool, tx_meta_json, mint_qty_int, json_file_list

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
        settings = do_settings(input_setup['campaign_name'], input_setup['minted_root'])
        out_print = {"err": False, "data": settings}

    if len(input_data) > 0:
        input_data = json.loads(input_data)

        # Data in:
        settings = input_data['settings']
        payer_hash = input_data['payer_hash']
        payer_addr = input_data['payer_addr']
        payer_ada = input_data['payer_ada']
        payer_return_ada = input_data['ada_to_return']
        payer_asset_string = input_data['payer_asset_string']

        # Data in & can return:
        tx_meta_json = input_data['payer_txmeta']
        mint_qty_int = input_data['qty_to_mint']

        # Process main plugin function
        return_err, return_txmeta, return_mintqty, return_jsonfiles = do_plugin(settings, payer_hash, payer_addr, payer_ada, payer_return_ada, payer_asset_string, tx_meta_json, mint_qty_int)
        out_print = {"err": return_err, "tx_meta": tx_meta_json, "mint_qty": mint_qty_int, "json_files": json_file_list}

    exit(json.dumps(out_print))
