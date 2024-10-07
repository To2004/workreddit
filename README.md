# Workreddit

## Description
**Workreddit** is an advanced Python-based Reddit data processing tool designed to extract, analyze, and organize data from various subreddits. The project now incorporates AI-powered analysis to provide deeper insights into Reddit discussions, particularly focusing on technology and troubleshooting topics.

## Features
- **Data Extraction:** Scrapes posts and comments from specified subreddits, including titles, bodies, upvotes, and authors.
- **Link/Image Extraction:** Automatically extracts any images or links included in the posts or comments.
- **Filtering:** Optionally filters posts based on the number of comments to focus on more substantial discussions.
- **Data Organization:** Saves scraped data in CSV format for easy access and analysis.
- **AI-Powered Analysis:** Utilizes Azure OpenAI services to analyze post content, identify user complaints, and provide relevant solutions or recommendations.
- **Cybersecurity Relevance Assessment:** Evaluates the cybersecurity relevance of each post, categorizing them as High, Medium, Low, or None.
- **Checkpoint System:** Implements a robust checkpoint mechanism to handle large datasets and allow for interrupted processing to be resumed.

## AI Integration
The `RedditDataProcessor` class now includes:
- **Complaint Analysis:** Identifies and summarizes the core issue in each post.
- **Diagnosis:** Provides a brief psychological explanation of the user's complaint.
- **Solution Finding:** Analyzes comments to find the most relevant solutions or recommendations.
- **Confidence Scoring:** Assigns a confidence score to each solution or recommendation.

## Limitations
- **Reddit API Restrictions:** The scraper may face limitations from the Reddit API, especially when attempting to scrape high-comment threads.
- **Handling Deleted Users:** The scraper checks for deleted user accounts, ensuring the data integrity of author information.
- **AI Analysis Accuracy:** While the AI-powered analysis provides valuable insights, its accuracy depends on the quality and clarity of the post and comment data.
- **Processing Time:** Due to the AI analysis, processing large datasets may take considerable time.

## Getting Started

### Prerequisites
- Python 3.x
- Required Python libraries (e.g., `praw`, `pandas`, `requests`, `re`, `langchain_openai`)
- Azure OpenAI API key and endpoint

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/To2004/workreddit.git
   ```
2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up environment variables for Azure OpenAI and LangChain (refer to the code for specific variable names).

### Usage
1. Initialize the `RedditDataProcessor` with your desired subreddit:
   ```python
   processor = RedditDataProcessor("techsupport")
   ```
2. Use the `process_posts` method to analyze Reddit data:
   ```python
   processor.process_posts(posts_data, comments_data, output_file_path)
   ```

## Data Processing Workflow
1. **Data Extraction:** Scrape posts and comments from the specified subreddit.
2. **AI Analysis:** Each post is analyzed to identify the user complaint, provide a diagnosis, and assess cybersecurity relevance.
3. **Solution Finding:** Comments are analyzed to find relevant solutions or recommendations.
4. **Checkpointing:** Progress is saved at regular intervals to allow for resume capability.
5. **Data Saving:** Processed data is saved to a CSV file for further analysis.

## Important Notes and Best Practices

### Handling Data Files
- **⚠️ IMPORTANT: Never open tables you want to update while the script is running.**
  Opening data files (especially CSV files) that the script is actively writing to can cause permission issues and may corrupt the data. Always ensure that all output files are closed before running the script.

### Performance Considerations
- For large datasets, consider running the script during off-hours or on a dedicated machine to avoid disrupting other work.
- Regularly monitor the script's progress using the logged information.

### Data Integrity
- Regularly backup your data files, especially before running large-scale processing tasks.
- Use version control for your data files if possible, to track changes over time.

### API Usage
- Be mindful of API rate limits, especially when processing large amounts of data in a short time.
- Consider implementing additional rate limiting in the script if necessary.

## Troubleshooting
If you encounter issues:
1. Check that all required libraries are installed and up to date.
2. Ensure all necessary API keys and endpoints are correctly set in your environment variables.
3. Verify that you have the necessary permissions to read from and write to the specified file paths.
4. If experiencing API-related issues, check your API usage and ensure you're within the allowed limits.

## Contributing
Contributions to Workreddit are welcome! Please refer to the `CONTRIBUTING.md` file for guidelines on how to make contributions.

## License
This project is licensed under the MIT License - see the `LICENSE.md` file for details.

## Acknowledgments
- Reddit API for providing access to the data
- Azure OpenAI for powering the AI analysis capabilities
- LangChain for enhancing our natural language processing capabilities
