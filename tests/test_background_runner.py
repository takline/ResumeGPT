import unittest
from unittest.mock import patch, MagicMock, call
import time
import concurrent.futures
from ..services.background_runner import BackgroundRunner, MAX_WORKERS as DEFAULT_MAX_WORKERS, BACKGROUND_TASKS_LOG_PATH

# Mock function to be executed in background
def mock_task_func(*args, **kwargs):
    # print(f"Mock task called with args: {args}, kwargs: {kwargs}")
    time.sleep(0.1) # Simulate work
    if 'fail' in kwargs and kwargs['fail']:
        raise ValueError("Task failed as requested")
    return "Task completed successfully"

class TestBackgroundRunner(unittest.TestCase):

    @patch('concurrent.futures.ThreadPoolExecutor')
    def test_init_default_workers(self, MockThreadPoolExecutor):
        """Test BackgroundRunner initialization with default max_workers."""
        runner = BackgroundRunner()
        MockThreadPoolExecutor.assert_called_once_with(max_workers=DEFAULT_MAX_WORKERS)
        self.assertIsNotNone(runner.logger)

    @patch('concurrent.futures.ThreadPoolExecutor')
    def test_init_custom_workers(self, MockThreadPoolExecutor):
        """Test BackgroundRunner initialization with custom max_workers."""
        custom_workers = 3
        runner = BackgroundRunner(max_workers=custom_workers)
        MockThreadPoolExecutor.assert_called_once_with(max_workers=custom_workers)

    def test_create_logger(self):
        """Test that the logger is created and configured."""
        runner = BackgroundRunner()
        self.assertIsNotNone(runner.logger)
        self.assertTrue(any(isinstance(h, unittest.mock.Base) or h.baseFilename == BACKGROUND_TASKS_LOG_PATH for h in runner.logger.handlers),
                        "FileHandler not configured for the correct log path.")

    def test_run_in_background_successful_submission(self):
        """Test successful task submission to the executor."""
        runner = BackgroundRunner(max_workers=1)
        mock_executor_instance = runner.executor
        # Spy on the submit method of the actual executor instance
        mock_executor_instance.submit = MagicMock(wraps=mock_executor_instance.submit)

        future = runner.run_in_background(mock_task_func, "arg1", kwarg1="value1")

        self.assertIsNotNone(future)
        mock_executor_instance.submit.assert_called_once_with(mock_task_func, "arg1", kwarg1="value1")
        self.assertIn(future, runner.futures)

        # Wait for the task to complete
        if future:
            future.result() # Ensure it finishes
        runner.shutdown()

    @patch.object(concurrent.futures.ThreadPoolExecutor, 'submit', side_effect=Exception("Submission failed"))
    def test_run_in_background_submission_failure(self, mock_submit_method):
        """Test task submission failure."""
        runner = BackgroundRunner(max_workers=1)
        future = runner.run_in_background(mock_task_func, "arg1")
        self.assertIsNone(future)
        # Logger should have logged an error, can be checked if logger is also mocked or by inspecting logs.
        runner.shutdown()

    def test_task_execution_and_completion(self):
        """Test that a submitted task executes and completes."""
        runner = BackgroundRunner(max_workers=1)
        callback_mock = MagicMock()

        def task_with_callback():
            time.sleep(0.05)
            callback_mock("done")
            return "finished"

        future = runner.run_in_background(task_with_callback)
        self.assertIsNotNone(future)

        # Wait for future to complete
        result = future.result(timeout=1) # Wait for result, raises TimeoutError if too long

        self.assertEqual(result, "finished")
        callback_mock.assert_called_once_with("done")

        # Check status after completion
        # Need a small delay for the .done() to be reliably true after result()
        time.sleep(0.01)
        statuses = runner.check_status()
        self.assertTrue(any("Task completed successfully." in s for s in statuses))

        runner.shutdown()

    def test_check_status_no_tasks(self):
        """Test check_status when no tasks are submitted."""
        runner = BackgroundRunner()
        self.assertEqual(runner.check_status(), ["No tasks submitted."])
        runner.shutdown()

    def test_check_status_running_task(self):
        """Test check_status for a running task."""
        runner = BackgroundRunner(max_workers=1)

        event = threading.Event()
        def long_running_task():
            event.wait(timeout=0.5) # Wait for a short period or until event is set
            return "long task done"

        future = runner.run_in_background(long_running_task)
        self.assertIsNotNone(future)

        statuses_running = runner.check_status()
        self.assertTrue(any("Task is running." in s for s in statuses_running))

        event.set() # Allow task to complete
        future.result(timeout=1) # Wait for completion
        runner.shutdown()

    def test_task_failure_and_status_check(self):
        """Test that task failure is correctly reported by check_status."""
        runner = BackgroundRunner(max_workers=1)
        future = runner.run_in_background(mock_task_func, fail=True)
        self.assertIsNotNone(future)

        with self.assertRaises(ValueError, msg="Task failed as requested"):
            future.result(timeout=1) # This will raise the exception from the task

        # Check status after failure
        time.sleep(0.01) # Give time for future to be marked done
        statuses = runner.check_status()
        self.assertTrue(any("Task completed with error: ValueError('Task failed as requested')" in s for s in statuses),
                        f"Statuses were: {statuses}")
        runner.shutdown()

    @patch.object(concurrent.futures.ThreadPoolExecutor, 'shutdown')
    def test_shutdown_method(self, mock_executor_shutdown):
        """Test that the shutdown method calls executor.shutdown."""
        runner = BackgroundRunner()
        runner.shutdown(wait=True)
        mock_executor_shutdown.assert_called_once_with(wait=True)

        runner.shutdown(wait=False)
        mock_executor_shutdown.assert_called_with(wait=False) # Called again

if __name__ == '__main__':
    unittest.main()
