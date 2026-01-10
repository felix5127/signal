
import os
import platform

# Platform
PLATFORM = platform.system()

# Storage Configuration
STORAGE = {
    "type": "excel",  # options: mysql, sqlite, excel
    "sqlite": {
        "path": "rss_data.db"
    },
    "mysql": {
        "host": "localhost",
        "port": 3306,
        "user": "root",
        "password": "password",
        "database": "rss_db"
    },
    "excel": {
        "path": "rss_data.xlsx"
    }
}

# Playwright Configuration
PLAYWRIGHT = {
    "headless": False,
    "timeout": 30000
}

# Processing Configuration
PROCESSING = {
    "max_items_per_feed": 5
}

# CDP Configuration
CDP_DEBUG_PORT = 9222
CUSTOM_BROWSER_PATH = None
SAVE_LOGIN_STATE = True
USER_DATA_DIR = "user_data_%s"
BROWSER_LAUNCH_TIMEOUT = 30
AUTO_CLOSE_BROWSER = True
HEADLESS = PLAYWRIGHT["headless"]

