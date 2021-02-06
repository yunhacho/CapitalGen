#!/usr/bin/env python
# coding: utf-8

# In[12]:


import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
from datetime import date, timedelta

from AboutTicker import *

'''
자동 로그인 방법
1)로그인 상태에서 윈도우 아래 ^ 아이콘에서 초록색 격자 박스 우클릭
2)계좌비밀번호 저장 (모의투자 계좌라면 0000) -> 등록 
3)AUTO 체크 -> 등록 버튼 다시 누르기 -> 닫기
4)코드 재실행하면 자동로그인 됨
'''


# In[13]:


class KiwoomOpenAPIwindow(QAxWidget):
    def __init__(self):
        super().__init__()
        self._create_kiwoom_instance()
        self._set_signal_slots()
        self._connect_to_OpenAPI()

    # 키움 OpenAPI+ 인스턴스 생성
    def _create_kiwoom_instance(self):
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")

    # 이벤트 처리 
    def _set_signal_slots(self):
        self._check_connect_status()
        self._check_connect_TR()
    
    # Open API 연결 및 로그인 윈도우 실행
    def _connect_to_OpenAPI(self):
        self.dynamicCall("CommConnect()")
        self.login_event_loop = QEventLoop() # 이벤트 루프 생성
        self.login_event_loop.exec_()
        '''
        GUI 로 만들지 않아서 이벤트 루프 생성해야한다.
        OnEventConnect 이벤트 발생할 때까지 루프돌면서 종료 안함
        '''
    # Open API 연결 및 로그인 여부 확인 이벤트 
    def _check_connect_status(self):
        self.OnEventConnect.connect(self.connect_status)
        
        '''
        통신 연결 상태 변경될 때 OnEventConnect 이벤트 발생
        발생한 이벤트 처리하기 위해 이벤트 처리 함수 필요
                OnEventConnect.connect(self.method) 
        이벤트 처리함수 self.method 와 OnEventConnect 자동 연결위해 connect 함수 사용
        OnEventConnect 의 리턴값이 self.method 의 인자로 들어가서 self.method 실행
        '''

    # Open API 연결 반환값 확인 
    def connect_status(self, errcode):
        if errcode==0:
            print('연결 성공')
        else: print('연결 실패')
        self.login_event_loop.exit() # 이벤트 처리해주면 루프 빠져나와야함

    # TR 이벤트 
    def _check_connect_TR(self):
        self.OnReceiveTrData.connect(self.receive_tr_data)

    # 시장구분에 다른 종목 코드 반환 
    def _get_codelist_by_market(self, market):
        ret=self.dynamicCall("GetCodeListByMarket(QString)", market).split(';')
        return ret[:-1]
    
    # 종목코드의 한글명 반환
    def _get_codename_by_code(self, code):
        return self.dynamicCall("GetMasterCodeName(QString)", code)

    # KOSPI, KOSDAQ 장내 기업 종목 코드 반환
    def _get_codelist_by_enterprise(self):
        enterpise=[]

        # 장내 + 코스닥 종목코드 합치기
        inmarket=self._get_codelist_by_market("0")
        inmarket.extend(self._get_codelist_by_market("10"))
        
        # 장내 종목에서 코스닥 제외한 시장구분 종목 제외
        for smarket in ["3", "4", "5", "6", "8", "9", "30"]:
            inmarket=set(inmarket)-set(self._get_codelist_by_market(smarket))
        
        # ETN 제외
        for code in inmarket:
            name=self._get_codename_by_code(code)
            if('ETN' not in name):
                enterpise.append(code)
        return enterpise

    # TR 입력 인자 설정
    def _set_input_value(self, id, value):
        self.dynamicCall("SetInputValue(QString, QString)", id, value)

    # TR을 서버로 송신
    def _communicate_req_data(self, rqname, trcode, next, screen):
        self.dynamicCall("CommRqData(QString, QString, int, QString)",rqname, trcode, next, screen)
        self.tr_event_loop=QEventLoop()
        self.tr_event_loop.exec_() # 이벤트 줄 때까지 대기 

    # TR 수신데이터 반환
    def _get_commnunicate_data(self,trcode, rqname, nindex, itemname):
        data=self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, nindex, itemname)
        return data

    # 레코드 반복횟수 반환
    def _get_repeat_cnt(self, trcode, rqname):
        return self.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)

    # TR 이벤트 처리 
    def receive_tr_data(self, screen, rqname, tickercode, recordname, next, unused1, unused2, unused3, unused4):
        if next=='2':
            self.remained_data = True
        else: self.remained_data = False

        if rqname == "opt10015_req":
            self.opt10015=self._opt10015(rqname, tickercode)
        
        try:  # 값 받아왔으면 루프 나옴 
            self.tr_event_loop.exit()
        except AttributeError:
            pass

    # 일별거래상세요청 TR 에서 기간중거래량 반환
    def _opt10015(self, rqname, tickercode):
        return self._get_commnunicate_data(tickercode, rqname, 0, "기간중거래량").strip()

    # 종목코드별 특정 일자 거래량 반환
    def _get_volume_by_ticker(self, next, screen, tickercode, yyyymmdd):
        self._set_input_value("종목코드", tickercode)
        self._set_input_value("시작일자", yyyymmdd)
        self._communicate_req_data("opt10015_req", "opt10015", next, screen)

        return self.opt10015


# In[ ]:



if __name__=="__main__":
    
    app=QApplication(sys.argv)
    kiwoom=KiwoomOpenAPIwindow()

    # 코스피, 코스닥 기업 종목코드 가져오기 (2382개)
    enterprises=kiwoom._get_codelist_by_enterprise()
    Date=date(2021,2,4).strftime('%Y%m%d')
    n=14
    
    tickers=get_tickers_top_volume_and_ATR(Date, n, enterprises)
    print(tickers)
    
    sys.exit(app.exec_())
    
    '''
    #전날 거래량 파악
    def get_yesterday():
        return datetime.strftime(datetime.now()-timedelta(1), '%Y%m%d')
        
    TR_REQ_TIME_INTERVAL = 2
    
    volumes=[]
    yesterday=get_yesterday()
    
    vol=kiwoom._get_volume_by_ticker(0, "0101", enterprises[0][0], yesterday)
    volumes.append((enterprises[0][0], vol))
    print(enterprises[0][0], vol)

    for trcode, name in enterprises[1:]:
        time.sleep(TR_REQ_TIME_INTERVAL)
        vol=kiwoom._get_volume_by_ticker(2, "0101", trcode, yesterday)
        volumes.append((trcode, vol))
        print(trcode, vol)
    '''
   


# In[ ]:




