import warnings
import MetaTrader5 as mt5
import requests
import time
import schedule
from argparse import ArgumentParser
from settings import *
from requests.auth import HTTPBasicAuth
warnings.filterwarnings('ignore')

def get_prediction():

    req = requests.get(url+'/login', auth=HTTPBasicAuth(username, password)).json()
    token = req['token']
    headers = {
    "x-access-token": token
    }
    req = requests.get(url+'/prediction', headers=headers).json()
    return req['prediction_data']['prediction']

def make_request(volume, direction, deviation, symbol, magic):
       
    if direction == 'long':
        order_type = mt5.ORDER_TYPE_BUY
    elif direction == 'short':
        order_type = mt5.ORDER_TYPE_SELL
    else:
        print('Invalid order type')
    
    request = {
    'action': mt5.TRADE_ACTION_DEAL,
    'symbol': symbol,
    'volume': volume,
    'type': order_type,
    'price': mt5.symbol_info_tick(symbol).ask,
    'deviation': deviation,
    'magic': magic,
    'comment': 'Order type: ' + direction,
    'type_time': mt5.ORDER_TIME_GTC,
    'type_filling': mt5.ORDER_FILLING_FOK
    }
    return mt5.order_send(request)


def send_order(result):
    position_id=result.order
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print("Order_send failed, retcode={}".format(result.retcode))
        print("Result",result)
    else:
        print("Position #{} closed, {}".format(position_id,result))
        result_dict=result._asdict()
        for field in result_dict.keys():
            print("   {}={}".format(field,result_dict[field]))
            if field=="request":
                traderequest_dict=result_dict[field]._asdict()
                for tradereq_filed in traderequest_dict:
                    print("       traderequest: {}={}".format(tradereq_filed,traderequest_dict[tradereq_filed]))


def init_mt5():
    if not mt5.initialize(
        path=path,
        login=mt5_account,
        password=mt5_password,
        server=mt5_server
        ):

        print("initialize() failed, error code =",mt5.last_error())
        mt5.shutdown()


def close_positions():
    init_mt5()  
    positions=mt5.positions_get(symbol=symbol)
    
    if len(positions)>0:
        for position in positions:
            if position.type == 0:
                direction = 'short'
                req = make_request(volume, direction, deviation, symbol, magic)
                send_order(req)
            elif position.type == 1:
                direction = 'long'
                req = make_request(volume, direction, deviation, symbol, magic)
                send_order(req)
            else:
                pass


def job():
    init_mt5()
    positions=mt5.positions_get(symbol=symbol)
    
    if positions==():
        direction = get_prediction()
        req = make_request(volume, direction, deviation, symbol, magic)
        send_order(req)

    elif len(positions)>0:
        for position in positions:
            direction = get_prediction() 
            if direction == 'long' and position.type == 1:              
                direction = 'long'
                req = make_request(volume, direction, deviation, symbol, magic)
                send_order(req)
                req = make_request(volume, direction, deviation, symbol, magic)
                send_order(req)                
            elif direction == 'short' and position.type == 0:
                direction = 'short'
                req = make_request(volume, direction, deviation, symbol, magic)
                send_order(req)
                req = make_request(volume, direction, deviation, symbol, magic)
                send_order(req)


schedule.every().day.at(hour_1).do(job)
schedule.every().day.at(hour_2).do(job)
schedule.every().day.at(hour_3).do(job)
schedule.every().day.at(hour_4).do(job)
schedule.every().day.at(hour_5).do(job)
schedule.every().day.at(hour_6).do(job)
schedule.every().day.at(hour_7).do(job)
schedule.every().day.at(hour_8).do(job)
schedule.every().day.at(close_trades).do(close_positions)


while True:
    schedule.run_pending()
    time.sleep(1)