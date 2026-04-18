import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Callable, Optional


logger = logging.getLogger(__name__)


class DailyTaskScheduler:
	def __init__(self, task: Callable[[], None], hour: int = 23, minute: int = 59):
		self.task = task
		self.hour = hour
		self.minute = minute
		self._started = False
		self._stop_event = threading.Event()
		self._thread: Optional[threading.Thread] = None

	def start(self):
		if self._started:
			return self

		self._started = True
		self._thread = threading.Thread(target=self._run, daemon=True, name="image-privacy-scheduler")
		self._thread.start()
		logger.info("Daily task scheduler started for %02d:%02d.", self.hour, self.minute)
		return self

	def stop(self):
		self._stop_event.set()

	def _seconds_until_next_run(self) -> float:
		now = datetime.now()
		next_run = now.replace(hour=self.hour, minute=self.minute, second=0, microsecond=0)
		if next_run <= now:
			next_run += timedelta(days=1)
		return max(0.0, (next_run - now).total_seconds())

	def _run(self):
		while not self._stop_event.is_set():
			seconds_to_wait = self._seconds_until_next_run()
			if self._stop_event.wait(seconds_to_wait):
				break
			try:
				self.task()
			except Exception:
				logger.exception("Daily scheduled task failed.")


def start_daily_task_scheduler(task: Callable[[], None], hour: int = 23, minute: int = 59) -> DailyTaskScheduler:
	scheduler = DailyTaskScheduler(task=task, hour=hour, minute=minute)
	return scheduler.start()