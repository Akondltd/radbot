"""
Task Coordinator - Manages execution order and dependencies for services.

This provides a lightweight task queue system that works with existing
threading/Qt services to prevent race conditions and ensure proper ordering.
"""

import logging
import time
import threading
from typing import Dict, List, Callable, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from queue import PriorityQueue

logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """Task priority levels - lower number = higher priority"""
    CRITICAL = 0    # Must run immediately (e.g., user actions)
    HIGH = 1        # Important operations (e.g., balance updates)
    NORMAL = 2      # Regular tasks (e.g., signal generation)
    LOW = 3         # Background tasks (e.g., statistics updates)
    IDLE = 4        # Run when nothing else is happening


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    WAITING = "waiting_for_dependencies"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(order=True)
class Task:
    """Represents a single task to be executed"""
    # Required fields (no defaults) MUST come first
    priority: int = field(compare=True)
    name: str = field(compare=False)
    func: Callable = field(compare=False)
    
    # Optional fields (with defaults) come after
    category: str = field(default="general", compare=False)  # e.g., "balance", "trade", "ui"
    args: tuple = field(default_factory=tuple, compare=False)
    kwargs: dict = field(default_factory=dict, compare=False)
    dependencies: List[str] = field(default_factory=list, compare=False)  # List of task names
    blocks_category: Optional[str] = field(default=None, compare=False)  # Block all tasks in this category until complete
    status: TaskStatus = field(default=TaskStatus.PENDING, compare=False)
    result: Any = field(default=None, compare=False)
    error: Optional[Exception] = field(default=None, compare=False)
    created_at: float = field(default_factory=time.time, compare=False)
    started_at: Optional[float] = field(default=None, compare=False)
    completed_at: Optional[float] = field(default=None, compare=False)
    retry_count: int = field(default=0, compare=False)
    max_retries: int = field(default=0, compare=False)
    timeout: Optional[float] = field(default=None, compare=False)  # Seconds
    
    def __post_init__(self):
        """Convert priority enum to int if needed"""
        if isinstance(self.priority, TaskPriority):
            self.priority = self.priority.value
    
    def execute(self) -> Any:
        """Execute the task function"""
        self.status = TaskStatus.RUNNING
        self.started_at = time.time()
        
        try:
            logger.debug(f"Executing task: {self.name} (priority={self.priority}, category={self.category})")
            start_time = time.time()
            self.result = self.func(*self.args, **self.kwargs)
            duration = time.time() - start_time
            self.status = TaskStatus.COMPLETED
            self.completed_at = time.time()
            logger.debug(f"Task completed: {self.name} in {duration:.2f}s")
            return self.result
            
        except Exception as e:
            self.error = e
            self.status = TaskStatus.FAILED
            self.completed_at = time.time()
            logger.error(f"Task failed: {self.name} - {e}", exc_info=True)
            raise


