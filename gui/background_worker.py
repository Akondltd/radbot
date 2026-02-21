from PySide6.QtCore import QObject, Signal, QThread
import traceback
import logging
from config.database_config import (
    DATABASE_PATH,
    TOKENS_TABLE_NAME,
    TOKENS_TABLE_COLUMNS,
    TRADE_PAIRS_TABLE_NAME,
    TRADE_PAIRS_TABLE_COLUMNS,
    SELECTED_PAIRS_TABLE_NAME,
    SELECTED_PAIRS_TABLE_COLUMNS
)

logger = logging.getLogger(__name__)

class DatabaseInitWorker(QObject):
    """Worker class for database initialization"""
    progress = Signal(str)
    finished = Signal(bool, str)
    error = Signal(str)

    def __init__(self, db):
        super().__init__()
        self.db = db
        self.conn = None
        self.cursor = None

    def run(self):
        """Start the initialization process"""
        try:
            # Get connection and cursor from database instance
            self.conn = self.db.get_connection()
            self.cursor = self.db.get_cursor()
            
            self.progress.emit("Database initialization started...")
            
            # Check if database is empty
            self.cursor.execute(f"SELECT COUNT(*) FROM {TOKENS_TABLE_NAME}")
            count = self.cursor.fetchone()[0]
            if count == 0:
                self.progress.emit("Database empty - populating tokens...")
                self._populate_database()
            else:
                self.progress.emit(f"Database already populated with {count} tokens")
            
            self.finished.emit(True, "Database initialization completed successfully")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {str(e)}", exc_info=True)
            self.error.emit(str(e))
            raise

    def _populate_database(self):
        """Populate database with tokens"""
        try:
            # Start transaction
            self.cursor.execute('BEGIN TRANSACTION')
            
            # Populate database
            self.db.populate_database()
            
            # Verify population
            self.cursor.execute(f"SELECT COUNT(*) FROM {TOKENS_TABLE_NAME}")
            count = self.cursor.fetchone()[0]
            logger.info(f"Tokens in database: {count}")
            
            # Commit transaction
            self.conn.commit()
            
            logger.info(f"Database populated successfully with {count} tokens")
            
        except Exception as e:
            logger.error(f"Error populating database: {str(e)}", exc_info=True)
            self.conn.rollback()
            raise

class DatabaseInitThread(QThread):
    """Thread for database initialization"""
    progress = Signal(str)
    finished = Signal(bool, str)
    error = Signal(str)

    def __init__(self, db):
        super().__init__()
        self.db = db
        self.worker = DatabaseInitWorker(db)
        
    def run(self):
        """Start the initialization process"""
        # Move worker to thread and connect signals
        self.worker.moveToThread(self)
        self.worker.progress.connect(self.progress)
        self.worker.finished.connect(self.finished)
        self.worker.error.connect(self.error)
        
        # Start worker
        self.worker.run()
        
    def get_connection(self):
        """Get the database connection after initialization"""
        return self.worker.conn
        
    def get_cursor(self):
        """Get the database cursor after initialization"""
        return self.worker.cursor
