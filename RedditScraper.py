import time
import praw
import pandas as pd
import os
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO)

class RedditScraper:
    def __init__(self, client_id, client_secret, user_agent):
        """
        Initializes the RedditScraper with the provided credentials.

        :param client_id: Reddit API client ID
        :param client_secret: Reddit API client secret
        :param user_agent: User agent string for the Reddit API
        """
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
            request_timeout=30  # Increased timeout to 30 seconds
        )

    def normalize_text(self, text):
        """
        Converts full-width Unicode characters to normal ASCII characters.

        :param text: The input text to normalize
        :return: Normalized text or None if the input is empty
        """
        if text:
            return ''.join([chr(ord(c) - 0xFEE0) if 0xFF01 <= ord(c) <= 0xFF5E else c for c in text])
        return None  # Return None if text is None or empty

    def extract_links_and_images(self, text):
        """
        Extracts image links (.jpg, .png, etc.) and other regular links from the given text.

        :param text: The input text to extract links from
        :return: A string of links/images found or "No links or images" if none are found
        """
        if text:
            image_links = re.findall(r'(https?://\S+\.(?:jpg|jpeg|png|gif))', text)
            other_links = re.findall(r'(https?://\S+)', text)

            if image_links:
                return ', '.join(image_links)  # Join multiple image links
            elif other_links:
                return ', '.join(other_links)  # Join other links if no images

        return "No links or images"  # Explicitly return this if no links or images are found

    def scrape_subreddit(self, subreddit, total_limit):
        """
        Scrapes posts and comments from the specified subreddit.

        :param subreddit: The subreddit to scrape
        :param total_limit: The maximum number of posts to scrape
        :return: Two lists containing post data and comment data
        """
        posts_data = []
        comments_data = []

        try:
            subreddit_obj = self.reddit.subreddit(subreddit)
            logging.info(f"Successfully connected to subreddit: {subreddit}")

            submission_count = 0
            start_time = time.time()

            for submission in subreddit_obj.top(limit=None):
                logging.info(f"Processing submission: {submission.title} (ID: {submission.id})")

                if submission_count >= total_limit:
                    break

                if submission.num_comments > 1:
                    normalized_title = self.normalize_text(submission.title)
                    normalized_selftext = self.normalize_text(submission.selftext)

                    post_info = {
                        "Post ID": submission.id or None,
                        "Title": normalized_title or None,
                        "Self Text": normalized_selftext or None,
                        "Post Type": submission.url.split('.')[-1] if submission.url else None,
                        "Upvotes": submission.score if submission.score is not None else None,
                        "Comments Count": submission.num_comments if submission.num_comments is not None else None,
                        "Author": submission.author.name if submission.author and submission.author.name else None,  # Check author
                        "Created Time (UTC)": submission.created_utc if submission.created_utc else None,
                        "Link/Image": self.extract_links_and_images(submission.selftext)  # Explicitly set to None if no link/image found
                    }
                    posts_data.append(post_info)

                    submission.comments.replace_more(limit=None)  # Fetch all comments
                    for comment in submission.comments.list():
                        normalized_body = self.normalize_text(comment.body)

                        comment_info = {
                            "Post ID": submission.id or None,
                            "Comment ID": comment.id or None,
                            "Comment Body": normalized_body or None,
                            "Comment Upvotes": comment.score if comment.score is not None else None,
                            "Comment Created Time (UTC)": comment.created_utc if comment.created_utc else None,
                            "Comment Author": comment.author.name if comment.author and comment.author.name else None,  # Check author
                            "Link/Image": self.extract_links_and_images(comment.body)  # Explicitly set to None if no link/image found
                        }
                        comments_data.append(comment_info)

                    submission_count += 1

                    # Check the time and sleep if necessary
                    elapsed_time = time.time() - start_time
                    if submission_count % 90 == 0:
                        if elapsed_time < 60:
                            time.sleep(60 - elapsed_time)
                        start_time = time.time()

        except praw.exceptions.APIException as e:
            if e.error_type == "RATELIMIT":
                wait_time = int(e.message.split(' ')[-2])
                logging.info(f"Rate limit exceeded. Sleeping for {wait_time + 10} seconds.")
                time.sleep(wait_time + 10)  # Sleep with a buffer
                return self.scrape_subreddit(subreddit, total_limit)
            else:
                logging.error(f"An error occurred while scraping subreddit {subreddit}: {e}")

        except Exception as e:  # Catch all other exceptions
            logging.error(f"An unexpected error occurred: {e}")

        return posts_data, comments_data

    def save_to_csv(self, data, file_path):
        """
        Saves the provided data to a CSV file.

        :param data: The data to save
        :param file_path: The path where the CSV file will be saved
        """
        if data:  # Only save if there is data to save
            df = pd.DataFrame(data)
            try:
                df.to_csv(file_path, index=False)
                logging.info(f"Data successfully saved to {file_path}.")
            except Exception as e:
                logging.error(f"Error saving CSV file: {e}")

    def scrape_and_save(self, subreddits, limit=None, output_folder="C:\\Users\\Asus\\Documents\\workreddit\\reddit_data"):
        """
        Scrapes the specified subreddits and saves the data to CSV files.

        :param subreddits: List of subreddits to scrape
        :param limit: Maximum number of posts to scrape from each subreddit
        :param output_folder: Folder path to save the output CSV files
        """
        for subreddit in subreddits:
            logging.info(f"Scraping subreddit: {subreddit}")
            posts_data, comments_data = [], []
            folder_path = f"{output_folder}/{subreddit}"
            os.makedirs(folder_path, exist_ok=True)

            try:
                posts_data, comments_data = self.scrape_subreddit(subreddit, limit)
                self.save_to_csv(posts_data, f"{folder_path}/{subreddit}_posts.csv")
                self.save_to_csv(comments_data, f"{folder_path}/{subreddit}_comments.csv")

            except Exception as e:
                logging.error(f"An error occurred: {e}")
            finally:
                # Always save backups of the data
                self.save_to_csv(posts_data, f"{folder_path}/{subreddit}_posts_backup.csv")
                self.save_to_csv(comments_data, f"{folder_path}/{subreddit}_comments_backup.csv")

            # Pause between subreddits
            time.sleep(5)  # Sleep for 5 seconds between different subreddit scrapes
