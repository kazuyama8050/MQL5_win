import MetaTrader5 as mt5
import os,io,sys,traceback
import time
from datetime import datetime, timedelta
import pandas as pd
import joblib
from argparse import ArgumentParser
import configparser
import socket
import asyncio
import threading

APP_NAME = "expert_monte_carlo"
current_script_path = os.path.abspath(__file__)
APP_HOME = os.path.abspath(os.path.join(current_script_path, ".."))
APP_DIR = os.path.abspath(os.path.join(current_script_path, "../.."))
PROJECT_DIR = os.path.abspath(os.path.join(current_script_path, "../../.."))

sys.path.append(os.path.join(PROJECT_DIR, "lib"))
sys.path.append(os.path.join(APP_DIR, "service"))
sys.path.append(os.path.join(APP_DIR, "model"))

from logger import Logger
from socket_handler import SocketHandler
from mail_handler import MailHandler
from account_handler import AccountHandler
from symbol_handler import SymbolHandler
from trade_handler import TradeHandler
from position_handler import PositionHandler
from position_model import PositionModel
from monte_carlo_model import MonteCarloModel
from trade_history_model import TradeHistoryModel
from trade_histories_model import TradeHistoriesModel
from monte_carlo_service import MonteCarloService
from feature_formatter_service import FeatureFormatterService

model_conf = configparser.ConfigParser()
model_conf.read(os.path.join(APP_DIR, "conf/monte_carlo_model.conf"))
conf = configparser.ConfigParser()
conf.read(os.path.join(APP_DIR, "conf/monte_carlo.conf"))

logger = Logger.get_logger(APP_DIR, APP_NAME)

def get_options():
    usage = "usage: %prog (Argument-1) [options]"
    parser = ArgumentParser(usage=usage)
    parser.add_argument("-s", "--symbol", dest="symbol", action="store", help="symbol", default="USDJPY", type=str)
    parser.add_argument("-t", "--train_term", dest="train_term", action="store", help="train_term", default="M1", type=str)
    parser.add_argument("-p", "--base_pips", dest="base_pips", action="store", help="base_pips", default=0.2, type=float)
    parser.add_argument("-l", "--base_lot", dest="base_lot", action="store", help="base_lot", default=0.01, type=float)
    parser.add_argument("-m", "--model_type", dest="model_type", action="store", help="model_type", default="decision_tree", type=str)
    parser.add_argument("-g", "--magic_number", dest="magic_number", action="store", help="magic_number", default=100000, type=int)
    parser.add_argument("-a", "--account_id", dest="account_id", action="store", help="account_id", required=True, type=int)
    parser.add_argument("-o", "--socket_port", dest="socket_port", action="store", help="socket_port", default=1024, type=int)
    return parser.parse_args()

options = get_options()

ACCOUNT_ID = options.account_id
ACCOUNT_PASS = input("Enter Password: ")
SERVER = "XMTrading-MT5 3"
SYMBOL = options.symbol
BASE_PIPS = options.base_pips
BASE_LOT = options.base_lot
TRAIN_TERM = options.train_term
MAGIC_NUMBER = options.magic_number
SOCKET_HOST = "127.0.0.1"
SOCKET_PORT = options.socket_port

SLEEP_TIME = 5


model_types = {
    "decision_tree": "決定木",
    "random_forest": "ランダムフォレスト"
}
MODEL_TYPE = options.model_type

accountHandler = AccountHandler(logger, ACCOUNT_ID, ACCOUNT_PASS, SERVER)
symbolHandler = SymbolHandler(SYMBOL)
tradeHandler = TradeHandler(logger)
positionHandler = PositionHandler(SYMBOL, MAGIC_NUMBER)
monteCarloModel = MonteCarloModel(BASE_LOT)
monteCarloService = MonteCarloService(SYMBOL, BASE_PIPS, MAGIC_NUMBER)

positions = []  ## ポジション情報配列（分解モンテカルロ法による数列がリセットされるとリセット）
trained_model = None  ## 機械学習モデル init()で定義
latest_symbol_timesec = None  ## シンボルの最新更新時間をもとに市場が開いているか判断する
force_stop_flag = False  ## Trueになるとポジション情報配列がなくなった場合にプロセスを終了する
tradeHistoriesModel = TradeHistoriesModel()


