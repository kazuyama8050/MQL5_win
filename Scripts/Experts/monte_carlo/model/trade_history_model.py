import MetaTrader5 as mt5
import os,io,sys

current_script_path = os.path.abspath(__file__)
APP_HOME = os.path.abspath(os.path.join(current_script_path, ".."))
APP_DIR = os.path.abspath(os.path.join(current_script_path, "../.."))
PROJECT_DIR = os.path.abspath(os.path.join(current_script_path, "../../.."))

sys.path.append(os.path.join(APP_DIR, "model"))

from position_model import PositionModel

class TradeHistoryModel():
    def __init__(self, position_ticket, trade_flag, profit):
        self._position_ticket = position_ticket
        self._trade_flag = trade_flag
        self._profit = profit

    def get_position_ticket(self):
        return self._position_ticket
    
    def get_trade_flag(self):
        return self._trade_flag
    
    def trade_flag_to_jp(self):
        trade_flag_jp = {
            PositionModel.BUYING_FLAG: "買い",
            PositionModel.SELLING_FLAG: "売り"
        }
        return trade_flag_jp[self.get_trade_flag()]
    
    def is_trade_flag_buying(self):
        return self._trade_flag == PositionModel.BUYING_FLAG

    
    def get_profit(self):
        return self._profit