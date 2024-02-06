
class PositionModel():
    BUYING_FLAG = 1
    SELLING_FLAG = -1
    NO_TRADE_FLAG = 0
    
    def __init__(self, ticket: int, trade_flag: int, price: float, lot: float):
        self._ticket = ticket
        self._trade_flag = trade_flag
        self._price = price
        self._lot = lot
        self._is_valid = 1

    def to_not_valid(self):
        self._is_valid = 0

    @staticmethod
    def reverse_trade_flag(trade_flag):
        return PositionModel.BUYING_FLAG if trade_flag == PositionModel.SELLING_FLAG else PositionModel.SELLING_FLAG

    def get_ticket(self):
        return self._ticket
    
    def get_trade_flag(self):
        return self._trade_flag
    
    def get_price(self):
        return self._price
    
    def get_lot(self):
        return self._lot
    
    def is_valid(self):
        return self._is_valid == 1