import MetaTrader5 as mt5

"""
価格リストは古い順から格納される
"""
class SymbolHandler(object):
    TIME_FRAME_DICT = {
        "M1": mt5.TIMEFRAME_M1,
        "M2": mt5.TIMEFRAME_M2,
        "M3": mt5.TIMEFRAME_M3,
        "M4": mt5.TIMEFRAME_M4,
        "M5": mt5.TIMEFRAME_M5,
        "M6": mt5.TIMEFRAME_M6,
        "M10": mt5.TIMEFRAME_M10,
        "M12": mt5.TIMEFRAME_M12,
        "M15": mt5.TIMEFRAME_M15,
        "M20": mt5.TIMEFRAME_M20,
        "M30": mt5.TIMEFRAME_M30,
        "H1": mt5.TIMEFRAME_H1,
        "H2": mt5.TIMEFRAME_H2,
        "H3": mt5.TIMEFRAME_H3,
        "H4": mt5.TIMEFRAME_H4,
        "H6": mt5.TIMEFRAME_H6,
        "H8": mt5.TIMEFRAME_H8,
        "H12": mt5.TIMEFRAME_H12,
        "D1": mt5.TIMEFRAME_D1,
        "W1": mt5.TIMEFRAME_W1,
        "WN1": mt5.TIMEFRAME_MN1,
    }
    
    def __init__(self, symbol):
        self._symbol = symbol
        
    @staticmethod
    def get_mt5_timeframe(term):
        return TIME_FRAME_DICT[term]

    def get_prices_by_pos(self, timeframe, pos):
        return mt5.copy_rates_from_pos(self._symbol, timeframe, 0, pos)
    
    def get_close_prices_by_pos(self, timeframe, pos):
        close_prices = []
        for price_tuple in self.get_prices_by_pos(timeframe, pos):
            close_prices.append(price_tuple.close)
        return close_prices
    
    ## 買う場合の価格
    def get_latest_bid(self):
        return mt5.symbol_info_tick(self._symbol).bid
    
    ## 売る場合の価格
    def get_latest_ask(self):
        return mt5.symbol_info_tick(self._symbol).ask

    def is_market_open(self):
        mt5.symbol_info(self._symbol).trade_mode == mt5.SYMBOL_TRADE_MODE_FULL