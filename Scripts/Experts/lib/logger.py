class Logger():
    @staticmethod
    def crit(text):
        try:
            raise("[Critical]" + text)
        except Exception as e:
            print(e)

    @staticmethod
    def error(text):
        print("[ERROR]" + text)

    @staticmethod
    def warn(text):
        print("[WARN]" + text)

    @staticmethod
    def notice(text):
        print("[NOTICE]" + text)

    @staticmethod
    def summary(text):
        print("[SUMMARY]" + text)