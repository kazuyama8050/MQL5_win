import MetaTrader5 as mt5
import os,io,sys

current_script_path = os.path.abspath(__file__)
APP_HOME = os.path.abspath(os.path.join(current_script_path, ".."))
APP_DIR = os.path.abspath(os.path.join(current_script_path, "../.."))
PROJECT_DIR = os.path.abspath(os.path.join(current_script_path, "../../.."))

sys.path.append(os.path.join(APP_DIR, "model"))

from trade_history_model import TradeHistoryModel

class TradeHistoriesModel():
    def __init__(self):
        self._benefit_histories = []
        self._loss_histories = []
        self._min_margin_rate = 1000000000 ## ありえない値を初期値に

    def reset(self):
        self._benefit_histories = []
        self._loss_histories = []
        self._min_margin_rate = 1000000000 ## ありえない値を初期値に

    def add_benefit_trade(self, trade_history: TradeHistoryModel):
        self._benefit_histories.append(trade_history)

    def add_loss_trade(self, trade_history: TradeHistoryModel):
        self._loss_histories.append(trade_history)

    def check_and_replace_min_margin_rate(self, margin_rate):
        if self._min_margin_rate > margin_rate:
            self._min_margin_rate = margin_rate

    def get_benefit_histories(self):
        return self._benefit_histories
    
    def get_loss_histories(self):
        return self._loss_histories

    def get_min_margin_rate(self):
        return self._min_margin_rate