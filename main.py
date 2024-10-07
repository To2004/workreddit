import os
import pandas as pd
import logging
import argparse
from dotenv import load_dotenv
from RedditScraper import RedditScraper
from RedditDataProcessor import RedditDataProcessor

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def scrape_reddit(subreddits, limit, output_folder):
    client_id = os.getenv('REDDIT_CLIENT_ID')
    client_secret = os.getenv('REDDIT_CLIENT_SECRET')
    user_agent = os.getenv('REDDIT_USER_AGENT')

    if not all([client_id, client_secret, user_agent]):
        logger.error("Reddit API credentials not found. Please check your .env file.")
        return

    scraper = RedditScraper(client_id, client_secret, user_agent)

    try:
        scraper.scrape_and_save(subreddits, limit=limit, output_folder=output_folder)
        logger.info(f"Scraping completed for subreddits: {', '.join(subreddits)}")
    except KeyboardInterrupt:
        logger.warning("Scraping interrupted. Saving collected data before exiting.")
    except Exception as e:
        logger.error(f"An error occurred during scraping: {e}")

def process_reddit_data(subreddit, base_path):
    try:
        # Load the posts and comments data
        posts_file = os.path.join(base_path, subreddit, f"{subreddit}_posts.csv")
        comments_file = os.path.join(base_path, subreddit, f"{subreddit}_comments.csv")
        
        logger.info(f"Loading data for subreddit: {subreddit}")
        posts_data = pd.read_csv(posts_file)
        comments_data = pd.read_csv(comments_file)
        
        # Initialize the RedditDataProcessor
        processor = RedditDataProcessor(subreddit)
        
        # Define the output file path for saving results
        output_file_path = os.path.join(base_path, subreddit, "condensed_data.csv")
        
        # Process posts and save results
        processor.process_posts(posts_data, comments_data, output_file_path)
        logger.info(f"Processing completed for subreddit: {subreddit}")
    
    except FileNotFoundError as e:
        logger.error(f"Error processing subreddit {subreddit}: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred while processing {subreddit}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Reddit Scraper and Data Processor")
    parser.add_argument("--scrape", action="store_true", help="Scrape Reddit data")
    parser.add_argument("--process", action="store_true", help="Process Reddit data")
    parser.add_argument("--subreddits", nargs="+", default=["techsupport"], help="List of subreddits to scrape/process")
    parser.add_argument("--limit", type=int, default=100, help="Number of posts to scrape (default: 100)")
    parser.add_argument("--output", default=os.getenv('OUTPUT_FOLDER', './reddit_data'), help="Output folder path")

    args = parser.parse_args()

    if args.scrape:
        scrape_reddit(args.subreddits, args.limit, args.output)
    
    if args.process:
        for subreddit in args.subreddits:
            process_reddit_data(subreddit, args.output)

    if not (args.scrape or args.process):
        logger.warning("No action specified. Use --scrape to scrape data or --process to process data.")

if __name__ == "__main__":
    main()
