import MetaTrader5 as mt5
import os,sys

current_script_path = os.path.abspath(__file__)
PROJECT_DIR = os.path.abspath(os.path.join(current_script_path, "../.."))
sys.path.append(os.path.join(PROJECT_DIR, "lib"))

from logger import Logger

class AccountHandler():
    def __init__(self, account, passwd, server):
        self._account = account
        self._passwd = passwd
        self._server = server

    def login(self, timeout = 60000):
        authorized = mt5.login(self._account, password=self._passwd, server=self._server, timeout=timeout)
        if authorized:
            Logger.notice("ログインに成功しました。 アカウント: {}".format(self._account))
        else:
            Logger.crit("ログインに失敗しました。 アカウント: {}".format(self._account))