def main_process():
    global positions
    global latest_symbol_timesec

    try:
        symbol_timesec_now = symbolHandler.get_latest_time_msc()
        if latest_symbol_timesec >= symbol_timesec_now:  ## 価格が更新されていないときはスリープ
            time.sleep(5)
            return 1
        latest_symbol_timesec = symbol_timesec_now

        if monteCarloModel.get_size() == 0: ## サイズが0の場合はリセット
            monteCarloModel.reset()
            positions = []
            if force_stop_flag is True:
                logger.info("Monte Carlo Size is 0 and Force Stopped Flag On")
                return 0

        if monteCarloModel.get_size() == 1: ## サイズが1の場合は分解
            monteCarloModel.decompose()

        if positionHandler.get_position_size_by_symbol_magic() == 0:
            if MODEL_TYPE == "decision_tree":
                feature_df = _get_symbol_info_for_decision_tree_model()
            
            order_request = monteCarloService.create_order_request(
                monteCarloService.calc_trade_flag(trained_model, feature_df),
                monteCarloModel.get_next_trade_lot(),
                "ポジション取得"
            )
            logger.info("ポジション取得リクエスト送信")

            order_result = tradeHandler.order_request(order_request)
            if TradeHandler.is_market_closed(order_result.retcode):
                time.sleep(30)
                return 1

            if TradeHandler.is_order_success(order_result.retcode) is False:
                return 0
            
            positions.append(
                PositionModel(
                    order_result.order,
                    PositionModel.BUYING_FLAG if order_request["type"] == mt5.ORDER_TYPE_BUY else PositionModel.SELLING_FLAG, 
                    order_result.price,
                    order_result.volume
                )
            )
            return 1

        latest_position_ticket = positions[-1].get_ticket()
        latest_position_price = positions[-1].get_price()
        latest_position_trade_flag = positions[-1].get_trade_flag()
        latest_position_lot = positions[-1].get_lot()
        latest_price = symbolHandler.get_latest_bid() if latest_position_trade_flag == PositionModel.BUYING_FLAG else symbolHandler.get_latest_ask()
        
        is_settlement, is_benefit = monteCarloService.calc_settlement(latest_position_trade_flag, latest_price, latest_position_price)

        if is_settlement is True:
            settlement_request = monteCarloService.create_settlement_request(
                latest_position_ticket,
                PositionModel.reverse_trade_flag(latest_position_trade_flag),
                latest_position_lot,
                "利益点到達" if is_benefit else "損失点到達"
            )
            order_result = tradeHandler.order_request(settlement_request)
            logger.info("ポジション決済リクエスト送信")
            
            if TradeHandler.is_market_closed(order_result.retcode):
                time.sleep(30)
                return 1

            if TradeHandler.is_order_success(order_result.retcode) is False:
                return 0
            
            positions[-1].to_not_valid()
            position_deals = mt5.history_deals_get(position = latest_position_ticket)
            real_profit = position_deals[-1].profit
            tradeHistory = TradeHistoryModel(latest_position_ticket, latest_position_trade_flag, real_profit)
            
            if is_benefit == True:
                monteCarloModel.operate_by_benefit()
                tradeHistoriesModel.add_benefit_trade(tradeHistory)
            else:
                monteCarloModel.operate_by_loss()
                tradeHistoriesModel.add_loss_trade(tradeHistory)
            return 1

        return 1
    except Exception as e:
        raise Exception()
    
