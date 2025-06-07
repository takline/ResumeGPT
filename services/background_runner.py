"""
Provides a BackgroundRunner class for executing functions asynchronously
using a thread pool. This allows long-running tasks to be offloaded from
the main execution flow, improving responsiveness for applications that
need to perform multiple operations concurrently (e.g., processing multiple
job postings).
"""
import time
from typing import List, Optional, Callable, Any
from ..config import config # Attempt to import global config
import logging
import concurrent.futures

# Attempt to get MAX_CONCURRENT_WORKERS from config, with a fallback
try:
    MAX_WORKERS = config.MAX_CONCURRENT_WORKERS
except AttributeError:
    logging.getLogger(__name__).warning(
        "config.MAX_CONCURRENT_WORKERS not found. Using default value of 4 for BackgroundRunner."
    )
    MAX_WORKERS = 4 # Default if not found in config

try:
    BACKGROUND_TASKS_LOG_PATH = config.BACKGROUND_TASKS_LOG
except AttributeError:
    logging.getLogger(__name__).warning(
        "config.BACKGROUND_TASKS_LOG not found. Using default 'background_tasks.log'."
    )
    BACKGROUND_TASKS_LOG_PATH = "background_tasks.log"


class BackgroundRunner:
    """
    Manages a thread pool for running tasks in the background.

    This class provides a simple interface to submit functions for asynchronous
    execution and to check on their status. It uses a ThreadPoolExecutor
    to limit the number of concurrently running threads.
    """
    def __init__(self, max_workers: Optional[int] = None):
        """
        Initializes the BackgroundRunner with a ThreadPoolExecutor.

        Args:
            max_workers (Optional[int]): The maximum number of threads to use.
                                         If None, defaults to MAX_WORKERS (from config or
                                         an internal default of 4).
        """
        self.max_workers = max_workers or MAX_WORKERS
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers)
        self.futures: List[concurrent.futures.Future] = []
        self.logger = self._create_logger()
        self.logger.info(f"BackgroundRunner initialized with max_workers={self.max_workers}.")

    def _create_logger(self) -> logging.Logger:
        """
        Creates and configures a dedicated logger for the BackgroundRunner.

        The logger outputs to a file specified by BACKGROUND_TASKS_LOG_PATH.
        It avoids duplicate logging if handlers are already present.

        Returns:
            logging.Logger: The configured logger instance.
        """
        logger = logging.getLogger(__name__ + ".BackgroundRunnerInstance") # Unique name for each instance's logger

        # Configure only if handlers have not been added yet (e.g. by other instances)
        if not logger.handlers:
            logger.propagate = False # Prevent logs from reaching the root logger if desired
            try:
                handler = logging.FileHandler(BACKGROUND_TASKS_LOG_PATH)
                formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(threadName)s - %(message)s")
                handler.setFormatter(formatter)
                logger.addHandler(handler)
                logger.setLevel(logging.INFO) # Default level
            except Exception as e:
                # Fallback to basic logging if file handler fails
                logging.basicConfig(level=logging.INFO)
                logger = logging.getLogger(__name__ + ".BackgroundRunnerInstance.Fallback")
                logger.error(f"Failed to configure file logger for BackgroundRunner. Using basicConfig. Error: {e}", exc_info=True)
        return logger

    def run_in_background(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Optional[concurrent.futures.Future]:
        """
        Submits a function to be executed in the background by the thread pool.

        Args:
            func (Callable): The function to execute.
            *args: Positional arguments to pass to the function.
            **kwargs: Keyword arguments to pass to the function.

        Returns:
            Optional[concurrent.futures.Future]: A Future object representing the
                                                 execution of the task, or None if
                                                 submission fails.
        """
        # Log submission without potentially large args/kwargs in primary message
        self.logger.info(f"Submitting task '{func.__name__}' to ThreadPoolExecutor.")
        # For more detailed debugging, one might log args/kwargs selectively or use reprlib for truncation.
        # self.logger.debug(f"Task '{func.__name__}' args: {args}, kwargs: {kwargs}")
        try:
            future = self.executor.submit(func, *args, **kwargs)
            self.futures.append(future)
            self.logger.info(f"Task '{func.__name__}' submitted successfully. Future: {future}")
            return future
        except Exception as e:
            self.logger.error(f"Failed to submit task '{func.__name__}': {e}", exc_info=True)
            return None

    def check_status(self) -> List[str]:
        """
        Checks the status of all submitted tasks.

        Returns:
            List[str]: A list of strings, each describing the status of a task
                       (e.g., "Task is running", "Task completed successfully",
                       "Task completed with error: ...").
        """
        if not self.futures:
            self.logger.info("No tasks submitted to check status.")
            return ["No tasks submitted."]
        
        statuses: List[str] = []
        active_futures_still: List[concurrent.futures.Future] = []

        for f in self.futures:
            if f.done():
                status_message = f"Task (Future {id(f)}) completed"
                try:
                    # Accessing f.exception() is the correct way to check for exceptions
                    # without re-raising it immediately if you just want to log it.
                    exception = f.exception(timeout=0) # timeout=0 to not block if somehow not truly done
                    if exception:
                        status_message += f" with error: {type(exception).__name__}('{str(exception)}')"
                        self.logger.error(f"Task Future {id(f)} completed with error: {exception}", exc_info=exception)
                    else:
                        # Optionally, you could log f.result() if it's small and safe to log
                        # result = f.result(timeout=0)
                        # status_message += f" successfully with result: {str(result)[:50]}..."
                        status_message += " successfully."
                        self.logger.info(f"Task Future {id(f)} completed successfully.")
                except concurrent.futures.CancelledError:
                    status_message += " (cancelled)."
                    self.logger.info(f"Task Future {id(f)} was cancelled.")
                except Exception as e: # Should be rare if f.done() is true
                    status_message += f" (error checking result: {type(e).__name__}('{str(e)}'))"
                    self.logger.error(f"Error retrieving result/exception for done task Future {id(f)}: {e}", exc_info=True)
                statuses.append(status_message)
            else:
                statuses.append(f"Task (Future {id(f)}) is running.")
                active_futures_still.append(f) # Keep it for the next status check

        self.futures = active_futures_still # Update the list to only contain still-active futures

        if not statuses: # Should only happen if futures list was cleared but no status messages generated
             return ["All tasks processed and futures list cleared."]
        return statuses

    def shutdown(self, wait: bool = True):
        """
        Shuts down the ThreadPoolExecutor.

        Args:
            wait (bool): If True (default), waits for all submitted tasks to complete
                         before shutting down. If False, shuts down immediately and
                         does not wait for tasks to finish.
        """
        self.logger.info(f"Shutting down BackgroundRunner's ThreadPoolExecutor (wait={wait}).")
        try:
            self.executor.shutdown(wait=wait)
            self.logger.info("ThreadPoolExecutor has been shut down.")
        except Exception as e:
            self.logger.error(f"Error during ThreadPoolExecutor shutdown: {e}", exc_info=True)

    def stop_all_tasks(self):
        """
        Initiates a non-waiting shutdown of the executor.

        Note: This does not forcibly stop running threads but prevents new tasks
        from starting and allows the program to exit sooner if `wait=False` is used.
        Currently running tasks will attempt to complete.
        """
        self.logger.warning(
            "stop_all_tasks() called. Initiating a non-waiting shutdown of the executor. "
            "Ongoing tasks will attempt to complete."
        )
        self.shutdown(wait=False)

