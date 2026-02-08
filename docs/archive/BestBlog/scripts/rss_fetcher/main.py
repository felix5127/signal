import asyncio
import os
import sys
import config

# Add current directory to sys.path to ensure modules can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from storage.manager import StorageManager
from utils.opml_parser import parse_opml
from modules.article_fetcher import ArticleFetcher
from modules.podcast_fetcher import PodcastFetcher
from modules.twitter_fetcher import TwitterFetcher
from modules.video_fetcher import VideoFetcher

def load_config():
    # Return a dictionary-like object or the module itself, 
    # but since existing code expects a dict structure (e.g. config['storage']),
    # we need to adapt it.
    return {
        'storage': config.STORAGE,
        'playwright': config.PLAYWRIGHT,
        'processing': config.PROCESSING
    }

async def run_module(module_name, opml_filename, fetcher_class, config, storage):
    print(f"\n=== Starting Module: {module_name} ===")
    opml_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), opml_filename)
    
    if not os.path.exists(opml_path):
        print(f"OPML file not found: {opml_path}")
        return

    feeds = parse_opml(opml_path)
    print(f"Found {len(feeds)} feeds in {opml_filename}")

    fetcher = fetcher_class(config, storage)
    await fetcher.start_browser()
    
    try:
        for feed in feeds:
            await fetcher.fetch_feed(feed)
    finally:
        await fetcher.close_browser()
    
    print(f"=== Finished Module: {module_name} ===\n")

async def main():
    cfg = load_config()
    storage = StorageManager(cfg)
    
    # Define tasks
    tasks = [
        ('Articles', 'BestBlogs_RSS_Articles.opml', ArticleFetcher),
        ('Podcasts', 'BestBlogs_RSS_Podcasts.opml', PodcastFetcher),
        ('Twitters', 'BestBlogs_RSS_Twitters.opml', TwitterFetcher),
        ('Videos', 'BestBlogs_RSS_Videos.opml', VideoFetcher)
    ]

    for name, opml_file, fetcher_cls in tasks:
        await run_module(name, opml_file, fetcher_cls, cfg, storage)

async def loop_main():
    while True:
        print(f"Starting fetch cycle at {datetime.datetime.now()}")
        await main()
        print("Cycle finished. Sleeping for 1 hour...")
        await asyncio.sleep(3600)  # Sleep for 1 hour

if __name__ == "__main__":
    import datetime
    asyncio.run(loop_main())
