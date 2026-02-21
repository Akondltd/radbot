import logging
import traceback
import sys
from PySide6.QtCore import QObject, QRunnable, Signal, Slot

class WorkerSignals(QObject):
    '''
    Defines the signals available from a running worker thread.

    Supported signals are:

    finished
        No data

    error
        `tuple` (exctype, value, traceback.format_exc())

    result
        `object` data returned from processing, anything

    progress
        `int` indicating % progress
    '''
    finished = Signal()
    error = Signal(tuple)
    result = Signal(object)
    progress = Signal(int)


class Worker(QRunnable):
    '''
    Worker thread for executing long-running tasks without blocking the UI.
    Inherits from QRunnable to be managed by a QThreadPool.
    '''

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @Slot()
    def run(self):
        '''
        Execute the worker's task.
        '''
        try:
            result = self.fn(*self.args, **self.kwargs)
        except Exception as e:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            try:
                self.signals.error.emit((exctype, value, traceback.format_exc()))
            except RuntimeError:
                pass  # Signal source deleted (app shutting down)
        else:
            try:
                self.signals.result.emit(result)
            except RuntimeError:
                pass  # Signal source deleted (app shutting down)
        finally:
            try:
                self.signals.finished.emit()
            except RuntimeError:
                pass  # Signal source deleted (app shutting down)


class QtBaseService(QObject):
    """Base class for all services that will run in a Qt-safe manner."""
    def __init__(self, service_name: str):
        super().__init__()
        self.service_name = service_name
        self.logger = logging.getLogger(f'service.{self.service_name}')
        self.logger.setLevel(logging.DEBUG)

    def start(self):
        """Subclasses must implement this to start their specific work."""
        raise NotImplementedError("Subclasses must implement the start() method.")

    def stop(self):
        """Subclasses must implement this to safely stop their work."""
        self.logger.info(f"Service {self.service_name} stop requested.")
        raise NotImplementedError("Subclasses must implement the stop() method.")