class TaskCoordinator:
    """
    Coordinates task execution with dependencies and ordering.
    Works with existing service architecture without requiring async rewrite.
    """
    
    def __init__(self):
        self.queue = PriorityQueue()
        self.completed_tasks: Dict[str, Task] = {}  # name -> Task
        self.running_tasks: Dict[str, Task] = {}  # name -> Task
        self.blocked_categories: set = set()  # Categories that are blocked
        
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._worker_thread: Optional[threading.Thread] = None
        
        # Statistics
        self.stats = {
            'tasks_submitted': 0,
            'tasks_completed': 0,
            'tasks_failed': 0,
            'total_execution_time': 0.0,
            'by_category': {}  # category -> {submitted, completed, failed, total_time}
        }
        
        logger.info("TaskCoordinator initialized")
    
    def submit(self, task: Task) -> None:
        """Submit a task for execution"""
        with self._lock:
            # Check if task with same name already exists
            if task.name in self.completed_tasks:
                logger.warning(f"Task {task.name} already completed, skipping")
                return
            
            if task.name in self.running_tasks:
                logger.warning(f"Task {task.name} already running, skipping")
                return
            
            # Update stats
            self.stats['tasks_submitted'] += 1
            if task.category not in self.stats['by_category']:
                self.stats['by_category'][task.category] = {
                    'submitted': 0, 'completed': 0, 'failed': 0, 'total_time': 0.0
                }
            self.stats['by_category'][task.category]['submitted'] += 1
            
            # Add to queue
            self.queue.put(task)
            logger.info(f"Task submitted: {task.name} (priority={task.priority}, category={task.category})")
    
    def start(self):
        """Start the task coordinator worker"""
        if self._worker_thread and self._worker_thread.is_alive():
            logger.warning("TaskCoordinator already running")
            return
        
        self._stop_event.clear()
        self._worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self._worker_thread.start()
        logger.info("TaskCoordinator started")
    
    def stop(self, timeout: float = 5.0):
        """Stop the task coordinator"""
        logger.info("Stopping TaskCoordinator...")
        self._stop_event.set()
        
        if self._worker_thread:
            self._worker_thread.join(timeout=timeout)
            if self._worker_thread.is_alive():
                logger.warning("TaskCoordinator did not stop gracefully")
        
        # Log final statistics
        self.log_statistics()
        logger.info("TaskCoordinator stopped")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get current task execution statistics"""
        with self._lock:
            return self.stats.copy()
    
    def log_statistics(self) -> None:
        """Log current task execution statistics"""
        with self._lock:
            logger.info("=== TaskCoordinator Statistics ===")
            logger.info(f"  Total submitted: {self.stats['tasks_submitted']}")
            logger.info(f"  Total completed: {self.stats['tasks_completed']}")
            logger.info(f"  Total failed: {self.stats['tasks_failed']}")
            logger.info(f"  Total execution time: {self.stats['total_execution_time']:.2f}s")
            
            if self.stats['by_category']:
                logger.info("  By category:")
                for category, cat_stats in self.stats['by_category'].items():
                    avg_time = cat_stats['total_time'] / cat_stats['completed'] if cat_stats['completed'] > 0 else 0
                    logger.info(f"    {category}: {cat_stats['completed']}/{cat_stats['submitted']} completed, "
                                f"{cat_stats['failed']} failed, avg time: {avg_time:.2f}s")
    
    def _process_queue(self):
        """Main worker loop - processes tasks from queue"""
        while not self._stop_event.is_set():
            try:
                # Get next task (blocks with timeout)
                try:
                    task = self.queue.get(timeout=1.0)
                except:
                    continue  # Timeout, check stop event
                
                # Check if we can run this task
                if not self._can_run_task(task):
                    # Put it back in queue and wait
                    self.queue.put(task)
                    time.sleep(0.1)  # Small delay to prevent busy waiting
                    continue
                
                # Mark category as blocked if needed
                with self._lock:
                    if task.blocks_category:
                        self.blocked_categories.add(task.blocks_category)
                        logger.debug(f"Category '{task.blocks_category}' blocked by task {task.name}")
                    
                    self.running_tasks[task.name] = task
                
                # Execute the task
                start_time = time.time()
                logger.debug(f"Executing task: {task.name} (priority={task.priority}, category={task.category})")
                
                try:
                    task.execute()
                    duration = time.time() - start_time
                    logger.debug(f"Task completed: {task.name} in {duration:.2f}s")
                    
                    # Update stats
                    with self._lock:
                        self.stats['tasks_completed'] += 1
                        self.stats['total_execution_time'] += duration
                        if task.category in self.stats['by_category']:
                            self.stats['by_category'][task.category]['completed'] += 1
                            self.stats['by_category'][task.category]['total_time'] += duration
                except Exception as e:
                    logger.error(f"Task execution failed: {task.name} - {e}", exc_info=True)
                    task.status = TaskStatus.FAILED
                    task.error = e
                    
                    # Update stats
                    with self._lock:
                        self.stats['tasks_failed'] += 1
                        if task.category in self.stats['by_category']:
                            self.stats['by_category'][task.category]['failed'] += 1
                
                finally:
                    # Clean up
                    with self._lock:
                        if task.name in self.running_tasks:
                            del self.running_tasks[task.name]
                        
                        if task.status == TaskStatus.COMPLETED:
                            self.completed_tasks[task.name] = task
                        
                        # Unblock category
                        if task.blocks_category:
                            self.blocked_categories.discard(task.blocks_category)
                            logger.debug(f"Category '{task.blocks_category}' unblocked")
                
            except Exception as e:
                logger.error(f"Error in task coordinator loop: {e}", exc_info=True)
                time.sleep(1.0)  # Prevent rapid error loops
    
    def _can_run_task(self, task: Task) -> bool:
        """Check if a task can run (dependencies met, category not blocked)"""
        with self._lock:
            # Check if category is blocked
            if task.category in self.blocked_categories:
                logger.debug(f"Task {task.name} waiting - category '{task.category}' is blocked")
                return False
            
            # Check dependencies
            for dep_name in task.dependencies:
                if dep_name not in self.completed_tasks:
                    logger.debug(f"Task {task.name} waiting for dependency: {dep_name}")
                    return False
                
                # Check if dependency succeeded
                dep_task = self.completed_tasks[dep_name]
                if dep_task.status != TaskStatus.COMPLETED:
                    logger.warning(f"Task {task.name} dependency {dep_name} failed")
                    task.status = TaskStatus.CANCELLED
                    return False
            
            return True
    
    def wait_for_task(self, task_name: str, timeout: float = None) -> Optional[Task]:
        """Wait for a specific task to complete and return it"""
        start_time = time.time()
        
        while True:
            with self._lock:
                if task_name in self.completed_tasks:
                    return self.completed_tasks[task_name]
            
            # Check timeout
            if timeout and (time.time() - start_time) > timeout:
                logger.warning(f"Timeout waiting for task: {task_name}")
                return None
            
            time.sleep(0.1)
    
    def get_task_status(self, task_name: str) -> Optional[TaskStatus]:
        """Get the current status of a task"""
        with self._lock:
            if task_name in self.running_tasks:
                return self.running_tasks[task_name].status
            elif task_name in self.completed_tasks:
                return self.completed_tasks[task_name].status
            return None
    
    def clear_completed(self, older_than_seconds: float = 3600):
        """Clear old completed tasks from memory"""
        with self._lock:
            cutoff_time = time.time() - older_than_seconds
            to_remove = [
                name for name, task in self.completed_tasks.items()
                if task.completed_at and task.completed_at < cutoff_time
            ]
            
            for name in to_remove:
                del self.completed_tasks[name]
            
            if to_remove:
                logger.info(f"Cleared {len(to_remove)} old completed tasks")


# Global task coordinator instance
_global_coordinator: Optional[TaskCoordinator] = None


def get_coordinator() -> TaskCoordinator:
    """Get or create the global task coordinator"""
    global _global_coordinator
    if _global_coordinator is None:
        _global_coordinator = TaskCoordinator()
        _global_coordinator.start()
    return _global_coordinator
