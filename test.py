import time
import pyupbit
import datetime
import numpy as np
import pandas as pd

access = "16XeFrmbZx1i96loOuLnxrcqUKb1LPC9OZGhMrMF"
secret = "wxwNWtEgnVoc7vJxUi9mUou4M42gydZs0YxnUbWZ"

def get_balance(ticker):
    """잔고 조회"""
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == ticker:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0
    return 0    

def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(ticker=ticker)["orderbook_units"][0]["ask_price"]

def stochastic(data, k_window, d_window, window):
    min_val = data.rolling(window=window, center =False).min()
    max_val = data.rolling(window=window, center =False).max()
    stoch = ( (data-min_val)/(max_val -min_val))*100
    K = stoch.rolling(window=k_window, center=False).mean()
    D = K.rolling(window=d_window, center=False).mean()
    return K, D


# 로그인
upbit = pyupbit.Upbit(access, secret)
print("autotrade start")


# 자동매매 시작
status = 0

while True:
    try:
        if status == 0: # 아것도 매수 안했을 때 매수조건 찾기
    
            # 이동평균선 조회
            df = pyupbit.get_ohlcv("KRW-BTC", interval="minute30", count=25)
            df['ma5'] = df['close'].rolling(5).mean()
            df['ma15'] = df['close'].rolling(15).mean()

            pppre_ma15 = df['ma15'].iloc[-4] 
            pppre_ma5 = df['ma5'].iloc[-4] 
            pppre_dev = pppre_ma15 - pppre_ma5
            
            ppre_ma5 = df['ma5'].iloc[-3]
            ppre_ma15 = df['ma15'].iloc[-3]
            ppre_dev = ppre_ma15 - ppre_ma5

            pre_ma5 = df['ma5'].iloc[-2]
            pre_ma15 = df['ma15'].iloc[-2]
            pre_dev = pre_ma15 - pre_ma5

            now_ma5 = df['ma5'].iloc[-1]
            now_ma15 = df['ma15'].iloc[-1]
            now_dev = now_ma15 - now_ma5

            if pppre_dev > ppre_dev and ppre_dev > pre_dev:
                if pre_ma5 <= pre_ma15 and now_dev <= pre_dev*0.5:
                    while status == 0:
                        check = pyupbit.get_ohlcv("KRW-BTC", interval="minute1", count=30)
                        check['ma20'] = df['close'].rolling(20).mean()
                        krw = get_balance("KRW")
                        check_price = get_current_price("KRW-BTC")
                        if krw > 5000 and check_price < check['ma20'].iloc[-1]:
                            upbit.buy_market_order("KRW-BTC", krw*0.9995)
                            buy_price = get_current_price("KRW-BTC")
                            status = 1
                            print("buy_BTC")
                        elif check_price < pppre_dev:
                            break
                        
        elif status == 1:
            current_price = get_current_price("KRW-BTC")

            df = pyupbit.get_ohlcv("KRW-BTC", interval="minute30", count=200)
            delta = df['close'].diff(1)
            delta = delta.dropna()
            up = delta.copy()
            down = delta.copy()

            up[ up < 0 ] = 0
            down[ down > 0 ] = 0
            time_period = 14
            AVG_Gain = up.ewm(com=time_period-1, min_periods=time_period).mean()
            AVG_Loss = abs(down.ewm(com=time_period-1, min_periods=time_period).mean())
            RS = AVG_Gain / AVG_Loss
            RSI = 100.0 - (100.0/(1.0+RS))
            df['RSI'] = RSI
            df['K'], df['D'] = stochastic(df['RSI'], 5, 5,5)

            df['ma5'] = df['close'].rolling(5).mean()
            df['ma15'] = df['close'].rolling(15).mean()

            pre_ma5 = df['ma5'].iloc[-2]
            pre_ma20 = df['ma15'].iloc[-2]
            now_ma5 = df['ma5'].iloc[-1]
            now_ma20 = df['ma15'].iloc[-1]
            

            if current_price < buy_price*0.98:
                btc = get_balance("BTC")
                upbit.sell_market_order("KRW-BTC", btc*0.9995)
                print("SELL by -2%")
                status = 0
            elif df['RSI'].iloc[-1] < 70 and df['RSI'].iloc[-2] > 70: # 70이상 올라갔다가 꺾일 때
                btc = get_balance("BTC")
                upbit.sell_market_order("KRW-BTC", btc*0.9995)
                print("SELL due to RSI high")
                status = 0
            elif now_ma5 < pre_ma5 and now_ma5 <= now_ma20:
                btc = get_balance("BTC")
                upbit.sell_market_order("KRW-BTC", btc*0.9995)
                print("SELL_BTC")
                status = 0
            else:
                status = 1
        
        time.sleep(1)

    except Exception as e:
        print(e)
        time.sleep(1)
