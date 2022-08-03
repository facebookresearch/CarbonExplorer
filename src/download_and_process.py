# Copyright (c) Meta Platforms, Inc. and affiliates.
# This source code is licensed under the CC-BY-NC license found in the
# LICENSE file in the root directory of this source tree.

import wget
import zipfile
import pandas as pd
import math
import re
import numpy as np

# Download EIA's U.S. Electric System Operating Data
def downloadAndExtract(path):
    url = "https://api.eia.gov/bulk/EBA.zip"
    
    wget.download(url)
    
    # extract the data
    with zipfile.ZipFile("EBA.zip","r") as zip_ref:
        zip_ref.extractall(path)


# Split json into multiple csv's for manual analysis, view
#
def writeCSV(eba_json):
    numRecords = eba_json.shape[0]
    recordsPerFile = 100
    numFiles = math.ceil(numRecords / recordsPerFile)

    for i in range(numFiles):
        if i == numFiles - 1:
            r = range(recordsPerFile * i + 1, numRecords)
        else:
            r = range(recordsPerFile * i + 1, recordsPerFile * (i + 1))
        print("Writing csv records in {0}".format(r))
        df = eba_json.iloc[r, :]
        df.to_csv("{0}/EBA_sub_{1}.csv".format(EIA_bulk_data_dir,i))

eba_json = None
ba_list = []
ts_list = []

def prepareEIAData(EIA_data_path):
    global eba_json
    global ba_list
    global ts_list

    # EBA.txt includes time series for power generation from
    # each balancing authority in json format.
    #
    eba_json = pd.read_json("{0}/EBA.txt".format(EIA_data_path), lines=True)
    #writeCSV(eba_json)

    # Construct list of BAs (ba_list)
    # Construct list of time series (ts_list) using CISO as reference
    #
    series_id_unique = list(eba_json.series_id.unique())
    series_id_unique = list(filter(lambda x: type(x) == str, series_id_unique))
    
    ba_num = 0
    for sid in series_id_unique:
        m = re.search("EBA.(.+?)-", str(sid))
        ba_this = m.group(1)
        if ba_this not in ba_list:
            ba_list.append(ba_this)
            ba_num = ba_num + 1

        if ba_this == "CISO":
            m = re.search("EBA.CISO-([A-Z\-]+\.)([A-Z\.\-]*)", str(sid))
            ts_list.append(m.group(2))
    print("EIA data prep done!")

    return eba_json, ba_list, ts_list


# Energy types
ng_list = [
    "WND", # wind
    "SUN", # solar
    "WAT", # hydro
    "OIL", # oil
    "NG",  # natural gas
    "COL", # coal
    "NUC", # nuclear
    "OTH", # other
]

# Renewable energy types
rn_list = ["WND", "SUN", "WAT"]

# Carbon intensity of the energy types, gCO2eq/kWh
carbon_intensity = {
    "WND": 11,
    "SUN": 41,
    "WAT": 24,
    "OIL": 650,
    "NG":  490,
    "COL": 820,
    "NUC": 12,
    "OTH": 230,
}

# Construct dataframe from json
# Target specific balancing authority and day
def extractBARange(ba_idx, start_day, end_day): 
    global eba_json
    start_idx = pd.Timestamp('{0}T00Z'.format(start_day), tz='UTC')
    end_idx = pd.Timestamp('{0}T00Z'.format(end_day), tz='UTC')

    idx = pd.date_range(start_day, end_day, freq = "H", tz='UTC')

    # Loop over generating assets and append data to ba_list
    #
    ba_list = []

    for ng_idx in ng_list:
        # Target json for specific balancing authority. 
        # Note .H series means timestamps are in GMT / UTC 
        #
        series_idx = 'EBA.{0}-ALL.NG.{1}.H'.format(ba_idx, ng_idx)
        this_json = eba_json[eba_json['series_id'] == series_idx]
        this_json = this_json.reset_index(drop=True)
        if this_json.empty:
            #print('Dataset does not include {0} data'.format(ng_idx))
            ba_list.append([0]*(idx.shape[0])) # append a list with zeros
            continue

        # Check start/end dates for BA's json include target day
        #
        start_dat = pd.Timestamp(this_json['start'].reset_index(drop=True)[0])
        end_dat = pd.Timestamp(this_json['end'].reset_index(drop=True)[0])
        if (start_idx < start_dat):
            print('Indexed start ({0}) precedes {1} dataset range ({2})'.format(start_idx, ng_idx, start_dat))
            #continue

        if (end_idx > end_dat):
            print('Indexed end ({0}) beyond {1} dataset range ({2})'.format(end_idx, ng_idx, end_dat))
            #continue

        # Extract data tuples for target day
        # this_json['data'][0] is a list of items x = [date, MWh] tuples 
        #
        tuple_list = this_json['data'][0]
        tuple_filtered = list(filter(\
            lambda x: (pd.Timestamp(x[0]) >= start_idx) & (pd.Timestamp(x[0]) <= end_idx), \
            tuple_list))
        df = pd.DataFrame(tuple_filtered, columns =['timestamp', 'power'])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values(by=['timestamp'], ascending=(True))
        df.set_index(pd.DatetimeIndex(df['timestamp']), inplace=True)
        df.drop(columns=['timestamp'], inplace=True)
        df = df.reindex(index=idx, fill_value=0).reset_index()
        ba_list.append(df['power'].tolist())

    dfa = pd.DataFrame(np.array(ba_list).transpose(), columns=ng_list)
    dfa = dfa.set_index(idx)
    return dfa

# Calculate carbon intensity of the grid (kg CO2/MWh)
# Takes a dataframe of energy generation as input (i.e. output of extractBARange)
# Returns a time series of carbon intensity dataframe
def calculateAVGCarbonIntensity(db):
    tot_carbon = None
    db[db < 0] = 0
    sum_db = db.sum(axis=1)
    for c in carbon_intensity:
        if tot_carbon is None:
            tot_carbon = carbon_intensity[c]*db[c]
        else:
            tot_carbon = tot_carbon + carbon_intensity[c]*db[c]
    tot_carbon = tot_carbon.div(sum_db).to_frame()
    tot_carbon.rename(columns={tot_carbon.columns[0]: "carbon_intensity"}, inplace=True)
    return tot_carbon

