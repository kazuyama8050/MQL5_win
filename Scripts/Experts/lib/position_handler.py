import MetaTrader5 as mt5

class PositionHandler():
    def __init__(self, symbol, magic_number):
        self._symbol = symbol
        self._magic_number = magic_number

    def get_position_size_by_symbol(self):
        return len(mt5.positions_get(symbol = self._symbol))
    
    def get_position_size_by_symbol_magic(self):
        size = 0
        for position in mt5.positions_get(symbol = self._symbol):
            if position.magic == self._magic_number:
                size += 1

        return size