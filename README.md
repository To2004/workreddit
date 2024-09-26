# Workreddit

## Description

**Workreddit** is a Python-based Reddit scraper designed to extract and organize data from various subreddits. The primary goal of this project is to collect insightful discussions and solutions related to technology and troubleshooting from Reddit, making it easier for users to retrieve and analyze this information.

## Features

- **Data Extraction:** Scrapes posts and comments from specified subreddits, including titles, bodies, upvotes, and authors.
- **Link/Image Extraction:** Automatically extracts any images or links included in the posts or comments.
- **Filtering:** Optionally filters posts based on the number of comments to focus on more substantial discussions (e.g., posts with more than 3,000 comments).
- **Data Organization:** Saves scraped data in CSV format for easy access and analysis.

## Limitations

- **Reddit API Restrictions:** The scraper may face limitations from the Reddit API, especially when attempting to scrape high-comment threads. If a post exceeds the comment limit or the API rate limit, it may not be fully retrievable.
- **Handling Deleted Users:** The scraper checks for deleted user accounts, ensuring the data integrity of author information.
- **Data Completeness:** While the scraper aims to collect extensive data, certain posts may not contain images or links, which will be noted in the output.

## Getting Started

### Prerequisites

- Python 3.x
- Required Python libraries (e.g., `praw`, `pandas`, `requests`, `re`)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/To2004/workreddit.git
