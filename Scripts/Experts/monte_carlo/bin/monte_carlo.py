import MetaTrader5 as mt5
import os,io,sys,traceback
import time
from datetime import datetime, timedelta
import pandas as pd
import joblib

APP_NAME = "expert_monte_carlo"
current_script_path = os.path.abspath(__file__)
APP_HOME = os.path.abspath(os.path.join(current_script_path, ".."))
APP_DIR = os.path.abspath(os.path.join(current_script_path, "../.."))
PROJECT_DIR = os.path.abspath(os.path.join(current_script_path, "../../.."))

sys.path.append(os.path.join(PROJECT_DIR, "lib"))
sys.path.append(os.path.join(APP_DIR, "service"))
sys.path.append(os.path.join(APP_DIR, "model"))

from logger import Logger
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
model_conf.read(os.path.join(app_dir, "conf/monte_carlo_model.conf"))

def get_options():
    usage = "usage: %prog (Argument-1) [options]"
    parser = ArgumentParser(usage=usage)
    parser.add_argument("-s", "--symbol", dest="symbol", action="store", help="symbol", default="USDJPY", type=str)
    parser.add_argument("-t", "--train_term", dest="train_term", action="store", help="train_term", default="M1", type=str)
    parser.add_argument("-p", "--base_pips", dest="base_pips", action="store", help="base_pips", default=0.2, type=float)
    parser.add_argument("-l", "--base_lot", dest="base_lot", action="store", help="base_lot", default=0.01, type=float)
    parser.add_argument("-m", "--model_type", dest="model_type", action="store", help="model_type", default="decision_tree", type=str)
    parser.add_argument("-g", "--magic_number", dest="magic_number", action="store", help="magic_number", default=100000, type=int)
    parser.add_argument("-f", "--force_stopped_flag", dest="force_stopped_flag", action="store", help="force_stopped_flag", default=False, type=int)
    return parser.parse_args()

options = get_options()

ACCOUNT_ID = 75079798
ACCOUNT_PASS = "NTK2njaydu@"
SERVER = "XMTrading-MT5 3"
SYMBOL = options.symbol
BASE_PIPS = options.base_pips
BASE_LOT = options.base_lot
TRAIN_TERM = options.train_term
MAGIC_NUMBER = options.magic_number
FORCE_STOPPED_FLAG = options.force_stopped_flag
SLEEP_TIME = 5


model_types = {
    "decision_tree": "決定木",
    "random_forest": "ランダムフォレスト"
}
MODEL_TYPE = options.model_type

accountHandler = AccountHandler(ACCOUNT_ID, ACCOUNT_PASS, SERVER)
symbolHandler = SymbolHandler(SYMBOL)
tradeHandler = TradeHandler(Logger)
positionHandler = PositionHandler(SYMBOL, MAGIC_NUMBER)
monteCarloModel = MonteCarloModel(BASE_LOT)
monteCarloService = MonteCarloService(SYMBOL, BASE_PIPS, MAGIC_NUMBER)

positions = []  ## ポジション情報配列（分解モンテカルロ法による数列がリセットされるとリセット）
trained_model = None
tradeHistoriesModel = TradeHistoriesModel()


def main():
    try:
        if monteCarloModel.get_size() == 0: ## サイズが0の場合はリセット
            monteCarloModel.reset()
            if FORCE_STOPPED_FLAG == 1:
                logger.info("Monte Carlo Size is 0 and Force Stopped Flag On")
                return 1

        if monteCarloModel.get_size() == 1: ## サイズが1の場合は分解
            monteCarloModel.decompose()

        if symbolHandler.is_market_open() == False:  ## 市場が正常に開いていないときはスリープ
            time.sleep(60)
            return 1

        if positionHandler.get_position_size_by_symbol_magic() == 0:
            modelpath = model_conf.get(MODEL_TYPE, "modelpath")
            if MODEL_TYPE == "decision_tree":
                feature_df = _get_symbol_info_for_decision_tree_model()
                            
            order_request = monteCarloService.create_order_request(
                monteCarloService.calc_trade_flag(trained_model, feature_df),
                monteCarloModel.get_next_trade_lot(),
                ""
            )

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
        Logger.error("異常終了\n\n{}".format(traceback.format_exc()))
        return 0
    
def _get_symbol_info_for_decision_tree_model():
    moveing_history_term_list = model_conf.get(MODEL_TYPE, "moveing_history_term_list").split(",")
    moveing_average_term_list = model_conf.get(MODEL_TYPE, "moveing_average_term_list").split(",")
    bb_term_list = model_conf.get(MODEL_TYPE, "bb_term_list").split(",")
    bb_sigma_list = model_conf.get(MODEL_TYPE, "bb_sigma_list").split(",")
    macd_short_window_list = model_conf.get(MODEL_TYPE, "macd_short_window_list").split(",")
    macd_long_window_list = model_conf.get(MODEL_TYPE, "macd_long_window_list").split(",")
    macd_signal_window_list = model_conf.get(MODEL_TYPE, "macd_signal_window_list").split(",")
    
    symbol_prices = symbolHandler.get_prices_by_pos(SymbolHandler.get_mt5_timeframe(TRAIN_TERM), max(moveing_history_term_list)+1)
    symbol_price_df = pd.DataFrame(symbol_prices, columns=["close"])
    
    symbol_price_df = FeatureFormatterService.set_history_diff(symbol_price_df, moveing_history_term_list)
    symbol_price_df = FeatureFormatterService.set_moving_average_indicators(symbol_price_df, moveing_average_term_list)
    symbol_price_df = FeatureFormatterService.set_bb_indicators(symbol_price_df, bb_term_list, bb_sigma_list)
    symbol_price_df = FeatureFormatterService.set_macd_indicators(symbol_price_df, macd_short_window_list, macd_long_window_list, macd_signal_window_list)
    symbol_price_df.drop("close", axis=1, inplace=True)
    
    return symbol_price_df

def init():
    accountHandler.login()
    positions = []
    trained_model = joblib.load(modelpath)

try:
    mt5.initialize()
    Logger.notice("start expert {}".format(APP_NAME))
    
    init()

    replaced_day = datetime.now().day
    loop_cnt = 0
    while True:
        start_time = time.time()
        now = datetime.now()
        if main() == 0:
            break
        
        if loop_cnt % 100:
            margin_rate = mt5.account_info().margin
            tradeHistoriesModel.check_and_replace_min_margin_rate(margin_rate)

        if now.hour == 0 and now.minute == 0 and now.day != replaced_day:
            replaced_day = now.day
            monteCarloService.mail_daily_summary()

        loop_cnt += 1

        elapsed_time = time.time() - start_time
        if elapsed_time > SLEEP_TIME: time.sleep(SLEEP_TIME - elapsed_time)

    Logger.notice("shutdown expert {}".format(APP_NAME))
    mt5.shutdown()
except:
    mt5.shutdown()
    sys.exit()
