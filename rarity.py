import os
import glob
import json
import pathlib
import argparse
import traceback

import requests
import pandas as pd

from tqdm import tqdm
from multiprocessing import Pool, cpu_count

SAVE_PATH = 'base_rarity'
PARSE_STEP = 20
METADATA_PATH = None
RARITY_PATH = None


def download(download_arg):
    address, i = download_arg
    token_ids = list(range(i*PARSE_STEP, (i+1)*PARSE_STEP))

    # check if already downloaded
    if all([os.path.exists(os.path.join(METADATA_PATH, f"{x}.json")) for x in token_ids]):
        return False

    # download
    try:
        querystring = {"token_ids": token_ids,
                       "offset": "0",
                       "limit": "20",
                       "asset_contract_address": address}
        r = requests.get("https://api.opensea.io/api/v1/assets", params=querystring)
        js = r.json()
        if len(js['assets']) == 0:
            return True
        for asset in js['assets']:
            save_d = {"token_id": asset['token_id'], "traits": asset.get('traits', [])}
            with open(os.path.join(METADATA_PATH, f"{asset['token_id']}.json"), "w") as f:
                json.dump(save_d, f)
    except Exception as e:
        print("Exception", e, traceback.format_exc())
        return False


class Rarity:
    def __init__(self):
        self.metas = glob.glob(os.path.join(METADATA_PATH, "*"))

    def _calc_rarity(self, row):
        res = 0
        for c in self.trait_cols:
            if row[c] == -1:
                continue
            trait_count = self.traits_counter[c][row[c]]
            res += 1 / (trait_count / len(self.metas))
        return res

    def __call__(self):
        df = []
        for x in self.metas:
            js = json.load(open(x))
            d = {}
            for trait in js['traits']:
                d['trait_' + trait['trait_type']] = trait['value']
                d['token_id'] = int(os.path.split(x)[-1].split(".")[0])
            df.append(d)
        df = pd.DataFrame(df)
        df.fillna(-1, inplace=True)
        self.trait_cols = [x for x in df.columns if "trait_" in x]
        self.traits_counter = {}
        for c in self.trait_cols:
            self.traits_counter[c] = df.groupby(c).agg({"token_id": ['count']}).to_dict()[('token_id', 'count')]
        
        df['rarity_score'] = df.apply(lambda x: self._calc_rarity(x), axis=1)
        df = df.sort_values("rarity_score", ascending=False)
        df.to_csv(os.path.join(os.path.split(RARITY_PATH)[0], "rarity.csv"), index=False)
        print("df", df)
        for i, js in enumerate(df.to_dict('records')):
            with open(os.path.join(RARITY_PATH, f"{js['token_id']}.json"), "w") as f:
                js['rarity_place'] = i
                json.dump(js, f)


if __name__ == "__main__":
    print('START RARITY')
    parser = argparse.ArgumentParser()
    parser.add_argument('--contract', type=str, help='Address of contract, i.e. 0x34234...')
    parser.add_argument('--max_token_id', type=int, help='Max token id')
    args = parser.parse_args()

    # create dirs
    METADATA_PATH = os.path.join(SAVE_PATH, args.contract, "metadata")
    pathlib.Path(METADATA_PATH).mkdir(exist_ok=True, parents=True)
    RARITY_PATH = os.path.join(SAVE_PATH, args.contract, "rarity")
    pathlib.Path(RARITY_PATH).mkdir(exist_ok=True, parents=True)

    # calculate args
    N = args.max_token_id // PARSE_STEP + 1
    map_args = [(args.contract, i) for i in range(0, N)]

    # download in multiple treads will only work with proxies
    # pool = Pool(cpu_count())
    # download_func = partial(download)
    # results = pool.map(download_func, map_args)
    # pool.close()
    # pool.join()

    # download in 1 thread
    for arg in tqdm(map_args):
        is_last = download(arg)
        if is_last:
            break

    # get_rarity
    rarity = Rarity()
    rarity()
