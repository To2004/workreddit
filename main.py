import os
from RedditScraper import RedditScraper

if __name__ == "__main__":
    # Load Reddit API credentials from environment variables
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    user_agent = "my_reddit_scraper/0.1"

    # Ensure that the credentials are set
    if not client_id or not client_secret:
        raise ValueError("Please set the REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET environment variables.")

    # Initialize the Reddit scraper
    scraper = RedditScraper(client_id, client_secret, user_agent)

    # List of subreddits to scrape
    subreddits = ['cybersecurity_help']

    # Set the number of posts to scrape
    limit = 10  # Adjust this number to your desired limit

    try:
        # Start scraping and saving data
        scraper.scrape_and_save(subreddits, limit=limit,
                                output_folder="reddit_data")  # Change path as needed
    except KeyboardInterrupt:
        print("Scraping interrupted. Saving collected data before exiting.")
