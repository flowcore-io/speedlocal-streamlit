import os
import pandas as pd

# Sets root folder dependent on current directory
__file__ = 'main.py'
ROOT_DIR = os.path.dirname(os.path.realpath(__file__))
#INPUT_DIR = os.path.join(ROOT_DIR, 'Input')
#OUTPUT_DIR = os.path.join(ROOT_DIR, 'maps')
GEO_DIR = os.path.join(ROOT_DIR, 'Geojson')
#files = os.listdir(INPUT_DIR)

# Sheet name with all trades
sheet = "Internal Trade All - PJ"

# Name of the geojson file we will use for coordinates
geomap_name = 'NUTS_RG_01M_2021_3035.geojson'

# Countries at nuts_0
c_nuts0 = ['DE', 'PL', 'UK', 'NL', 'BE', 'LT', 'FI', 'CZ', 'SK', 'AT', 'FR', 'CH']
intCountries = ['DK', 'NO', 'SE', 'PL', 'DE']
extCountries = ['BE', 'UK', 'NL']
dic = {}
for x in c_nuts0:
    if x in intCountries:
        dic[x] = x + '1'
    else:
        dic[x] = x

# Countries at nuts_1
c_nuts1 = ['DE', 'PL']
# Countries at nuts_2
c_nuts2 = ['DK', 'NO', 'SE']

dkisl1 = 'DKISL1', 55.979076, 7.096848        # Latitude and longitude
dkisl2 = 'DKISL2', 56.068326, 6.603515
dkisl3 = 'DKISL3', 56.193403, 6.350176
deisl = 'DEISL', 55.136747, 6.205615
dkislbh= 'DKISLBH', 55.136895, 14.902472
GlobalMarket = 'Global Market', 65.108709, -1.337080
lst = [dkisl1, dkisl2, dkisl3, dkislbh, deisl, GlobalMarket]
energy_isl = pd.DataFrame(lst, columns=['id', 'lat', 'lon'])

