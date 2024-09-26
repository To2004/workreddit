from RedditScraper import RedditScraper

if __name__ == "__main__":
    client_id = "P2uzdkS7eFXodLmNuH7qaQ"
    client_secret = "s9x-kA_VtE4MjBwz8yE1RlSd16pOBA"
    user_agent = "my_reddit_scraper/0.1 by Character_Guava7050"

    scraper = RedditScraper(client_id, client_secret, user_agent)
    subreddits = [  'cybersecurity_help']

    # Set the number of posts you want to scrape
    limit = 10  # Change this number to your desired limit

    try:
        scraper.scrape_and_save(subreddits, limit=limit,
                                output_folder="C:\\Users\\Asus\\Documents\\workreddit\\reddit_data")
    except KeyboardInterrupt:
        print("Scraping interrupted. Saving collected data before exiting.")