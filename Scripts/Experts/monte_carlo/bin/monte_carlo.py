import MetaTrader5 as mt5
import os,io,sys,traceback
import time
from datetime import datetime, timedelta

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

ACCOUNT_ID = 75079798
ACCOUNT_PASS = "NTK2njaydu@"
SERVER = "XMTrading-MT5 3"
SYMBOL = "USDJPY"
BASE_PIPS = 0.02
BASE_LOT = 0.01
MAGIC_NUMBER = 100000
SLEEP_TIME = 5

accountHandler = AccountHandler(ACCOUNT_ID, ACCOUNT_PASS, SERVER)
symbolHandler = SymbolHandler(SYMBOL)
tradeHandler = TradeHandler(Logger)
positionHandler = PositionHandler(SYMBOL, MAGIC_NUMBER)
monteCarloModel = MonteCarloModel(BASE_LOT)
monteCarloService = MonteCarloService(SYMBOL, BASE_PIPS, MAGIC_NUMBER)

positions = []  ## ポジション情報配列（分解モンテカルロ法による数列がリセットされるとリセット）
tradeHistoriesModel = TradeHistoriesModel()


def main():
    try:
        if monteCarloModel.get_size() == 0: ## サイズが0の場合はリセット
            monteCarloModel.reset()

        if monteCarloModel.get_size() == 1: ## サイズが1の場合は分解
            monteCarloModel.decompose()

        if symbolHandler.is_market_open() == False:  ## 市場が正常に開いていないときはスリープ
            time.sleep(60)
            return 1

        if positionHandler.get_position_size_by_symbol_magic() == 0:
            order_request = monteCarloService.create_order_request(
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

def init():
    accountHandler.login()
    positions = []
    print(mt5.symbol_info_tick(SYMBOL))

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