def _get_symbol_info_for_decision_tree_model():
    moveing_history_term_list = [int(x) for x in model_conf.get(MODEL_TYPE, "moveing_history_term_list").split(",")]
    moveing_average_term_list = [int(x) for x in model_conf.get(MODEL_TYPE, "moveing_average_term_list").split(",")]
    bb_term_list = [int(x) for x in model_conf.get(MODEL_TYPE, "bb_term_list").split(",")]
    bb_sigma_list = [int(x) for x in model_conf.get(MODEL_TYPE, "bb_sigma_list").split(",")]
    macd_short_window_list = [int(x) for x in model_conf.get(MODEL_TYPE, "macd_short_window_list").split(",")]
    macd_long_window_list = [int(x) for x in model_conf.get(MODEL_TYPE, "macd_long_window_list").split(",")]
    macd_signal_window_list = [int(x) for x in model_conf.get(MODEL_TYPE, "macd_signal_window_list").split(",")]
    symbol_prices = symbolHandler.get_prices_by_pos(SymbolHandler.get_mt5_timeframe(TRAIN_TERM), max(moveing_history_term_list)+1)
    symbol_price_df = pd.DataFrame(symbol_prices, columns=["close"])
    
    symbol_price_df, history_diff_columns = FeatureFormatterService.set_history_diff(symbol_price_df, moveing_history_term_list)
    symbol_price_df, ma_columns = FeatureFormatterService.set_moving_average_indicators(symbol_price_df, moveing_average_term_list)
    symbol_price_df, bb_columns = FeatureFormatterService.set_bb_indicators(symbol_price_df, bb_term_list, bb_sigma_list)
    symbol_price_df, macd_columns = FeatureFormatterService.set_macd_indicators(symbol_price_df, macd_short_window_list, macd_long_window_list, macd_signal_window_list)

    feature_columns = history_diff_columns + ma_columns + bb_columns + macd_columns
    feature_columns = sorted(feature_columns)
    symbol_price_df = symbol_price_df[feature_columns]
    return symbol_price_df.tail(1)

def init():
    global latest_symbol_timesec
    global trained_model
    global positions

    accountHandler.login()
        
    if symbolHandler.is_trade_mode_full() == False:
        logger.error("Symbol Trade Mode Invalid.")
        return 0
    
    latest_symbol_timesec = symbolHandler.get_latest_time_msc()
    
    positions = []

    logger.info("Read Trained Model Start.")
    modelpath = os.path.join(APP_DIR, model_conf.get(MODEL_TYPE, "modelpath").format(symbol=SYMBOL, term=TRAIN_TERM, base_pips=str(BASE_PIPS).replace(".", "")))
    trained_model = joblib.load(modelpath)
    logger.info("Read Trained Model Done.")

    return 1

def main_loop():
    replaced_day = datetime.now().day
    loop_cnt = 0
    while True:
        start_time = time.time()
        now = datetime.now()
        if main_process() == 0:
            break
        
        if loop_cnt % 100:
            margin_rate = mt5.account_info().margin
            tradeHistoriesModel.check_and_replace_min_margin_rate(margin_rate)

        ## 日次処理
        if now.hour == 0 and now.minute == 0 and now.day != replaced_day:
            replaced_day = now.day
            monteCarloService.mail_daily_summary(tradeHistoriesModel)

        loop_cnt += 1

        elapsed_time = time.time() - start_time
        if elapsed_time < SLEEP_TIME: time.sleep(SLEEP_TIME - elapsed_time)
        

def handle_socket_commands():
    global force_stop_flag
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((SOCKET_HOST, SOCKET_PORT))
    server_socket.listen(1)  # 1つの接続まで待ち受け
   
    while True:
        client_socket, client_address = server_socket.accept()
        command = client_socket.recv(1024).decode("utf-8")
        if not command:
            continue
        
        data = command.strip()
        if data == "force_stop":
            force_stop_flag = True
            logger.info("Force Stop Socket Command Receive.")
        else:
            logger.info("Invalid Socket Command Receive. {}".format(command))

        client_socket.close()


if __name__ == "__main__":
    try:
        mt5.initialize()
        logger.info("Start expert {}".format(APP_NAME))
        
        if init() == 0:
            raise Exception("Failed Init EA")
        
        server_thread = threading.Thread(target=handle_socket_commands, daemon=True)
        server_thread.start()

        main_loop()
        logger.info("shutdown expert {}".format(APP_NAME))
    except Exception as e:
        logger.error("異常終了\n{0}\n{1}".format(e, traceback.format_exc()))
        body_template = MailHandler.read_mail_body_template(conf.get("mail", "error_template_path"))
        ret = MailHandler.send_mail(
            "エラー発生のた異常終了",
            body_template.format(
                account=ACCOUNT_ID,
                trade_mode=AccountHandler.to_trade_mode_jp(mt5.account_info().trade_mode),
                expert_name=APP_NAME,
                symbol=SYMBOL,
                msg="異常終了\n{0}\n{1}".format(e, traceback.format_exc())
            )
        )
        if ret == 0:
            logger.error("エラーメール送信に失敗しました。")
    finally:
        mt5.shutdown()
        logger.info("End expert {}".format(APP_NAME))
        sys.exit()
