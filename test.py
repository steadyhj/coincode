import time
import pyupbit
import datetime

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

# 로그인
upbit = pyupbit.Upbit(access, secret)
print("autotrade start")


# 자동매매 시작
status = 0

while True:
    try:
        if status == 0: # 아것도 매수 안했을 때 매수조건 찾기
    
            # 이동평균선 조회
            df = pyupbit.get_ohlcv("KRW-BTC", interval="minute30", count=50)
            df['ma5'] = df['close'].rolling(5).mean()
            df['ma20'] = df['close'].rolling(20).mean()

            pre_ma5 = df['ma5'].iloc[-2]
            pre_ma20 = df['ma20'].iloc[-2]
            now_ma5 = df['ma5'].iloc[-1]
            now_ma20 = df['ma20'].iloc[-1]
            

            if pre_ma5 < pre_ma20 and now_ma5 >= now_ma20:
                krw = get_balance("KRW")
                if krw > 5000:
                    upbit.buy_market_order("KRW-BTC", krw*0.9995)
                    buy_price = get_current_price("KRW-BTC")
                    status = 1
                    time.sleep(1800)

        elif status == 1:
            current_price = get_current_price("KRW-BTC")
            df = pyupbit.get_ohlcv("KRW-BTC", interval="minute30", count=50)
            df['ma5'] = df['close'].rolling(5).mean()
            df['ma20'] = df['close'].rolling(20).mean()

            pre_ma5 = df['ma5'].iloc[-2]
            pre_ma20 = df['ma20'].iloc[-2]
            now_ma5 = df['ma5'].iloc[-1]
            now_ma20 = df['ma20'].iloc[-1]
            

            if current_price < buy_price:
                btc = get_balance("BTC")
                upbit.sell_market_order("KRW-BTC", btc*0.9995)
                status = 0
            elif now_ma5 < now_ma20:
                btc = get_balance("BTC")
                upbit.sell_market_order("KRW-BTC", btc*0.9995)
                status = 0
            elif now_ma5 < pre_ma5 and now_ma5 < now_ma20:
                btc = get_balance("BTC")
                upbit.sell_market_order("KRW-BTC", btc*0.9995)
                status = 0
            elif current_price < df['close'].iloc[-1] and df['close'].iloc[-1] <= df['open'].iloc[-2]:  
                btc = get_balance("BTC")
                upbit.sell_market_order("KRW-BTC", btc*0.9995)
            else:
                status = 1
        
        time.sleep(180)

    except Exception as e:
        print(e)
        time.sleep(1)
