import socket
import sys,traceback

"""
ローカルホストの対象ポート剥けてコマンド送信を実行するスクリプト
arg1: 送信先ポート番号
arg2: コマンド文字列
"""

def main():
    try:
        print("Start Socket Command.")
        args = sys.argv
        PORT = int(args[1])
        COMMAND = str(args[2])
        
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('localhost', PORT))

        # コマンドをサーバーに送信
        client_socket.send(COMMAND.encode('utf-8'))
        
        print("Send Socket Command. str: {0}, port: {1}".format(COMMAND, PORT))
        
        # 結果を受信して表示
        result = client_socket.recv(1024).decode('utf-8')
        print(f"Server response: {result}")

    except Exception as e:
        print(traceback.format_exc())
    finally:
        # ソケットを閉じる
        if client_socket is not None:
            client_socket.close()
            
if __name__ == "__main__":
    main()
