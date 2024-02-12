import os
import pandas as pd

class FeatureFormatterService():
    @staticmethod
    def set_history_diff(df, mh_term_list):
        column_list = []
        for term in mh_term_list:
            df[f"mh_{term}"] = (df["close"] - df["close"].shift(term)) / df["close"].shift(term) * 100
            column_list.append(f"mh_{term}")
        return df, column_list
    
    @staticmethod
    def set_moving_average_indicators(df, ma_term_list):
        column_list = []
        for term in ma_term_list:
            df[f"ma_{term}"] = df['close'].rolling(window=term).mean()
            df[f"ma_close_{term}"] = (df["close"] - df[f"ma_{term}"]) / df[f"ma_{term}"] * 100
            df[f"ma_diff_{term}"] = (df[f"ma_{term}"] - df[f"ma_{term}"].shift(term)) / df[f"ma_{term}"].shift(term) * 100
            column_list.append(f"ma_close_{term}")
            column_list.append(f"ma_diff_{term}")
        return df, column_list
            
    @staticmethod
    def set_macd_indicators(df, short_window_list, long_window_list, signal_window_list):
        column_list = []
        for i in range(len(short_window_list)):
            short_window = short_window_list[i]
            long_window = long_window_list[i]
            signal_window = signal_window_list[i]
            
            short_ema = df["close"].ewm(span=short_window, adjust=False).mean()
            long_ema = df["close"].ewm(span=long_window, adjust=False).mean()
            
            df[f"macd_{short_window}_{long_window}_{signal_window}"] = short_ema - long_ema
            df[f"signal_line_{short_window}_{long_window}_{signal_window}"] = df[f"macd_{short_window}_{long_window}_{signal_window}"].ewm(span=signal_window, adjust=False).mean()
            
            ## MACDとMACDシグナルとの価格差
            df[f"macd_signal_diff_{short_window}_{long_window}_{signal_window}"] = df[f"macd_{short_window}_{long_window}_{signal_window}"] - df[f"signal_line_{short_window}_{long_window}_{signal_window}"]
            column_list.append(f"macd_signal_diff_{short_window}_{long_window}_{signal_window}")

            ## MACDと終値との価格差
            df[f"macd_close_diff_{short_window}_{long_window}_{signal_window}"] = df[f"macd_{short_window}_{long_window}_{signal_window}"] - df["close"]
            column_list.append(f"macd_close_diff_{short_window}_{long_window}_{signal_window}")

            ## MACDシグナルと終値との価格差
            df[f"signal_close_diff_{short_window}_{long_window}_{signal_window}"] = df[f"signal_line_{short_window}_{long_window}_{signal_window}"] - df["close"]
            column_list.append(f"signal_close_diff_{short_window}_{long_window}_{signal_window}")
        return df, column_list
    
    @staticmethod
    def set_bb_indicators(df, bb_term_list, bb_sigma_list):
        column_list = []
        for term in bb_term_list:
            for sigma in bb_sigma_list:
                # 上部バンドと下部バンドの計算
                std_dev = df['close'].rolling(window=term).std()
                df[f"upper_bb_close_{term}_{sigma}"] = (df[f"ma_{term}"] + sigma * std_dev) - df["close"]
                df[f"lower_bb_close_{term}_{sigma}"] = (df[f"ma_{term}"] - sigma * std_dev) - df["close"]
                
                column_list.append(f"upper_bb_close_{term}_{sigma}")
                column_list.append(f"lower_bb_close_{term}_{sigma}")
        return df, column_list
