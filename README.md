# MintedWithLovelace-plugins

Plugins for the Minted DApp allow you to interrupt a minting process at the point before the dapp assembles the json files to mint for a particular incoming transaction. When a Plugin is activated for a campaign, Minted will attempt to run the plugin at this interrupt point, and will include setting and transaction information as json string input to the plugin. The plugin is expected to produce the required JSON files for minting, along with either the already-determined NFT count or a modified count, per the technicals outlined below.

This repository contains a template plugin file to utilize, which handles all the input/output required by Minted, found here: https://github.com/MadeWithLovelace/MintedWithLovelace-plugins/blob/main/pluginTemplate.py

### About Plugins
#### Plugin Should Expect...

There are two distinct input sets expected by Minted when it runs a plugin: --setup and --data. During configuration of a new campaign in Minted, if a plugin is activated, Minted will attempt to run that plugin's setup function to add any custom setting information. If none is required for your plugin, leave the setup section in the plugin unaltered. If you do need to setup some custom settings, add them as input prompts within the setup function and be sure to also add them to the do_plugin function for processing in real time...add them by the same names as dictionary items in do_plugin.

The --data option is for normal operation, to pass in data Minted is configured to pass in, as well as any custom settings you established. One setting which is added by Minted is "mwl_path", which is the absolute folderpath to the campaign's main folder (e.g. ~/.MintedWithLovelace/campaigns/THISCAMPAIGN/). 

Following are these two options and what Minted outputs to the plugin for each for reference:

--setup 
"{
  'campaign_name': YOURCAMPAIGNNAME,
  'minted_root': MWLFolderRoot (e.g. ~/.MintedWithLovelace)
}"

--data 
"{
    'settings': list-settings (pos=0 is the campaign base folder (e.g. ~/.MintedWithLovelace/campaigns/THISCAMPAIGN/), pos=1+ are custom settings
    'payer_hash': str'TXhashstring',
    'payer_addr': str'PayersAddress',
    'payer_ada': intADA-payed,
    'payer_asset_string': str'anyAssetsIncluded_as_a_string_withUnique_separators',
    'policy_id': str'CampaignPolicyID',
    'payer_txmeta': str'{json_of_tx_meta_if_any}',
    'qty_to_mint': intNumber_of_NFTs_to_Mint,
    'ada_to_return': intADA-to-return
}"


#### Minted expects...

For setup, Minted expects an output json string {"err": err_bool, "data": setting_prompts_list}, which is preformatted in the template so for most cases if developing a plugin, you will just need to output for the do_setup function, which expects to output just a list of any custom settings.

For normal operation, you will have 3 outputs and 1 file action expected. For the file action, your plugin is expected to place the appropriate JSON files for the NFTs to be minted for this particular payment. These files should be placed in the queued folder, the template plugin already has this code in the appropriate sections so all you need to note are the variable names for use in your code.

The do_plugin function should return: error status (True or False bool), the json meta data in string format...which if you are not watching for incoming txmeta or modifying it in any way, you can simply ignore this var and it will just pass through...and lastly the mint quantity integer, either modified per your plugin or just leave it as is and it will pass through.

### Additional Notes

For questions or support join the [MintedWithLovelace discord server](https://mintedwithlovelace.com).

#### Demo Plugins Available

Coming soon!

#### Project Specific Plugins

##### :: [CypherArtist](https://github.com/MadeWithLovelace/MintedWithLovelace-plugins/blob/main/cypherartist.py) ::

This plugin generates the NFT(s) in-real-time, deriving the colour pallette using the payer's Cardano stake key (shared portion of the address, linking all addresses in a wallet). Each NFT minted for a given wallet is also unique from each other, including arrangement of some colour elements and some pattern elements and some of both. The CypherArtist generates the art, uploads/pins/hashes it for IPFS, and generates the resultant JSON files, returned to Minted for minting to finalize.

### Notices

Copyright 2022 - MadeWithLovelace - All Rights Reserved

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
