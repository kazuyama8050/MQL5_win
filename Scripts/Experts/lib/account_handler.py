import MetaTrader5 as mt5
import os,sys

current_script_path = os.path.abspath(__file__)
PROJECT_DIR = os.path.abspath(os.path.join(current_script_path, "../.."))
sys.path.append(os.path.join(PROJECT_DIR, "lib"))

class AccountHandler():
    def __init__(self, logger, account, passwd, server):
        self._logger = logger
        self._account = account
        self._passwd = passwd
        self._server = server

    def login(self, timeout = 60000):
        account_info = mt5.account_info()
        if account_info is not None:
            if account_info.login != self._account:
                self._logger.error("別アカウントがログイン中です。 ID: {}".format(self._account))
                raise Exception()
            elif account_info.login == self._account:
                self._logger.info("既にログイン中です。")
        else:
            authorized = mt5.login(self._account, password=self._passwd, server=self._server, timeout=timeout)
            if authorized:
                self._logger.info("ログインに成功しました。 アカウント: {}".format(self._account))
            else:
                self._logger.critical("ログインに失敗しました。 アカウント: {}".format(self._account))
                raise Exception()
        
    @staticmethod
    def to_trade_mode_jp(trade_mode):
        trade_mode_jp_dict = {
            mt5.ACCOUNT_TRADE_MODE_DEMO: "デモ口座",
            mt5.ACCOUNT_TRADE_MODE_CONTEST: "コンテスト口座",
            mt5.ACCOUNT_TRADE_MODE_REAL: "リアル口座"
        }
        if trade_mode in trade_mode_jp_dict.keys():
            return trade_mode_jp_dict[trade_mode]
        return "予期せぬ口座種別"