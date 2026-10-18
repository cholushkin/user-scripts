import os

# possible log levels: important/normal/verbose/disabled
class LogManager:
    def __init__(self, globalLogLevel):
        """
        Initializes the LogManager with a global log level.

        Args:
            globalLogLevel (str): The global log level ("important", "normal", "verbose", "disabled").
        """
        self.globalLogLevel = globalLogLevel.lower()
        self.logLevels = {
            "important": 3,
            "normal": 2,
            "verbose": 1,
            "disabled": 0,
        }
        if self.globalLogLevel not in self.logLevels:
            print(f"Error: Invalid global log level '{globalLogLevel}'.  Defaulting to 'disabled'.")
            self.globalLogLevel = "disabled"

    def log(self, message_log_level, message):
        """
        Logs a message if its level is at or above the global log level.

        Args:
            message_log_level (str): The log level of the message ("important", "normal", "verbose", "disabled").
            message (str): The message to log.
        """
        message_log_level = message_log_level.lower()
        if message_log_level not in self.logLevels:
            print(f"Error: Invalid message log level '{message_log_level}'.  Message not logged.")
            return  # Important: Exit if the level is invalid

        if self.logLevels.get(message_log_level, 0) >= self.logLevels.get(self.globalLogLevel, 0):
            print(message)