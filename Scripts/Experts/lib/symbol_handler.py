import MetaTrader5 as mt5

"""
価格リストは古い順から格納される
"""
class SymbolHandler(object):
    def __init__(self, symbol):
        self._symbol = symbol

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