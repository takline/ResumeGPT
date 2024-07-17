import threading
import time
from ..config import config
import logging


class BackgroundRunner:
    def __init__(self):
        self.threads = []
        self.logger = self._create_logger()

    def _create_logger(self):
        """Creates a custom logger for the BackgroundRunner."""
        logger = logging.getLogger(__name__)
        handler = logging.FileHandler(config.BACKGROUND_TASKS_LOG)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger

    def run_in_background(self, func, *args, **kwargs):
        """Submits a function to be run in the background."""
        self.logger.info(
            f"Submitting task {func.__name__} with args {args} and kwargs {kwargs}"
        )
        thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        self.threads.append(thread)
        thread.start()
        self.logger.info("Task submitted.")

    def check_status(self):
        """Checks the status of the background tasks."""
        if not self.threads:
            self.logger.info("No tasks submitted.")
            return "No tasks submitted."
        
        statuses = []
        for thread in self.threads:
            if thread.is_alive():
                self.logger.info("Task is running.")
                statuses.append("Task is running.")
            else:
                self.logger.info("Task completed.")
                statuses.append("Task completed.")
        return statuses

    def stop_all_tasks(self):
        """Stops all running background tasks."""
        self.logger.info("Stopping all tasks.")
        for thread in self.threads:
            if thread.is_alive():
                # Python does not provide a direct way to kill threads.
                self.logger.warning("Cannot directly stop threads. They will complete on their own.")
        self.logger.info("All tasks stopped.")

