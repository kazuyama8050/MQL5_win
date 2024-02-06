import math

class MonteCarloModel():
    def __init__(self, base_lot):
        self._monte_carlo_list = [0, 1]
        self._base_lot = base_lot

    def reset(self):
        self._monte_carlo_list = [0, 1]

    def get_size(self):
        return len(self._monte_carlo_list)

    def get_next_trade_lot(self):
        self._is_valid_size()
        return (self._monte_carlo_list[0] + self._monte_carlo_list[-1]) * self._base_lot
    
    def get_additional_val(self):
        self._is_valid_size()
        return self._monte_carlo_list[0] + self._monte_carlo_list[-1]
    
    def operate_by_benefit(self):
        self._is_valid_size()
        self._monte_carlo_list.pop(0)
        self._monte_carlo_list.pop(-1)

    def operate_by_loss(self):
        self._monte_carlo_list.append(self.get_additional_val())

    """
    数列サイズが一つの場合は2つに分解する
    偶数の場合は2等分
    奇数の場合は0要素に小さいほう、1要素に大きいほう
    """
    def decompose(self):
        if self.get_size() != 1: return
        number = self._monte_carlo_list[0]
        if number == 0: raise Exception("invalid monte carlo list before decompose")
        if number % 2 == 0:
            self._monte_carlo_list[0] = number / 2
            self._monte_carlo_list[1] = number / 2
        else:
            self._monte_carlo_list[0] = math.floor(number)
            self._monte_carlo_list[0] = math.ceil(number)
            

    def _is_valid_size(self):
        if self.get_size() < 2:
            raise Exception("invalid monte carlo list size")

        