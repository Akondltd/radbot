"""
Service Coordinator - Unified management for all services with task coordination.

Provides a clean interface to manage both threading-based and Qt-based services
with proper ordering and dependency management.
"""

import logging
from typing import Any, Dict, List, Optional, Union
from PySide6.QtCore import QObject, Signal

from services.qt_base_service import QtBaseService
from services.task_coordinator import TaskCoordinator, Task, TaskPriority

logger = logging.getLogger(__name__)


class ServiceCategory:
    """Service categories for grouping and coordination"""
    # Core infrastructure
    CORE = "core"                    # Database, wallet, etc.
    
    # Data fetching
    DATA_FETCH = "data_fetch"        # Balance updates, price fetches
    
    # Analysis
    ANALYSIS = "analysis"            # Signal generation, technical indicators
    
    # Execution
    EXECUTION = "execution"          # Trade execution
    
    # UI Updates
    UI = "ui"                        # UI refresh, icon caching
    
    # Background
    BACKGROUND = "background"        # Stats, optimization, cleanup


class ServiceCoordinator(QObject):
    """
    Unified coordinator for all services (threading and Qt-based).
    Integrates with TaskCoordinator for proper ordering.
    """
    
    # Signals
    service_started = Signal(str)      # service_name
    service_stopped = Signal(str)      # service_name
    service_error = Signal(str, str)   # service_name, error_message
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Service registry
        self.services: Dict[str, Any] = {}
        self.service_categories: Dict[str, str] = {}  # service_name -> category
        
        # Task coordinator for execution ordering
        self.task_coordinator = TaskCoordinator()
        self.task_coordinator.start()
        
        self.logger.info("ServiceCoordinator initialized")
    
    def register_service(
        self,
        service,  # Any service with a name/service_name attribute
        category: str = ServiceCategory.BACKGROUND,
        dependencies: List[str] = None
    ):
        """
        Register a service with the coordinator.
        
        Args:
            service: The service instance
            category: Service category for grouping
            dependencies: List of service names this service depends on
        """
        service_name = getattr(service, 'name', None) or getattr(service, 'service_name', 'unknown')
        
        if service_name in self.services:
            self.logger.warning(f"Service '{service_name}' already registered")
            return
        
        self.services[service_name] = service
        self.service_categories[service_name] = category
        
        self.logger.info(f"Registered service: {service_name} (category: {category})")
    
    def start_service(self, service_name: str, priority: TaskPriority = TaskPriority.NORMAL):
        """Start a specific service"""
        if service_name not in self.services:
            self.logger.error(f"Service '{service_name}' not registered")
            return
        
        service = self.services[service_name]
        category = self.service_categories.get(service_name, ServiceCategory.BACKGROUND)
        
        # Create a task to start the service
        task = Task(
            priority=priority,
            name=f"start_{service_name}",
            category=category,
            func=self._start_service_impl,
            args=(service_name,)
        )
        
        self.task_coordinator.submit(task)
    
    def _start_service_impl(self, service_name: str):
        """Implementation of service start"""
        try:
            service = self.services[service_name]
            service.start()
            self.service_started.emit(service_name)
            self.logger.info(f"Service started: {service_name}")
        except Exception as e:
            error_msg = str(e)
            self.service_error.emit(service_name, error_msg)
            self.logger.error(f"Failed to start service {service_name}: {e}", exc_info=True)
            raise
    
    def stop_service(self, service_name: str):
        """Stop a specific service"""
        if service_name not in self.services:
            self.logger.error(f"Service '{service_name}' not registered")
            return
        
        try:
            service = self.services[service_name]
            service.stop()
            self.service_stopped.emit(service_name)
            self.logger.info(f"Service stopped: {service_name}")
        except Exception as e:
            self.logger.error(f"Error stopping service {service_name}: {e}", exc_info=True)
    
    def start_category(self, category: str, priority: TaskPriority = TaskPriority.NORMAL):
        """Start all services in a category"""
        services_in_category = [
            name for name, cat in self.service_categories.items()
            if cat == category
        ]
        
        self.logger.info(f"Starting {len(services_in_category)} services in category: {category}")
        
        for service_name in services_in_category:
            self.start_service(service_name, priority)
    
    def stop_category(self, category: str):
        """Stop all services in a category"""
        services_in_category = [
            name for name, cat in self.service_categories.items()
            if cat == category
        ]
        
        self.logger.info(f"Stopping {len(services_in_category)} services in category: {category}")
        
        for service_name in services_in_category:
            self.stop_service(service_name)
    
    def start_all(self):
        """Start all services in category order.
        
        Services are started directly on the calling (main/GUI) thread
        because Qt services use QTimers which require the main event loop.
        """
        self.logger.info("Starting all services...")
        
        category_order = [
            ServiceCategory.CORE,
            ServiceCategory.DATA_FETCH,
            ServiceCategory.ANALYSIS,
            ServiceCategory.EXECUTION,
            ServiceCategory.UI,
            ServiceCategory.BACKGROUND,
        ]
        
        for category in category_order:
            services_in_category = [
                name for name, cat in self.service_categories.items()
                if cat == category
            ]
            for service_name in services_in_category:
                self._start_service_impl(service_name)
    
    def stop_all(self):
        """Stop all services"""
        self.logger.info("Stopping all services...")
        
        # Stop in reverse order (background first, core last)
        category_order = [
            ServiceCategory.BACKGROUND,
            ServiceCategory.UI,
            ServiceCategory.EXECUTION,
            ServiceCategory.ANALYSIS,
            ServiceCategory.DATA_FETCH,
            ServiceCategory.CORE,
        ]
        
        for category in category_order:
            self.stop_category(category)
        
        # Stop task coordinator
        self.task_coordinator.stop()
    
    def submit_task(
        self,
        name: str,
        func: callable,
        priority: TaskPriority = TaskPriority.NORMAL,
        category: str = ServiceCategory.BACKGROUND,
        dependencies: List[str] = None,
        blocks_category: str = None,
        **kwargs
    ) -> Task:
        """
        Submit a one-off task to the coordinator.
        
        Args:
            name: Task name
            func: Function to execute
            priority: Task priority
            category: Task category
            dependencies: List of task names to wait for
            blocks_category: Block all tasks in this category while running
            **kwargs: Additional arguments for Task
        
        Returns:
            The created Task object
        """
        task = Task(
            priority=priority,
            name=name,
            category=category,
            func=func,
            dependencies=dependencies or [],
            blocks_category=blocks_category,
            **kwargs
        )
        
        self.task_coordinator.submit(task)
        return task
    
    def get_service_status(self) -> Dict[str, Dict]:
        """Get status of all services"""
        status = {}
        
        for service_name, service in self.services.items():
            category = self.service_categories.get(service_name, "unknown")
            
            # Check if service is running
            is_running = False
            is_running = getattr(service, 'running', False)
            
            status[service_name] = {
                "category": category,
                "running": is_running,
                "type": type(service).__name__
            }
        
        return status
    
    def get_service(self, name: str) -> Optional[Any]:
        """Get a service by name"""
        return self.services.get(name)
    
    def get_services_by_category(self, category: str) -> List[Any]:
        """Get all services in a category"""
        return [
            self.services[name]
            for name, cat in self.service_categories.items()
            if cat == category
        ]


# Example usage and migration guide
"""
MIGRATION GUIDE:

1. Old way (direct service management):
   ```
   balance_service = WalletBalanceService(...)
   balance_service.start()
   
   trade_monitor = TradeMonitor(...)
   trade_monitor.start()
   ```

2. New way (coordinated):
   ```
   coordinator = ServiceCoordinator()
   
   # Register services
   coordinator.register_service(
       balance_service,
       category=ServiceCategory.DATA_FETCH
   )
   
   coordinator.register_service(
       trade_monitor,
       category=ServiceCategory.EXECUTION,
       dependencies=["wallet_balance"]  # Wait for balance service
   )
   
   # Start all (they'll start in proper order)
   coordinator.start_all()
   ```

3. Submitting coordinated tasks:
   ```
   # This will wait for balance update before executing
   coordinator.submit_task(
       name="execute_trade_123",
       func=execute_trade,
       args=(trade_id,),
       category=ServiceCategory.EXECUTION,
       dependencies=["update_wallet_balance"],
       blocks_category=ServiceCategory.EXECUTION  # No other trades while running
   )
   ```
"""
