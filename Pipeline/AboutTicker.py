#!/usr/bin/env python
# coding: utf-8

# In[2]:


from pykrx import stock
from datetime import datetime, timedelta, date
import pandas as pd
import math


# In[3]:


# 거래량 상위 500개 종목 반환
def get_top_volume_by_date(Date,ticker_list, top=500):
    '''
    파라미터: Date > "YYYYmmdd" 문자열 형식, 개장일 날짜로 보장되어야 함 
              ticker_list > 종목 코드(문자열 형식) 리스트
              top(default=500) > 거래량 상위로부터 top개 까지 반환
              
    date 날짜에 ticker_list 안 모든 종목에 대하여 
    거래량 상위 top개 종목코드 리스트 형태로 반환
    '''
    volumes=[]

    for ticker in ticker_list:
        vol=stock.get_market_ohlcv_by_date(Date, Date, ticker)
        
        if(len(vol.index)>0):
            volumes.append((ticker,vol['거래량'][0]))

    volumes.sort(key=lambda x: -x[1])
    
    return list(x[0] for x in volumes[0:top])


# In[4]:


# 개장일 기준 n+1일 전 날짜 반환
# n일 전 날짜 반환이 깔끔하지만, 이 함수는 ATR 계산에 사용되기때문에 
# 14ATR 은 15일 전날의 종가가 필요해서 n+1일 전 날짜 반환
def get_ndays_ago_from_date(Date, n):
    '''
    파라미터: date > "YYYYmmdd" 문자열 형식, 개장일 날짜로 보장되어야 함
              n > 조회할 n일 전. 정수 형식
    
    휴장일 제외 개장일 기준으로 date로 부터 n+1일 전 개장일  
    "YYYYmmdd" 문자열 형식으로 반환
    '''
    
    # 휴장일 조회는 나중에 정교화 필요 ....
    closeday20=pd.read_csv('2020_data.csv', sep=',')
    closeday21=pd.read_csv('2021_data.csv',sep=',')
    closeday=pd.concat([closeday20, closeday21], ignore_index=True)

    closeday=list(closeday['일자 및 요일'])

    day=date(int(Date[0:4]), int(Date[4:6]), int(Date[6:8]))

    nday=1
    while(nday!=n+1):
        ndays_ago = day - timedelta(1)
        
        if(ndays_ago.weekday()!=5 and ndays_ago.weekday()!=6):
            if(ndays_ago.isoformat() not in closeday):
                nday+=1
        day=ndays_ago
    
    return ndays_ago.strftime('%Y%m%d')


# In[5]:


# n ATR 반환
def get_n_ATR(Date, n, tickercode):
    '''
    파라미터: n > n ATR 의 n 입력. 정수 형태
              date > 조회할 날짜 "YYYYmmdd" 문자열 형태로 입력
                     개장일으로 보장되어야 함
              tickercode > 조회할 종목 코드 문자열 형태로 입력
              
    diff_today_hl= 오늘 고가-저가
    diff_yester_today_ch= 전일 종가-오늘 고가
    diff_yester_today_cl= 전일 종가-오늘 저가
    
    입력한 종목에 대하여 date 로 부터 n ATR 반환
    n+1 일의 데이터가 없으면 -1 반환
    '''
    
    nday = get_ndays_ago_from_date(Date, n)
    OHLCV= stock.get_market_ohlcv_by_date(nday, Date, tickercode)
     
    if(len(OHLCV.index)!=n+1):
        return -1
      
    ATR=0

    for i in range(n, 0, -1):
        ohlcv=OHLCV.iloc[i]
        prev_c=OHLCV.iloc[i-1]['종가']

        diff_today_hl=abs(ohlcv['고가']-ohlcv['저가'])
        diff_yester_today_ch= abs(prev_c-ohlcv['고가'])
        diff_yester_today_cl= abs(prev_c-ohlcv['저가'])

        TR = max(diff_today_hl, diff_yester_today_ch)
        TR = max(TR, diff_yester_today_cl)
    
        ATR+=TR
                                          
    ATR=ATR/n
    
    return(ATR)


# In[6]:


# nATR 의 상위 종목코드 반환
def get_top_nATR_by_date(Date, n, ticker_list, trimpoint=0.1, top=100):
    '''
    파라미터: Date > 조회할 날짜 "YYYYmmdd" 문자열 형태로 입력
                     개장일으로 보장되어야 함
              n > n일전까지 ATR 계산할 n. 정수 형태로 입력
              ticker_list > 조회할 종목 코드 문자열 리스트
              trimpoint(default=0.1) > 내림차순으로 정렬하였을 때
                          상위 trimpoint 까지는 절사할
                          필요 있기 때문에 절사할 범위 입력. 
                          0~1 까지의 실수가 보장되어야함
               top(default=100) > trimpoint 절사 후 그 다음부터 top개까지의 
                     상위 ATR 종목 반환.
                     입력하는 ticker_list의 개수가 trimpoint 절사 후에도 
                     top개는 남아있어야 함
    
    입력받은 ticker_list의 모든 종목에 대하여 Date 로 부터 n일 전 까지
    n ATR을 구한 후, 내림 차순으로 상위에서 trimpoint(ex.0.1=10%) 만큼
    절사 후, 다음 값으로 부터 top개의 [(종목코드, nATR) , ...] 리스트 반환
    '''
    
    ATR=[]
    for ticker in ticker_list:
        atr=get_n_ATR(Date, n, ticker)
        
        if(atr!=-1):
            ATR.append((ticker, atr))
            
    ATR.sort(key=lambda x: -x[1])
    
    trim=math.ceil(len(ATR)*trimpoint)

    ATR=ATR[trim:trim+top]
    
    
    return ATR


# In[7]:


# 거래량 상위 top 개 추출 후 trimpoint 까지 제거한 상위 nATR top개의 종목코드 반환
def get_tickers_top_volume_and_ATR(Date, n, ticker_list, top_volume=500,  atr_trimpoint=0.1, top_atr=100):
    '''
    파라미터: Date > 조회할 날짜 "YYYYmmdd" 문자열 형태로 입력.
                     개장일로 보장되어야함
              n > n일 전까지의 nATR을 구하기 위한 n. 정수 형태로 입력.
              ticker_list > 조회 대상이 되는 종목코드 리스트
              
              top_volume(default=500) > 거래량 상위 top_volume개 종목코드 반환 
              atr_trimpoint(default=0.1) > nATR 상위에서부터 trimpoint 까지 절사
              top_atr(default=100) > nATR top_atr 개 종목코드 반환
    '''
    
    volume_ticker_list = get_top_volume_by_date(Date, ticker_list, top_volume)
    atr_list = get_top_nATR_by_date(Date, n, volume_ticker_list, atr_trimpoint, top_atr)
    
    tickers=list(x[0] for x in atr_list)
    
    return tickers


# In[9]:


if __name__=="__main__":

    Date=date(2021,2,4).strftime('%Y%m%d')  # date.today().strftime('%Y%m%d') 개장일로 보장되어야 함
    n=14
    ticker_list=["005930"]
    
    tickers=get_tickers_top_volume_and_ATR(Date, n, ticker_list, 1, 0, 1)
    
    print(tickers)


# In[ ]:




