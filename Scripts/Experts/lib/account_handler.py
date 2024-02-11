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
        authorized = mt5.login(self._account, password=self._passwd, server=self._server, timeout=timeout)
        if authorized:
            self._logger.info("ログインに成功しました。 アカウント: {}".format(self._account))
        else:
            self._logger.critical("ログインに失敗しました。 アカウント: {}".format(self._account))
            raise Exception()