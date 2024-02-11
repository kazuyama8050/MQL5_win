import logging,os,sys
from logging.handlers import TimedRotatingFileHandler
import datetime

class Logger():
    @staticmethod
    def get_logger(app_dir, app_name):
        log_format = logging.Formatter(fmt="%(asctime)s\t%(levelname)s\t%(message)s", datefmt=None, style='%')
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setFormatter(log_format)
        logger.addHandler(stdout_handler)
        
        log_filename = app_name + datetime.datetime.today().strftime("%Y%m%d")
        file_handler = TimedRotatingFileHandler(
            filename=os.path.join(app_dir, "log", log_filename + ".log"),
            when="D",
            interval=31,
            backupCount=5,
            encoding="utf-8"
        )
        file_handler.setFormatter(log_format)
        logger.addHandler(file_handler)
        return logger
