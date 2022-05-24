# MintedWithLovelace-plugins

Plugins for the Minted DApp allow you to interrupt a minting process at the point before the dapp assembles the json files to mint for a particular incoming transaction. When a Plugin is activated for a campaign, Minted will attempt to run the plugin at this interrupt point, and will include setting and transaction information as json string input to the plugin. The plugin is expected to produce the required JSON files for minting, along with either the already-determined NFT count or a modified count, per the technicals outlined below.

This repository contains a template plugin file to utilize, which handles all the input/output required by Minted, found here: https://github.com/MadeWithLovelace/MintedWithLovelace-plugins/blob/main/pluginTemplate.py

### About Plugins
#### Plugin Should Expect...

There are two distinct input sets a plugin for Minted should expect input from: --setup and --data. During configuration of a new campaign in Minted, if a plugin is activated, Minted will attempt to run that plugin's setup function to add any custom setting information. If none is required for your plugin, leave the setup section in the plugin unaltered. If you do need to setup some custom settings, add them as input prompts within the setup function and be sure to also add them to the do_plugin function for processing in real time...add them by the same names as dictionary items in do_plugin.

The --data option is for normal operation, to pass in data Minted is configured to pass in, as well as any custom settings you established. One setting which is added by Minted is "mwl_path", which is the absolute folderpath to the campaign's main folder (e.g. ~/.MintedWithLovelace/campaigns/THISCAMPAIGN/). 

Following are these two options and what Minted outputs to the plugin for each for reference:

--setup 
"{
  'campaign_name': YOURCAMPAIGNNAME,
  'minted_root': MWLFolderRoot (e.g. ~/.MintedWithLovelace)
}"

--data 
"{
    'settings': list-settings (pos=0 is the campaign base folder (e.g. ~/.MintedWithLovelace/campaigns/THISCAMPAIGN/), pos=1+ are any added custom settings
    'is_test': bool,
    'payer_hash': str'TXhashstring',
    'payer_addr': str'PayersAddress',
    'payer_ada': intADA-received-in-payment,
    'ada_to_return': intADA-to-return
    'payer_asset_string': str'anyAssetsIncluded_as_a_string_withUnique_separators',
    'policy_id': str'CampaignPolicyID',
    'payer_txmeta': str'{json_of_tx_meta_if_any}',
    'qty_to_mint': intNumber_of_NFTs_to_Mint
}"


#### Minted Expected Returns

##### Setup returns...

For setup, Minted expects an output json string:

  {"err": true/false, "data": listSetting_prompts}

which is preformatted in the template so for most cases if developing a plugin, you will just need to output for the do_setup function, which expects to output just a list of any custom settings.

##### Normal/in-dapp operation returns...

For normal operation, you will have 3 outputs:

  {"err": true/false, "action": "mint/refund", "tx_meta": jsonstringTx_meta_json, "mint_qty": intToMintQty}

Your plugin should output any error boolean to the "err" similar to the setup returns. Second is the "action" return, which can be either "mint" or "refund". Next, "tx_meta" returns the TX Metadata which was passed into the plugin from Minted and altered in any way, if any at all. Minted will output either the discovered inbound TX Meta, to be then attached to the mint tx, or if "no-txmeta" is returned, Minted will ignore the tx-meta. This is handy especially if you expect tx-metadata to come in and want to deterministically filter which tx's should pass on the txmeta vs not pass it on (but perhaps use that data for the plugin only, for example). And lastly you can either pass the already-determined mint-qty to Minted or your plugin may alter that number for some reason, and you can return the new number. 

For the file action, your plugin is expected to place the appropriate JSON files for the NFTs to be minted for this particular payment it's processing, into the queued folder, which is mapped to a variable in the plugins template (see next section for more).  Of course, if you are returning the action "refund" you would not place any files in the queued folder.

#### Plugin Template
The [Minted Plugin Template](https://github.com/MadeWithLovelace/MintedWithLovelace-plugins/blob/main/pluginTemplate.py) allows you to easily create a custom Plugin compatible for use with Minted, with the following data passed and folders already made available to the plugin: 

Settings/Data Sent to Plugin:
```
  settings = A list of all custom settings, with the first 2 positions in the list preset to: 0 = campaign root directory (e.g. "~/.MintedWithLovelace/campaigns/YOURCAMPAIGNNAME/testnet/"); 1 = Your campaign name (e.g. MyCampaign). List positions 2 and up are populated with any custom settings you added to the setup function of the plugin.
  is_test = A boolean reflecting whether running on testnet (true = on testnet)
  payer_hash = This TX hash
  payer_addr = This TX payer Cardano address
  payer_ada = This TX incoming ADA amount represented in lovelace (35 ADA = 35000000)
  payer_return_ada = This is the amount of ADA, represented in lovelace, to be returned with the mint
  payer_asset_string = This TX wallet's assets owned, preceded by any assets included with this TX (feature coming soon)
  policy_id = This campaign minting Policy ID
  tx_meta_json = This TX metadata (if any)
  mint_qty_int = Number of NFTs to Mint to This Buyer (reflecting any adjustments already made by any Action Script)
```
Folders Already Available:
```
  campaign_path = your campaign path for the current network (test or main) (e.g. "~/.MintedWithLovelace/campaigns/YOURCAMPAIGN/testnet")
  queued = the queued folder for the current campaign/network (e.g. "~/.MintedWithLovelace/campaigns/YOURCAMPAIGNNAME/testnet/minting/auto/queued/")
  cache_dir = a custom cache folder for your plugin using your campaign name (e.g. "~/.MintedWithLovelace/plugins/cacheMyCampaign")
  scripts_dir = the Action Scripts directory for Minted, to make it easier to map to a scripts file if doing further conditions within your plugin
```

#### Demo and Live Usecase Plugins Available

Soon-to-launch Live Usecase :: [CypherMonks Generative "Live Artist" Plugin](https://github.com/MadeWithLovelace/MintedWithLovelace-plugins/blob/main/live-usecases/artistCypherMonks.py) ::

This plugin generates the NFT(s) in-real-time, deriving the colour pallette using the payer's Cardano stake key (shared portion of the address, linking all addresses in a wallet). Each NFT minted for a given wallet is also unique from each other, including arrangement of some colour elements and some pattern elements and some of both. The CypherArtist generates the art, uploads/pins/hashes it for IPFS, and generates the resultant JSON files, returned to Minted for minting to finalize.

### Additional Notes

For questions or support join the [MintedWithLovelace discord server](https://mintedwithlovelace.com).


### Notices

Copyright 2022 - MadeWithLovelace - All Rights Reserved

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
