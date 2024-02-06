import MetaTrader5 as mt5

class TradeHandler():
    def __init__(self, logger):
        self._logger = logger

    def order_request(self, request):
        result =  mt5.order_send(request)
        self.print_order_message(result)
        return result
    
    @staticmethod
    def is_order_success(retcode: int):
        return retcode == mt5.TRADE_RETCODE_DONE
    
    @staticmethod 
    def is_market_closed(retcode: int):
        return retcode == mt5.TRADE_RETCODE_MARKET_CLOSED

    def print_order_message(self, result):
        retcode = result.retcode
        retcode_msgs = {
            mt5.TRADE_RETCODE_REQUOTE: "リクオートされました。",
            mt5.TRADE_RETCODE_REJECT: "リクエストが拒否されました。",
            mt5.TRADE_RETCODE_CANCEL: "トレードによってリクエストが拒否されました。",
            mt5.TRADE_RETCODE_PLACED: "注文が出されました。",
            mt5.TRADE_RETCODE_DONE: "正常完了しました。",
            mt5.TRADE_RETCODE_DONE_PARTIAL: "リクエストが一部のみ完了しました。",
            mt5.TRADE_RETCODE_ERROR: "リクエスト処理エラーが発生しました。",
            mt5.TRADE_RETCODE_TIMEOUT: "タイムアウトによりリクエストがキャンセルされました。",
            mt5.TRADE_RETCODE_INVALID: "無効なリクエストです。",
            mt5.TRADE_RETCODE_INVALID_VOLUME: "リクエストされたロット数が無効です。",
            mt5.TRADE_RETCODE_INVALID_PRICE: "リクエストされた価格が無効です。",
            mt5.TRADE_RETCODE_INVALID_STOPS: "リクエストされたストップが無効です。",
            mt5.TRADE_RETCODE_TRADE_DISABLED: "取引が無効化されました。",
            mt5.TRADE_RETCODE_MARKET_CLOSED: "市場が閉鎖中です。",
            mt5.TRADE_RETCODE_NO_MONEY: "資金が不十分です。",
            mt5.TRADE_RETCODE_PRICE_CHANGED: "価格が変更されました。",
            mt5.TRADE_RETCODE_PRICE_OFF: "リクエスト処理に必要な相場が不在です。",
            mt5.TRADE_RETCODE_INVALID_EXPIRATION: "リクエストされた注文有効期限が無効です。",
            mt5.TRADE_RETCODE_ORDER_CHANGED: "注文状態が変化しました。",
            mt5.TRADE_RETCODE_TOO_MANY_REQUESTS: "リクエストが頻繁過ぎます。",
            mt5.TRADE_RETCODE_NO_CHANGES: "リクエストに変更がありませんでした。",
            mt5.TRADE_RETCODE_SERVER_DISABLES_AT: "サーバが自動取引を無効化しました。",
            mt5.TRADE_RETCODE_CLIENT_DISABLES_AT: "クライアント端末が自動取引を無効化しました。",
            mt5.TRADE_RETCODE_LOCKED: "リクエスト処理中のためロック中です。",
            mt5.TRADE_RETCODE_FROZEN: "注文やポジションが凍結中です。",
            mt5.TRADE_RETCODE_INVALID_FILL: "無効な注文補填タイプです。",
            mt5.TRADE_RETCODE_CONNECTION: "取引サーバに未接続です。",
            mt5.TRADE_RETCODE_ONLY_REAL: "ライブ口座でのみ可能な操作です。",
            mt5.TRADE_RETCODE_LIMIT_ORDERS: "未決注文数が上限に達しました。",
            mt5.TRADE_RETCODE_LIMIT_VOLUME: "シンボルの注文やポジションのボリュームが限界に達しました。",
            mt5.TRADE_RETCODE_INVALID_ORDER: "注文の種類が不正または禁止されています。",
            mt5.TRADE_RETCODE_POSITION_CLOSED: "指定されたポジションはすでに閉鎖済みです。",
            mt5.TRADE_RETCODE_INVALID_CLOSE_VOLUME: "決済ロット数がポジションのロット数を超過しています。",
            mt5.TRADE_RETCODE_CLOSE_ORDER_EXIST: "指定されたポジションの決済注文が既存です。",
            mt5.TRADE_RETCODE_LIMIT_POSITIONS: "ポジション数が上限に達しています。",
            mt5.TRADE_RETCODE_REJECT_CANCEL: "未決注文アクティベーションリクエストは却下され、注文がキャンセルされました。",
            mt5.TRADE_RETCODE_LONG_ONLY: "買いポジションのみリクエスト可能です。",
            mt5.TRADE_RETCODE_SHORT_ONLY: "売りポジションのみリクエスト可能です。",
            mt5.TRADE_RETCODE_FIFO_CLOSE: "FIFOによるポジション決済のみ可能です。",
            # mt5.TRADE_RETCODE_HEDGE_PROHIBITED: "保有ポジションの反対ポジションをとることはできません。"
        }

        if retcode in retcode_msgs.keys():
            self._logger.notice(retcode_msgs[retcode])
        else:
            self._logger.notice("リクエスト処理にて予期せぬ異常が発生しました。")

        if retcode == mt5.TRADE_RETCODE_DONE:
            self._logger.notice("<注文結果> 約定チケット：{0}、ポジションチケット：{1}、 ロット数：{2}、価格：{3}、コメント：{4}".format(
                    result.deal, result.order, result.volume, result.price, result.comment
                )
            )
