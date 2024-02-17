"""
@author: jshub

 data required bid & ask for option strikes
 
"""

#============== Required libraries=============
import math
import json
import requests
import pandas as pd
from datetime import datetime

from utils import *

url =  "https://www.nseindia.com/api/quote-derivative?symbol=BANKNIFTY"   # change this URL for  other NSE Indices

headers={'user-agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36',
         'accept-language':'en-US,en;q=0.9,bn;q=0.8','accept-encoding':'gzip, deflate, br'}
r=requests.get(url,headers=headers).json()

vix = VIX_CALC(r)
