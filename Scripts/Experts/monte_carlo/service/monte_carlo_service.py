import MetaTrader5 as mt5
import os,io,sys
from datetime import datetime, timedelta

current_script_path = os.path.abspath(__file__)
APP_HOME = os.path.abspath(os.path.join(current_script_path, ".."))
APP_DIR = os.path.abspath(os.path.join(current_script_path, "../.."))
PROJECT_DIR = os.path.abspath(os.path.join(current_script_path, "../../.."))

sys.path.append(os.path.join(PROJECT_DIR, "lib"))
sys.path.append(os.path.join(APP_DIR, "model"))

from mail_handler import MailHandler
from symbol_handler import SymbolHandler
from position_model import PositionModel
from trade_history_model import TradeHistoryModel
from trade_histories_model import TradeHistoriesModel

class MonteCarloService():
    def __init__(self, symbol, base_pips, magic_number):
        self._symbol = symbol
        self._base_pips = base_pips
        self._magic_number = magic_number
        self._symbolHandler = SymbolHandler(self._symbol)

    def calc_trade_flag(self, model, feature_df):
        pred = model.predict(feature_df)
        return PositionModel.BUYING_FLAG if pred >= 0.5 else PositionModel.SELLING_FLAG
    
    def calc_settlement(self, latest_position_trade_flag: int, latest_price: float, latest_position_price: float):
        is_settlement = False
        is_benefit = False
        if latest_position_trade_flag == PositionModel.BUYING_FLAG:
           if latest_price - latest_position_price >= self._base_pips:
               is_settlement = True
               is_benefit = True
           elif latest_position_price - latest_price >= self._base_pips:
               is_settlement = True
               is_benefit = False
        elif latest_position_trade_flag == PositionModel.SELLING_FLAG:
            if latest_position_price - latest_price >= self._base_pips:
                is_settlement = True
                is_benefit = True
            elif latest_price - latest_position_price >= self._base_pips:
                is_settlement = True
                is_benefit = False

        return is_settlement, is_benefit
    
    def create_order_request(self, trade_flag: int, lot: int, comment: str):
        order_type = mt5.ORDER_TYPE_BUY if trade_flag == PositionModel.BUYING_FLAG else mt5.ORDER_TYPE_SELL
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": self._symbol,
            "volume": lot,
            "type": order_type,
            "magic": self._magic_number,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_DAY,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        return request
    
    def create_settlement_request(self, position_ticket: int, trade_flag: int, lot: int, comment: str):
        order_type = mt5.ORDER_TYPE_BUY if trade_flag == PositionModel.BUYING_FLAG else mt5.ORDER_TYPE_SELL
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": self._symbol,
            "volume": lot,
            "type": order_type,
            "position": position_ticket,
            "magic": self._magic_number,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        return request
    
    def mail_daily_summary(self, trade_histories: TradeHistoriesModel):
        yesterday = datetime.now() - timedelta(days=1)
        account_info = mt5.account_info()
        ea_text = "サーバ名: {0}\nID: {1}\nティック: {2}".format(
            account_info.server,
            account_info.login,
            self._symbol
        )

        benefit_histories = trade_histories.get_benefit_histories()
        loss_histories = trade_histories.get_loss_histories()

        total_benefit_list_by_buying = []
        total_benefit_list_by_selling = []
        text_of_benefit_trade_but_loss = ""
        for benefit_history in benefit_histories:
            profit = benefit_history.get_profit()
            if benefit_history.is_trade_flag_buying() == True:
                total_benefit_list_by_buying.append(profit)
            else:
                total_benefit_list_by_selling.append(profit)
            
            if profit < 0:
                text_of_benefit_trade_but_loss += "ポジションチケット: {0}, 損益: {1}\n".format(benefit_history.get_position_ticket(), profit)

        total_loss_list_by_buying = []
        total_loss_list_by_selling = []
        text_of_loss_trade_but_benefit = ""
        for loss_history in loss_histories:
            profit = loss_history.get_profit()
            if loss_history.is_trade_flag_buying() == True:
                total_loss_list_by_buying.append(profit)
            else:
                total_loss_list_by_selling.append(profit)
            
            if profit > 0:
                text_of_loss_trade_but_benefit += "ポジションチケット: {0}, 損益: {1}\n".format(loss_history.get_position_ticket(), profit)


            
        total_profit_text = "トレード回数: {0}, トータル損益: {1}".format(
            len(benefit_histories) + len(loss_histories),
            sum(total_benefit_list_by_buying) + sum(total_benefit_list_by_selling) + sum(total_loss_list_by_buying) + sum(total_loss_list_by_selling)
        )
        profit_by_buying_position_text = "買いポジションの利益: {0}回/{1}, 損失: {2}回/{3}".format(
            len(total_benefit_list_by_buying),
            sum(total_benefit_list_by_buying),
            len(total_loss_list_by_buying),
            sum(total_loss_list_by_buying)
        )
        profit_by_selling_position_text = "売りポジションの利益: {0}回/{1}, 損失: {2}回/{3}".format(
            len(total_benefit_list_by_selling),
            sum(total_benefit_list_by_selling),
            len(total_loss_list_by_selling),
            sum(total_loss_list_by_selling)
        )
        alert_profit_positions_text = "利益判定だが損失だったトレード記録: {0}\n\n損失判定だが利益だったトレード記録: {1}".format(
            text_of_benefit_trade_but_loss,
            text_of_loss_trade_but_benefit
        )
        margin_rate_text = "最低マージンレート: {}".format(trade_histories.get_min_margin_rate())
        mail_body = "{0}\n{1}\n{2}\n{3}\n{4}\n{5}".format(
            ea_text,
            total_profit_text,
            profit_by_buying_position_text,
            profit_by_selling_position_text,
            alert_profit_positions_text,
            margin_rate_text
        )

        mail_title = "[{}] Daily Summary".format(yesterday.strftime("%Y-%m-%d"))
        MailHandler.send_mail(mail_title, mail_body)