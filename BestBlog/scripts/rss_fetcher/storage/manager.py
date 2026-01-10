import os
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.sql import func
import datetime

Base = declarative_base()

class RSSItem(Base):
    __tablename__ = 'rss_items'

    id = Column(Integer, primary_key=True, autoincrement=True)
    author = Column(String(255))
    sourceName = Column(String(255))
    url = Column(Text)
    body = Column(Text)
    image_links = Column(Text) # JSON or comma-separated
    video_links = Column(Text)
    audio_links = Column(Text)
    publish_time = Column(DateTime)
    title = Column(String(500))
    intro = Column(Text)
    created_at = Column(DateTime, default=func.now())

class StorageManager:
    def __init__(self, config):
        self.config = config
        self.type = config['storage']['type']
        self.engine = None
        self.Session = None
        
        if self.type in ['mysql', 'sqlite']:
            self._init_db()
        elif self.type == 'excel':
            self.excel_path = config['storage']['excel']['path']

    def _init_db(self):
        if self.type == 'sqlite':
            db_path = self.config['storage']['sqlite']['path']
            # Ensure absolute path if needed, or relative to script
            self.engine = create_engine(f'sqlite:///{db_path}')
        elif self.type == 'mysql':
            c = self.config['storage']['mysql']
            url = f"mysql+pymysql://{c['user']}:{c['password']}@{c['host']}:{c['port']}/{c['database']}"
            self.engine = create_engine(url)
        
    def is_item_exists(self, url):
        """
        Check if an item with the given url already exists in the storage.
        """
        if self.type in ['mysql', 'sqlite']:
            session = self.Session()
            try:
                exists = session.query(RSSItem).filter_by(url=url).first()
                return exists is not None
            finally:
                session.close()
        elif self.type == 'excel':
            if os.path.exists(self.excel_path):
                try:
                    df = pd.read_excel(self.excel_path)
                    if 'url' in df.columns:
                        return url in df['url'].values
                except Exception:
                    pass
            return False
        return False

    def save_item(self, item_data):
        """
        item_data: dict with keys matching the columns
        """
        # Ensure lists are converted to strings for storage
        for key in ['image_links', 'video_links', 'audio_links']:
            if isinstance(item_data.get(key), list):
                item_data[key] = ','.join(item_data[key])
        
        # Ensure publish_time is a datetime object or None
        if isinstance(item_data.get('publish_time'), str):
            # Simple parsing, might need more robust parsing depending on RSS format
            # But feedparser usually returns struct_time, we'll handle that in fetcher
            pass

        if self.type in ['mysql', 'sqlite']:
            session = self.Session()
            try:
                # Check for duplicates based on url
                exists = session.query(RSSItem).filter_by(url=item_data['url']).first()
                if not exists:
                    rss_item = RSSItem(**item_data)
                    session.add(rss_item)
                    session.commit()
                    print(f"Saved to DB: {item_data.get('title')}")
                else:
                    print(f"Skipped (Duplicate): {item_data.get('title')}")
            except Exception as e:
                print(f"Error saving to DB: {e}")
                session.rollback()
            finally:
                session.close()

        elif self.type == 'excel':
            self._save_to_excel(item_data)

    def _save_to_excel(self, item_data):
        # Load existing or create new
        if os.path.exists(self.excel_path):
            try:
                df = pd.read_excel(self.excel_path)
            except Exception:
                df = pd.DataFrame()
        else:
            df = pd.DataFrame()

        # Check duplicate
        if not df.empty and 'url' in df.columns:
            if item_data['url'] in df['url'].values:
                print(f"Skipped (Duplicate Excel): {item_data.get('title')}")
                return

        new_row = pd.DataFrame([item_data])
        df = pd.concat([df, new_row], ignore_index=True)
        
        try:
            df.to_excel(self.excel_path, index=False)
            print(f"Saved to Excel: {item_data.get('title')}")
        except Exception as e:
            print(f"Error saving to Excel: {e}")
