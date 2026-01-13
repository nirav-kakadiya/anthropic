"""
Scheduler - Automated periodic scans with cron-like scheduling.

Features:
- Schedule scans at intervals (hourly, daily, weekly)
- Background execution
- Integration with storage and alerts
- Scan comparison and change detection
- Configurable callbacks
"""

import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Callable, Any
from enum import Enum
import json


class ScheduleInterval(Enum):
    """Scan interval options."""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    CUSTOM = "custom"


@dataclass
class ScheduledTask:
    """A scheduled scan task."""
    task_id: str
    name: str
    interval: ScheduleInterval
    interval_seconds: int
    url: Optional[str] = None
    features: list[str] = field(default_factory=list)
    niche: str = ""
    callback: Optional[Callable] = None
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    is_active: bool = True
    config: dict = field(default_factory=dict)


@dataclass
class TaskResult:
    """Result of a scheduled task run."""
    task_id: str
    run_time: str
    success: bool
    keywords_found: int = 0
    gaps_found: int = 0
    new_keywords: list[str] = field(default_factory=list)
    error: Optional[str] = None
    duration_seconds: float = 0.0


class ScanScheduler:
    """
    Schedule and manage automated scans.

    Usage:
        scheduler = ScanScheduler()

        # Add a daily scan
        scheduler.add_task(
            name="Daily Market Scan",
            url="https://mysite.com",
            features=["flux ai", "kling ai"],
            interval=ScheduleInterval.DAILY,
            callback=my_callback_function
        )

        # Start the scheduler (runs in background)
        scheduler.start()

        # Check status
        print(scheduler.get_status())

        # Stop when done
        scheduler.stop()
    """

    INTERVAL_SECONDS = {
        ScheduleInterval.HOURLY: 3600,
        ScheduleInterval.DAILY: 86400,
        ScheduleInterval.WEEKLY: 604800,
    }

    def __init__(
        self,
        storage=None,
        alert_manager=None,
    ):
        self.storage = storage
        self.alert_manager = alert_manager

        self.tasks: dict[str, ScheduledTask] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._results: list[TaskResult] = []

    def add_task(
        self,
        name: str,
        url: Optional[str] = None,
        features: list[str] = None,
        niche: str = "",
        interval: ScheduleInterval = ScheduleInterval.DAILY,
        custom_interval_seconds: int = 0,
        callback: Optional[Callable[[TaskResult], None]] = None,
        run_immediately: bool = False,
        config: dict = None,
    ) -> str:
        """
        Add a scheduled scan task.

        Args:
            name: Task name for identification
            url: URL to scan (for auto mode)
            features: List of your features (for manual mode)
            niche: Your niche
            interval: How often to run
            custom_interval_seconds: Custom interval if using CUSTOM
            callback: Function to call with results
            run_immediately: Run once immediately
            config: Additional configuration

        Returns:
            task_id
        """
        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.tasks)}"

        if interval == ScheduleInterval.CUSTOM:
            interval_seconds = custom_interval_seconds
        else:
            interval_seconds = self.INTERVAL_SECONDS[interval]

        task = ScheduledTask(
            task_id=task_id,
            name=name,
            interval=interval,
            interval_seconds=interval_seconds,
            url=url,
            features=features or [],
            niche=niche,
            callback=callback,
            next_run=datetime.now() if run_immediately else datetime.now() + timedelta(seconds=interval_seconds),
            config=config or {},
        )

        self.tasks[task_id] = task
        return task_id

    def remove_task(self, task_id: str) -> bool:
        """Remove a scheduled task."""
        if task_id in self.tasks:
            del self.tasks[task_id]
            return True
        return False

    def pause_task(self, task_id: str) -> bool:
        """Pause a task."""
        if task_id in self.tasks:
            self.tasks[task_id].is_active = False
            return True
        return False

    def resume_task(self, task_id: str) -> bool:
        """Resume a paused task."""
        if task_id in self.tasks:
            self.tasks[task_id].is_active = True
            self.tasks[task_id].next_run = datetime.now()
            return True
        return False

    def _run_task(self, task: ScheduledTask) -> TaskResult:
        """Execute a single task."""
        start_time = time.time()
        result = TaskResult(
            task_id=task.task_id,
            run_time=datetime.now().isoformat(),
            success=False,
        )

        try:
            # Import here to avoid circular imports
            from .scout_agent import AutoScoutAgent, ScoutAgent

            # Create appropriate agent
            if task.url:
                # Use auto mode
                agent = AutoScoutAgent.from_url(task.url)
                # Note: In real usage, you'd need to fetch pages first
                # For now, we'll just use manual mode with any provided features
                if task.features:
                    agent.add_manual_features(task.features)
                if task.niche:
                    agent.set_manual_niche(task.niche)
            else:
                # Use manual mode
                agent = AutoScoutAgent.manual(
                    features=task.features,
                    niche=task.niche
                )

            # Run research (without data, just to test the flow)
            scan_result = agent.run_research()

            result.success = True
            result.keywords_found = scan_result.total_keywords
            result.gaps_found = scan_result.total_gaps

            # Save to storage if available
            if self.storage:
                self.storage.save_scan(
                    scan_id=scan_result.scan_id,
                    url=task.url or "",
                    niche=task.niche,
                    keywords=scan_result.all_keywords,
                    gaps=[{"keyword": g.keyword} for g in (scan_result.gap_report.gaps if scan_result.gap_report else [])],
                )

            # Send alerts if available
            if self.alert_manager and result.gaps_found > 0:
                self.alert_manager.notify_scan_complete(
                    keywords_found=result.keywords_found,
                    gaps_found=result.gaps_found,
                    top_opportunities=result.new_keywords[:5],
                )

        except Exception as e:
            result.success = False
            result.error = str(e)

            if self.alert_manager:
                self.alert_manager.notify_error(
                    error_message=str(e),
                    context=f"Task: {task.name}"
                )

        result.duration_seconds = time.time() - start_time

        # Update task stats
        task.last_run = datetime.now()
        task.next_run = datetime.now() + timedelta(seconds=task.interval_seconds)
        task.run_count += 1

        # Call callback if provided
        if task.callback:
            try:
                task.callback(result)
            except Exception:
                pass  # Don't let callback errors affect scheduler

        self._results.append(result)

        return result

    def _scheduler_loop(self):
        """Main scheduler loop."""
        while self._running:
            now = datetime.now()

            for task in self.tasks.values():
                if not task.is_active:
                    continue

                if task.next_run and now >= task.next_run:
                    self._run_task(task)

            # Sleep for a bit before checking again
            time.sleep(10)  # Check every 10 seconds

    def start(self):
        """Start the scheduler in a background thread."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop the scheduler."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None

    def run_now(self, task_id: str) -> Optional[TaskResult]:
        """Manually trigger a task to run immediately."""
        if task_id not in self.tasks:
            return None

        return self._run_task(self.tasks[task_id])

    def get_status(self) -> dict:
        """Get scheduler status."""
        return {
            "running": self._running,
            "total_tasks": len(self.tasks),
            "active_tasks": sum(1 for t in self.tasks.values() if t.is_active),
            "total_runs": sum(t.run_count for t in self.tasks.values()),
            "tasks": [
                {
                    "task_id": t.task_id,
                    "name": t.name,
                    "interval": t.interval.value,
                    "is_active": t.is_active,
                    "run_count": t.run_count,
                    "last_run": t.last_run.isoformat() if t.last_run else None,
                    "next_run": t.next_run.isoformat() if t.next_run else None,
                }
                for t in self.tasks.values()
            ]
        }

    def get_results(self, limit: int = 20) -> list[TaskResult]:
        """Get recent task results."""
        return self._results[-limit:]

    def export_config(self) -> str:
        """Export scheduler configuration as JSON."""
        config = {
            "tasks": [
                {
                    "name": t.name,
                    "url": t.url,
                    "features": t.features,
                    "niche": t.niche,
                    "interval": t.interval.value,
                    "interval_seconds": t.interval_seconds,
                    "is_active": t.is_active,
                    "config": t.config,
                }
                for t in self.tasks.values()
            ]
        }
        return json.dumps(config, indent=2)

    def import_config(self, config_json: str):
        """Import scheduler configuration from JSON."""
        config = json.loads(config_json)

        for task_config in config.get("tasks", []):
            interval = ScheduleInterval(task_config.get("interval", "daily"))
            self.add_task(
                name=task_config.get("name", "Imported Task"),
                url=task_config.get("url"),
                features=task_config.get("features", []),
                niche=task_config.get("niche", ""),
                interval=interval,
                custom_interval_seconds=task_config.get("interval_seconds", 86400),
                config=task_config.get("config", {}),
            )


def create_scheduler(storage=None, alert_manager=None) -> ScanScheduler:
    """Factory function to create a ScanScheduler."""
    return ScanScheduler(storage=storage, alert_manager=alert_manager)
