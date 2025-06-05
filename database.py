import os
import time
import sqlite3
import logging
import shutil
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
DB_PATH = "diamond_store.db"
DAMASCUS_TZ = timezone(timedelta(hours=3))

# Logger
logger = logging.getLogger(__name__)

# Date and time adapters for SQLite
def adapt_datetime(dt):
    """Convert datetime to a SQLite-compatible format."""
    return dt.isoformat()

def convert_datetime(text):
    """Convert text from SQLite to datetime."""
    return datetime.fromisoformat(text)

sqlite3.register_adapter(datetime, adapt_datetime)
sqlite3.register_converter("timestamp", convert_datetime)

# Database connection function
def get_connection():
    """Create a database connection with improved settings."""
    for i in range(5):  # Retry connection 5 times
        try:
            conn = sqlite3.connect(
                DB_PATH,
                timeout=30.0,  # Increased timeout
                isolation_level=None,  # Enable manual transaction control
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
            )
            conn.execute('PRAGMA journal_mode=WAL')  # Use WAL mode
            conn.execute('PRAGMA busy_timeout=30000')  # Set busy timeout
            return conn
        except sqlite3.OperationalError as e:
            if i == 4:  # If all attempts failed
                raise e
            time.sleep(1)  # Wait a second before retrying

def init_wal():
    """Initialize WAL mode for the database."""
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute('PRAGMA journal_mode=WAL')
        conn.commit()
    except Exception as e:
        logger.error(f"Error initializing WAL: {e}")
    finally:
        if conn:
            conn.close()

# Database initialization function
def init_db():
    """Initialize the database with security, performance, and backup improvements."""
    try:
        # Create a backup before any changes
        if os.path.exists(DB_PATH):
            backup_path = f'backup/diamond_store_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
            os.makedirs('backup', exist_ok=True)
            shutil.copy2(DB_PATH, backup_path)

        # Create a connection to the database with improved settings
        conn = get_connection()
        c = conn.cursor()

        # Enable advanced settings for performance and security
        c.executescript('''
            -- Enable foreign key constraints
            PRAGMA foreign_keys = ON;

            -- Improve write performance
            PRAGMA journal_mode = WAL;

            -- Improve concurrency
            PRAGMA synchronous = NORMAL;

            -- Improve cache size
            PRAGMA cache_size = -2000;

            -- User table with improvements
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                balance REAL DEFAULT 0.0 CHECK (balance >= 0),
                joined_date TEXT NOT NULL,
                last_activity TEXT NOT NULL,
                status TEXT DEFAULT 'active' CHECK (status IN ('active', 'banned', 'suspended')),
                account_data TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            -- Balance history table
            CREATE TABLE IF NOT EXISTS balance_history (
                history_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                old_balance REAL NOT NULL,
                new_balance REAL NOT NULL,
                change_amount REAL NOT NULL,  -- Renamed amount to change_amount
                transaction_type TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            );

            -- Improved orders table
            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_type TEXT NOT NULL CHECK (product_type IN ('game', 'app')),
                product_id TEXT NOT NULL,
                amount TEXT NOT NULL,
                price REAL NOT NULL,
                created_at TEXT NOT NULL,
                status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'rejected', 'expired')),
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            );

            -- Transactions table
            CREATE TABLE IF NOT EXISTS transactions (
                tx_id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                type TEXT NOT NULL CHECK (type IN ('deposit', 'withdrawal')),
                payment_method TEXT NOT NULL,
                payment_details TEXT,
                original_amount REAL,
                original_currency TEXT,
                created_at TEXT NOT NULL,
                status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'rejected', 'expired')),
                reject_reason TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            );

            -- Admin logs table
            CREATE TABLE IF NOT EXISTS admin_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                details TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            -- Create index for faster user lookups
            CREATE INDEX IF NOT EXISTS idx_users_user_id ON users (user_id);

            -- Create index for order status lookups
            CREATE INDEX IF NOT EXISTS idx_orders_status ON orders (status);

            -- Create index for transaction status lookups
            CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions (status);
        ''')

        conn.commit()
        logger.info("Database initialized successfully.")

    except sqlite3.Error as e:
        logger.error(f"Database initialization error: {e}")

    finally:
        if conn:
            conn.close()