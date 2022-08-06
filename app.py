import json
from flask import Flask, request
from binance.client import Client
from binance.enums import *
import os
import requests

app = Flask(__name__)

API_KEY = str(os.environ['API_KEY'])
API_SECRET = str(os.environ['API_SECRET'])
TEST_NET = bool(str(os.environ['TEST_NET']))
LINE_TOKEN=str(os.environ['LINE_TOKEN'])
BOT_NAME=str(os.environ['BOT_NAME'])
FREEBALANCE=str(os.environ['FREEBALANCE'])
SECRET_KEY=str(os.environ['SECRET_KEY'])

client = Client(API_KEY,API_SECRET,testnet=TEST_NET)

#STATIC API for testnet
#API_KEY = '3ebbe4c386be6fd911894b3b0b72c6f2026959e47e74ed9aa0ff8f676a04a9c3'
#API_SECRET = '4b060561fddd153b5367614e8427bb5fd2a5b312f1dc2fff830278ddf36ed18a'
#client = Client(API_KEY,API_SECRET,testnet=True)


url = 'https://notify-api.line.me/api/notify'
headers = {'content-type':'application/x-www-form-urlencoded','Authorization':'Bearer '+LINE_TOKEN}
#msg = 'Hello LINE Notify'
#r = requests.post(url, headers=headers, data = {'message':msg})
#print (r.text)

#print(API_KEY)
#print(API_SECRET)

@app.route("/")
def hello_world():
    return "AKNB2"

