"""
@author: jshub

 data required bid & ask for option strikes
 
"""

#============== Required libraries=============
import math
import json
import pandas as pd
from datetime import datetime

#============== Script Constants===============
r1 = 7.14/100          #1 month Term MIBOR        Source: https://www.fbil.org.in/#/home
r2 = 7.35/100         # 3 Month Term MIBOR
N30 = 43200             # No. of minutes in 30 days
N365 = 525600           # No. of minutes in 365 day-year
twoStrikeDiff = 100    # 50 for Nifty, 100 for Bank Nifty

#======================== functions ============

def ASK_BID_CALC(orderbook_list):
    value = 0
    for i in range(0,len(orderbook_list),1):
        value = value + orderbook_list[i]["quantity"]
    return value

def EXPIRY_SELECTION(expiry_dates):
    date = expiry_dates[0]
    date = date + " 15:30"
    datetime_object = datetime.strptime(date, '%d-%b-%Y %H:%M')
    if (datetime_object - datetime.now()).days > 3 :
        nearTermExp = expiry_dates[0]
        nextMonthExp = expiry_dates[1]
    else:
        nearTermExp = expiry_dates[1]
        nextMonthExp = expiry_dates[2]
    return nearTermExp,nextMonthExp

def TIME_TO_EXP_CALC(expiry):
     expiry = expiry + " 15:30"
     value = ((datetime.strptime(expiry, '%d-%b-%Y %H:%M') - datetime.now()).total_seconds()/60)
     return value

def K0_CALC(F,strikeList):
    for i in strikeList:
        if i<F:
            break
    return i

def K_DELTA_CALC(row,data,k0,twoStrikeDiff):

    if (row["strikePrice"]==data.iloc[0]["strikePrice"]) or (row["strikePrice"]==data.iloc[-1]["strikePrice"]) or (row["strikePrice"]==k0):
        return twoStrikeDiff
    else:
        return (row["Next_Strike"] - row["Previous_Strike"])/2
    return 0     
        
def STRIKE_CONTRIBUTION_CALC(row,const):
    value = row["k_delta"]*row["Q"]*const/pow(row["strikePrice"],2)
    return value

def STRIKE_CONTRIBUTION_CALCULATION(r,data,expiry,minutes_to_exp,rate,twoStrikeDiff):
    T = minutes_to_exp/N365
    data = data.sort_values(by="strikePrice",ascending = False)
    strikeList = list(data["strikePrice"].unique())
    expiryDate = data["expiryDate"].unique()[0]
    dataList = r["stocks"]
    
    '''
    F price calculation as per NSE white paper
    '''
    data["diff"] = abs(data["ask"] - data["bid"])
    for i in range(0,len(dataList)):
        if((dataList[i]["metadata"]["instrumentType"]=="Index Futures") and (dataList[i]["metadata"]["expiryDate"]==expiryDate)):
           F = dataList[i]["metadata"]["lastPrice"]
    K0 = K0_CALC(F,strikeList)
    data.loc[data["strikePrice"]== K0,"strikeToKeep"] = 1
    data.loc[((data["optionType"]=="Call") & (data["strikePrice"]>K0)),"strikeToKeep"] = 1
    data.loc[((data["optionType"]=="Put") & (data["strikePrice"]<K0)),"strikeToKeep"] = 1
    data = data.dropna()
    data["sum"] = data["bid"].rolling(2).sum()
    try:
        if (data.loc[data["sum"]==0,"optionType"][0] == "Put"):
            data = data[data["strikePrice"]>data.loc[data["sum"]==0,"strikePrice"][0]]
        else:
            data = data[data["strikePrice"]<data.loc[data["sum"]==0,"strikePrice"][0]]
    except:
        pass
    data["Q"] = (data["bid"] + data["ask"])/2
    data.loc[((data["strikePrice"]==K0) & (data["optionType"]=="Call")),"Q"] = data[data["strikePrice"]==K0]["Q"].mean()
    data = data[~((data["strikePrice"]==K0) & (data["optionType"]=="Put"))]
    data["spread"] = abs(data["ask"] - data["bid"])/data["Q"]*100
    data = data.sort_values(by="strikePrice",ascending=True)
    # data = data.reset_index(drop = True)
    data['Previous_Strike'] = data['strikePrice'].shift(1)
    data['Next_Strike'] = data['strikePrice'].shift(-1)
    data["k_delta"] = data.apply(K_DELTA_CALC, args=(data,K0,twoStrikeDiff),axis = 1)

    const = math.exp(rate*T)
    data["contribution"] = data.apply(STRIKE_CONTRIBUTION_CALC,args=(const,),axis = 1)
    value = data["contribution"].sum()*2/T
    value = value - (1/T)*pow(F/K0-1,2)
    return value
    
    
    
def VIX_CALC(r):
    value = 0
    df = pd.DataFrame()
    # path = r"E:\Option chain\json\nifty50\futOi\2023-09-01--15-32-09.json"
    # path = r"E:\Option chain\json\bankNifty\futOi\2023-09-01--15-32-10.json"
    # with open(path) as json_file:
    #         r = json.load(json_file)
    expiry_dates = r["expiryDatesByInstrument"]["Index Futures"][0:3]
    nearTermExp,nextTermExp = EXPIRY_SELECTION(expiry_dates)
    t1 = TIME_TO_EXP_CALC(nearTermExp)
    t2 = TIME_TO_EXP_CALC(nextTermExp)
    spotValue = r["underlyingValue"]
    dataList = r["stocks"]
    dataList = [x for x in dataList if "Index Options" in x["metadata"]["instrumentType"]]
    # dataList = [x for x in dataList if  x["metadata"]["strikePrice"]<= spotValue]
    for i in range(0,len(dataList),1):
        data = dataList[i]
        optionType = data["metadata"]["optionType"]
        strikePrice = data["metadata"]["strikePrice"]
        expiryDate = data["metadata"]["expiryDate"]
        price = data["metadata"]["lastPrice"]
        ask = data["marketDeptOrderBook"]["ask"][0]["price"]
        bid = data["marketDeptOrderBook"]["bid"][0]["price"]
        # askQty = ASK_BID_CALC(data["marketDeptOrderBook"]["ask"])
        # bidQty = ASK_BID_CALC(data["marketDeptOrderBook"]["bid"])
        # impliedVolatility = data["marketDeptOrderBook"]["otherInfo"]["impliedVolatility"]
        # volume = data["metadata"]["numberOfContractsTraded"]
        temp = pd.DataFrame({"optionType":optionType,"strikePrice":strikePrice,"expiryDate":expiryDate,"ask":ask,"bid":bid,},index = [0])
        # temp = pd.DataFrame({"optionType":optionType,"strikePrice":strikePrice,"expiryDate":expiryDate,
        #                      "ask":ask,"bid":bid,"IV":impliedVolatility,"price":price,"volume":volume},index = [0])
        df = pd.concat([df,temp])
    nearTermData = df[df["expiryDate"]==nearTermExp]
    nextTermData = df[df["expiryDate"]==nextTermExp]
    sigma1 = STRIKE_CONTRIBUTION_CALCULATION(r,nearTermData,nearTermExp,t1,r1,twoStrikeDiff)
    sigma2 = STRIKE_CONTRIBUTION_CALCULATION(r,nextTermData,nextTermExp,t2,r2,twoStrikeDiff)
    
    value = ((t1/N365)*sigma1*((t2-N30)/(t2-t1)) + (t2/N365)*sigma2*((N30-t1)/(t2-t1)))*N365/N30
    value = round(math.sqrt(value)*100,3)
    return value
