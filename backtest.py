
import matplotlib.pyplot as plt 
%matplotlib inline
import numpy as np 
import pandas as pd 
import time 
import requests 
import json
from datetime import datetime
import talib


def get_btcprice(ticker,max_):
    """
    [coingeckoのAPIからビットコインの価格データを取得する]
    
    引数
    ticker{str}: ティッカー(例：bitcoin、ethereum、ripple)
    max_{str}: 期間(例：max、14days)
    
    Return
    r2{json}:価格、出来高、市場全体の時価総額
    """
    
    url = 'https://api.coingecko.com/api/v3/coins/' + ticker + '/market_chart?vs_currency=jpy&days=' + max_
    r = requests.get(url)
    r2 = json.loads(r.text) 
    return r2


def reshape_pricedata(r2):
    """
    [jsonから価格データだけをPandasに変換して抽出する]
    
    引数
    r2{json}: get_btcprice()で取得したデータ
    
    Return
    data{dataframe}: データフレーム
    """

    data = pd.DataFrame(r2['prices'])
    data.columns = ['date','price']
    date = []
    for i in data['date']:
        tsdate = int(i / 1000)
        loc = datetime.utcfromtimestamp(tsdate)
        date.append(loc)
    data.index = date
    del data['date']
    return data


#ビットコインの全期間の価格データを取得する
r2 = get_btcprice('bitcoin', 'max')
btc = reshape_pricedata(r2)

# 変化率を計算する
change = btc['price'].pct_change()

# 変化率に1を足して累積変化率を計算する
trade_return = (change+1).cumprod()
trade_return[0] = 1

# 累積変化率の前後5日文を確認する
print(trade_return.head(),trade_return[-5:])

# 累積リターンの計算
from pylab import rcParams
import matplotlib as mpl

# フォントの設定
font = {"family":"Noto Sans CJK JP"}
mpl.rc('font', **font)
rcParams['figure.figsize'] = 15,5


def cal_backtest(price,mterm1=12,mterm2=26,mterm3=5,momterm=6):
    """
    [モメンタムとMacdを組み合わせたトレード戦略のリターンを計算する関数]
    
    mterm1{int} : macdの短期期間
    mterm2{int} : macdの長期期間
    mterm3{int} : macdの差分
    momterm{int} : モメンタムの計算期間
    
    [戻り値]
    trade_return{pdseries} : トレードパフォーマンスのホールドしていた場合との比較したデータフレーム
    
    """
    # 価格データをtalibで計算できるようにNumpyに変換
    numpyprice = np.array(price)
    
    # 変化率と累積変化率を計算
    change = price.pct_change()
    hold_return = (change + 1).cumprod()
    hold_return[0] = 1
    
    # テクニカル指標を計算
    momentum = talib.MOM(price, timeperiod=momterm)
    macd = talib.MACD(price, fastperiod=mterm1, slowperiod=mterm2, signalperiod=mterm3)
    # トレード戦略に基づいてトレードシグナルを計算(買い=1、売り=-1,ノーポジ=0)
    signal = []
    for i in range(len(price)):
        if momentum[i] > 0 and macd[2][i] > 0:
            signal.append(1)
        elif momentum[i] < 0 and macd[2][i] < 0 :
            signal.append(-1)
        else:
            signal.append(0)

    # 累積リターンの計算
    trade_returns = ((change[1:] * signal[:-1]) + 1).cumprod()
    
    # ホールドしていた場合とのリターンを比較するためにデータフレームを作成
    df = pd.DataFrame({'hold':hold_return,'trade':trade_returns})
    df3 = df.fillna(method='ffill')
    y1 = np.array(df3['hold'])
    y2 = np.array(df3['trade'])
    x = price.index[0:len(price)-1]
    return df3

# バックテストを実行
df = cal_backtest(btc['price'], mterm1=12, mterm2=26, mterm3=5, momterm=6)

# 比較結果をグラフにプロットする
plt.title('トレードリターンの比較')
plt.plot(df['hold'], 'b-', label='ホールドしてた場合のリターン', alpha=0.3, linewidth=1)
plt.plot(df['trade'], 'orange', label='MACD&モメンタムで取引した場合のリターン', alpha=1, linewidth=1.5)
plt.ylabel('倍率')
plt.grid(which='both')
plt.legend()

returns=[]
for i in range(2,20):
    for r in range(2,20):
        for e in range(5,25):
            for f in range(6,30):
                returns.append([cal_backtest(price,mterm1=e,mterm2=f,mterm3=int(i),momterm=int(r)),i,r,e,f])
                print(returns[-1])
ed=np.array(returns)