@app.route("/webhook", methods=['POST'])
def webhook():
    data = json.loads(request.data)
    print("decoding data...")
    action = data['side']
    amount = data['amount']
    symbol = data['symbol']
    passphrase = data['passphrase']
    lev = data['leverage']
    #separate amount type
    fiat=0
    usdt=0
    percent=0
    
    if amount[0]=='@':
        fiat=float(amount[1:len(amount)])
    if amount[0]=='$':
        usdt=float(amount[1:len(amount)])
    if amount[0]=='%':
        percent= float(amount[1:len(amount)])
    print(symbol, " : ",action," : amount=",amount," : leverage=" , lev)
    print('amount=',amount)
    print('fiat=',fiat)
    print('USDT=',usdt)
    print('Percent=',percent)
        
    COIN = symbol[0:len(symbol)-4] 

    bid = 0
    ask = 0
    usdt = float(usdt)
    lev = int(lev)
    
    bid = float(client.futures_orderbook_ticker(symbol =symbol)['bidPrice'])
    ask = float(client.futures_orderbook_ticker(symbol =symbol)['askPrice'])
        
    posiAmt = percent*float(client.futures_position_information(symbol=symbol)[0]['positionAmt'])/100
    print("100% Position amount>>",float(client.futures_position_information(symbol=symbol)[0]['positionAmt']))
    print(percent,"% Position amount>>", posiAmt )
    
    #List of action OpenLong=BUY, OpenShort=SELL, StopLossLong, StopLossShort, CloseLong=LongTP, CloseShort=ShortTP, CloseLong, CloseShort, 
    #OpenLong/BUY    
    if action == "OpenLong" and usdt>0:
        qty_precision = 0
        for j in client.futures_exchange_info()['symbols']:
            if j['symbol'] == symbol:
                qty_precision = int(j['quantityPrecision'])
        #check if buy in @ or fiat
        if amount[0]=='@':            
            fiat=float(amount[1:len(amount)])
            Qty_buy=round(fiat,qty_precision)
            usdt=round(fiat*bid,qty_precision)
            print("BUY/LONG by @ amount=", fiat, " ", COIN, ">> USDT=",round(usdt,3))
        if amount[0]=='$':
            usdt=float(amount[1:len(amount)])
            Qty_buy = round(usdt/bid,qty_precision)
            print("BUY/LONG by USDT amount=", usdt, ">> COIN", round(usdt,30))
        print("CF>>", symbol,">>",action, ">>Qty=",Qty_buy, " ", COIN,">>USDT=", round(usdt,3))
        Qty_buy = round(Qty_buy,qty_precision)
        print('qty buy : ',Qty_buy)
        client.futures_change_leverage(symbol=symbol,leverage=lev)
        print('leverage : ',lev)
        order_BUY = client.futures_create_order(symbol=symbol, side='BUY', type='MARKET', quantity=Qty_buy)
        print(symbol," : BUY")
        #success openlong, push line notification        
        msg ="BINANCE:\n" + "BOT       :" + BOT_NAME + "\nCoin       :" + COIN + "/USDT" + "\nStatus    :" + action + "[BUY]" + "\nAmount  :" + str(Qty_buy) + " "+  COIN +"/"+str(usdt)+" USDT" + "\nPrice       :" + str(bid) + " USDT" + "\nLeverage:" + str(lev) + "\nPaid        :" + str(round(usdt/lev,3)) + " USDT"
        r = requests.post(url, headers=headers, data = {'message':msg})
        
    #OpenShort/SELL
    if action == "OpenShort" and usdt > 0:        
        qty_precision = 0
        for j in client.futures_exchange_info()['symbols']:
            if j['symbol'] == symbol:
                qty_precision = int(j['quantityPrecision'])
        #check if sell in @ or fiat
        if amount[0]=='@':            
            fiat=float(amount[1:len(amount)])
            Qty_sell=round(fiat,qty_precision)
            usdt=round(fiat*ask,qty_precision)
            print("SELL/SHORT by @ amount=", fiat, " ", COIN, ">> USDT=",round(usdt,3))
        if amount[0]=='$':
            usdt=float(amount[1:len(amount)])
            Qty_sell = round(usdt/ask,qty_precision)
            print("SELL/SHORT by USDT amount=", usdt, ">> COIN", round(usdt,30))
        print("CF>>", symbol,">>", action, ">> Qty=", Qty_sell, " ", COIN,">>USDT=", round(usdt,3))
        Qty_sell = round(Qty_sell,qty_precision)
        print('qty sell : ',Qty_sell)
        client.futures_change_leverage(symbol=symbol,leverage=lev)
        print('leverage : ',lev)
        order_SELL = client.futures_create_order(symbol=symbol, side='SELL', type='MARKET', quantity=Qty_sell)
        print(symbol,": SELL")
        #success openshort, push line notification        
        msg ="BINANCE:\n" + "BOT       :" + BOT_NAME + "\nCoin       :" + COIN + "/USDT" + "\nStatus    :" + action + "[SHORT]" + "\nAmount  :" + str(Qty_sell) + " "+  COIN +"/"+str(usdt)+" USDT" + "\nPrice       :" + str(bid) + " USDT" + "\nLeverage:" + str(lev) + "\nPaid        :" + str(round(usdt/lev,3)) + " USDT"
        r = requests.post(url, headers=headers, data = {'message':msg})

        
    if action == "CloseLong":
        if posiAmt > 0.0 :
            qty_precision = 0
            for j in client.futures_exchange_info()['symbols']:
                if j['symbol'] == symbol:
                    qty_precision = int(j['quantityPrecision'])
            print("qty_precision",qty_precision)
            #check if sell in % or $
            if amount[0]=='%':            
                qty_close=round(posiAmt,qty_precision)                
                usdt=round(qty_close*ask,qty_precision)                
                print("SELL/CloseLong by % amount=", qty_close, " ", COIN, ">> USDT=",round(usdt,3))
            if amount[0]=='$':
                usdt=float(amount[1:len(amount)])                
                qty_close = round(usdt/ask,qty_precision)                
                print("SELL/CloseLong by USDT amount=", usdt, ">> COIN", round(usdt*qty_close,30))
            print("CF>>", symbol,">>", action, ">> Qty=", qty_close, " ", COIN,">>USDT=", round(usdt,3))                    
            #qty_close = float(client.futures_position_information(symbol=symbol)[0]['positionAmt'])            
            close_BUY = client.futures_create_order(symbol=symbol, side='SELL', type='MARKET', quantity=qty_close)
            #success close sell, push line notification        
            msg ="BINANCE:\n" + "BOT       :" + BOT_NAME + "\nCoin       :" + COIN + "/USDT" + "\nStatus    :" + action + "[SELL]" + "\nAmount  :" + str(qty_close) + " "+  COIN +"/"+str(round((qty_close*bid),3))+" USDT" + "\nPrice       :" + str(ask) + " USDT" + "\nLeverage:" + str(lev) + "\nReceive     :" + str(round((qty_close*bid/lev),3)) + " USDT"
            r = requests.post(url, headers=headers, data = {'message':msg})
            print(symbol,": CloseLong")

    if action == "CloseShort":
        if posiAmt < 0.0 :
            qty_precision = 0
            for j in client.futures_exchange_info()['symbols']:
                if j['symbol'] == symbol:
                    qty_precision = int(j['quantityPrecision'])
            #check if buy in @ or fiat
            if amount[0]=='%':            
                qty_close=round(posiAmt,qty_precision)
                usdt=round(qty_close*bid,qty_precision)
                print("BUY/CloseShort by % amount=", qty_close, " ", COIN, ">> USDT=",round(qty_close*usdt,3))
            if amount[0]=='$':
                usdt=float(amount[1:len(amount)])
                qty_close = round(usdt/bid,qty_precision)
                print("BUY/CloseShort by USDT amount=", usdt, ">> COIN", round(qty_close,3))
            print("CF>>", symbol,">>",action, ">>Qty=",qty_close, " ", COIN,">>USDT=", round(usdt,3))
            #qty_close = float(client.futures_position_information(symbol=symbol)[0]['positionAmt'])
            close_SELL = client.futures_create_order(symbol=symbol, side='BUY', type='MARKET', quantity=qty_close*-1)            
            #success close buy, push line notification        
            msg ="BINANCE:\n" + "BOT       :" + BOT_NAME + "\nCoin       :" + COIN + "/USDT" + "\nStatus    :" + action + "[BUY]" + "\nAmount  :" + str(qty_close*-1) + " "+  COIN +"/"+str(round((qty_close*ask*-1),3))+" USDT" + "\nPrice       :" + str(ask) + " USDT" + "\nLeverage:" + str(lev) + "\nReceive     :" + str(round((qty_close*ask*-1/lev),3)) + " USDT"
            r = requests.post(url, headers=headers, data = {'message':msg})
            print(symbol,": CloseShort")
            
    if action == "test":
        print("TEST!")
        msg ="BINANCE:\n" + "BOT       :" + BOT_NAME + "\nTest.."
        r = requests.post(url, headers=headers, data = {'message':msg})        
    
    print("---------------------------------")

    return {
        "code" : "success",
        "message" : data
    }

if __name__ == '__main__':
    app.run(debug=True)
