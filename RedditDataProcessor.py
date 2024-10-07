import os
import pandas as pd
import logging
import time
import json
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain.prompts import ChatPromptTemplate
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RedditDataProcessor:
    """
    A class for processing Reddit post data, analyzing user complaints, and finding relevant answers.

    This class uses AI-powered analysis to process Reddit posts, identify user complaints,
    diagnose issues, assess cybersecurity relevance, and find solutions or recommendations
    based on post comments.

    Attributes:
        subreddit (str): The name of the subreddit being processed.
        max_retries (int): Maximum number of retry attempts for API calls.
        llm (AzureChatOpenAI): The language model used for AI-powered analysis.
        str_parser (StrOutputParser): Parser for string outputs.
        json_parser (JsonOutputParser): Parser for JSON outputs.
    """

    def __init__(self, subreddit, max_retries=3):
        """
        Initialize the RedditDataProcessor.

        Args:
            subreddit (str): The name of the subreddit to process.
            max_retries (int, optional): Maximum number of retry attempts for API calls. Defaults to 3.
        """
        self.subreddit = subreddit
        self.max_retries = max_retries
        self.llm = self._initialize_llm()
        self.str_parser = StrOutputParser()
        self.json_parser = JsonOutputParser()

    def _initialize_llm(self):
        """
        Initialize and return the Azure ChatOpenAI language model.

        Returns:
            AzureChatOpenAI: Configured language model instance.
        """
        return AzureChatOpenAI(
            model=os.getenv('AZURE_MODEL_NAME'),
            deployment_name=os.getenv('AZURE_DEPLOYMENT_NAME'),
            temperature=1,
            openai_api_type="azure",
            streaming=True
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10),
           retry=retry_if_exception_type((ConnectionError, TimeoutError)))
    def make_api_call(self, prompt, inputs):
        """
        Make an API call with retry logic.

        This method will retry the API call up to 3 times with exponential backoff
        if a ConnectionError or TimeoutError occurs.

        Args:
            prompt (ChatPromptTemplate): The prompt template for the API call.
            inputs (dict): The input data for the prompt.

        Returns:
            dict: The JSON response from the API call.
        """
        sequence = prompt | self.llm | JsonOutputParser()
        return sequence.invoke(inputs)
          def process_posts(self, posts_data, comments_data, file_path, chunk_size=1000):
        """
        Process Reddit posts in chunks, analyzing each post and finding relevant answers.

        This method processes posts in chunks to optimize memory usage, saves progress
        regularly, and implements a checkpointing system for resuming interrupted processing.

        Args:
            posts_data (pd.DataFrame): DataFrame containing Reddit posts.
            comments_data (pd.DataFrame): DataFrame containing post comments.
            file_path (str): Path to save the processed data.
            chunk_size (int, optional): Number of posts to process in each chunk. Defaults to 1000.
        """
        results = []
        checkpoint_file = f"{file_path}_checkpoint.json"

        results = self._load_checkpoint(checkpoint_file)
        total_posts = len(posts_data)
        processed_posts = len(results)

        json_prompt = self._create_post_analysis_prompt()

        for chunk_start in range(processed_posts, total_posts, chunk_size):
            chunk_end = min(chunk_start + chunk_size, total_posts)
            chunk = posts_data.iloc[chunk_start:chunk_end]

            for i, (_, post) in enumerate(chunk.iterrows(), start=chunk_start):
                post_id = post.get("Post ID")
                retry_count = 0
                while retry_count < self.max_retries:
                    try:
                        result = self._process_single_post(post, json_prompt, comments_data)
                        if result:
                            results.append(result)
                            self._save_checkpoint(checkpoint_file, results, i + 1, total_posts)
                        break  # Success, exit the retry loop
                    except Exception as e:
                        retry_count += 1
                        logger.error(
                            f"Error processing post ID {post_id} (Attempt {retry_count}/{self.max_retries}): {e}")
                        if retry_count == self.max_retries:
                            logger.error(f"Max retries reached for post ID {post_id}. Skipping.")
                        else:
                            time.sleep(2 ** retry_count)  # Exponential backoff

                if (i + 1) % 100 == 0:
                    logger.info(f"Processed {i + 1} out of {total_posts} posts")

            # Save results to CSV after each chunk
            self.save_to_csv(results, file_path)

        self._cleanup_checkpoint(checkpoint_file)

    def _normalize_text(self, text):
        """
        Normalize text by converting full-width characters to half-width and removing unwanted characters.

        This method handles various text anomalies, including full-width characters
        often found in Asian language keyboards, and removes certain unwanted character ranges.

        Args:
            text (str): The input text to normalize.

        Returns:
            str or None: The normalized text, or None if the input is empty or None.
        """
        if text:
            # Replace full-width characters with half-width equivalents
            normalized = []
            for c in text:
                code = ord(c)
                if 0xFF01 <= code <= 0xFF5E:  # Full-width punctuation
                    normalized.append(chr(code - 0xFEE0))
                elif code == 0x3000:  # Full-width space
                    normalized.append(chr(0x0020))  # Replace with normal space
                elif 0x2E80 <= code <= 0x2FFF:  # Range of CJK characters, for example
                    continue  # Ignore unwanted characters
                else:
                    normalized.append(c)

            # Join the list to form a single string and strip any leading/trailing spaces
            return ''.join(normalized).strip()
        return None  # Return None if text is None or empty

    def _process_single_post(self, post, json_prompt, comments_data):
        """
        Process a single Reddit post, analyzing its content and finding relevant answers.

        This method normalizes the post text, sends it to the AI for analysis,
        and processes the AI's response to extract relevant information.

        Args:
            post (pd.Series): A single post's data.
            json_prompt (ChatPromptTemplate): The prompt template for post analysis.
            comments_data (pd.DataFrame): DataFrame containing post comments.

        Returns:
            dict or None: Processed post data including analysis results, or None if processing fails.
        """
        post_id = post.get("Post ID")
        title = self._normalize_text(post.get('Title', ''))
        self_text = self._normalize_text(post.get('Self Text', ''))
        combined_text = f"Title: {title}\n\nContent: {self_text}"

        try:
            json_response = self.make_api_call(json_prompt, {"text": combined_text})
            logger.info(f"API response for post ID {post_id}: {json_response}")

            user_complaint = json_response.get('user_complaint', None)
            diagnosis = json_response.get('diagnosis', None)
            cybersecurity_relevance = json_response.get('cybersecurity_relevance', 'None')

            if user_complaint == -1000 or diagnosis == -1000 or user_complaint is None or diagnosis is None:
                logger.info(f"No valid issue found for post ID {post_id}, skipping.")
                return None

            if cybersecurity_relevance in ['Low', 'None']:
                user_complaint = self._generalize_complaint(user_complaint)

            solution, recommendation, steps, confidence = self.find_answers(comments_data, post_id, user_complaint,
                                                                            diagnosis)

            return {
                "post_id": post_id,
                "created_time": post.get("Created Time (UTC)"),
                "user_complaint": user_complaint,
                "diagnosis": diagnosis,
                "cybersecurity_relevance": cybersecurity_relevance,
                "solution": solution,
                "recommendation": recommendation,
                "steps": steps,
                "confidence": confidence
            }
        except Exception as e:
            logger.error(f"Error processing post ID {post_id}: {e}")
            return None

    def _create_post_analysis_prompt(self):
        """
        Create and return the prompt template for post analysis.

        This method defines the system message and user message format
        for the AI to analyze Reddit posts.

        Returns:
            ChatPromptTemplate: The configured prompt template for post analysis.
        """
        return ChatPromptTemplate.from_messages([
            ("system",
             "You are Dr. Alex, a highly experienced psychologist specializing in online community dynamics and cybersecurity. "
             "Analyze the following Reddit post and return a JSON with three keys: 'user_complaint', 'diagnosis', and 'cybersecurity_relevance'. "
             "'user_complaint': Summarize the core issue in one concise sentence (max 15 words). If there's a specific question, include it. "
             "'diagnosis': Identify the root cause or underlying issue, not just restating the complaint. Be specific and concise (max 20 words). "
             "'cybersecurity_relevance': Assess if the post is directly related to cybersecurity. Use 'High', 'Medium', 'Low', or 'None'. "
             "- High: Direct cybersecurity threats, hacking attempts, data breaches, or specific security vulnerabilities. "
             "- Medium: Discussions about cybersecurity practices, tools, or general security concerns. "
             "- Low: General tech issues that might have minor security implications. "
             "- None: Tech issues, usability problems, or discussions not related to security at all. "
             "Be conservative in your assessment. If in doubt, choose the lower relevance level. "
             "If no valid issue is found, set 'user_complaint' and 'diagnosis' to -1000, and 'cybersecurity_relevance' to 'None'. "
             "Be very certain in your analysis before providing a response."),
            ("user", "{text}"),
        ])

    def _generalize_complaint(self, user_complaint):
        """
        Generalize a user complaint for posts with low cybersecurity relevance.

        This method uses the AI to create a more generalized version of the user complaint,
        focusing on broader psychological or social aspects rather than specific tech details.

        Args:
            user_complaint (str): The original user complaint.

        Returns:
            str: A generalized version of the user complaint.
        """
        general_prompt = ChatPromptTemplate.from_messages([
            ("system",
             "Given a specific user complaint, provide a more general version that captures the core issue without specific cybersecurity details. Focus on the broader psychological or social aspects of the complaint."),
            ("user", f"Specific complaint: {user_complaint}\nProvide a more general version:"),
        ])
        general_response = general_prompt | self.llm | self.str_parser
        generalized_complaint = general_response.invoke({})
        logger.info(f"Generalized user complaint: {generalized_complaint}")
        return generalized_complaint

    def find_answers(self, comments_data, post_id, user_complaint, diagnosis):
        """
        Find the best answer or recommendation for a given post based on its comments.

        This method analyzes the comments of a post to find relevant solutions or recommendations
        that address the user's complaint and the diagnosed issue.

        Args:
            comments_data (pd.DataFrame): DataFrame containing post comments.
            post_id (str): The ID of the post being processed.
            user_complaint (str): The user's complaint or issue.
            diagnosis (str): The diagnosed root cause or underlying issue.

        Returns:
            tuple: (solution, recommendation, steps, confidence)
                solution (str or int): The best solution found, or -999 if no solution.
                recommendation (str or int): A recommendation if no solution, or -999 if a solution is found.
                steps (str): Steps for the solution, or "No steps" if not applicable.
                confidence (float): Confidence level in the answer (0 to 1).
        """
        logger.info(f"Finding answers for post ID: {post_id}")

        comments = comments_data[comments_data["Post ID"] == post_id]

        if comments.empty:
            logger.warning(f"No comments available for post ID: {post_id}.")
            return -999, -999, "No steps", 0

        comments_text = "\n".join(comments["Comment Body"].tolist())

        answer_prompt = self._create_answer_prompt()

        try:
            json_response = self.make_api_call(answer_prompt, {"user_complaint": user_complaint, "diagnosis": diagnosis,
                                                               "comments": comments_text})
            logger.info(f"Answer API response for post ID {post_id}: {json_response}")

            answer = json_response.get('Answer', 'No relevant answer found')
            steps = json_response.get('Steps', 'No steps')
            confidence = json_response.get('Confidence', 0)
            is_solution = json_response.get('Is_Solution', False)

            if answer == 'No relevant answer found':
                logger.info(f"No relevant answer found for post ID {post_id}")
                return -999, -999, "No steps", 0

            if is_solution and confidence >= 0.95:
                solution, recommendation = answer, -999
            else:
                solution, recommendation = -999, answer

            if confidence < 0.95:
                recommendation, solution, steps = answer, -999, "No steps"

            return solution, recommendation, steps, confidence

        except Exception as e:
            logger.error(f"Error in API call or response processing for post ID {post_id}: {e}")
            return -999, -999, "No steps", 0

    def _create_answer_prompt(self):
        """
        Create a prompt template for generating answers to user complaints.

        This method defines a system message that instructs the AI on how to
        format its response when analyzing user complaints and related comments.

        Returns:
            ChatPromptTemplate: A formatted prompt template for answer generation.
        """
        return ChatPromptTemplate.from_messages([
            ("system",
             "You are Dr. Alex, an expert in psychology and cybersecurity. "
             "Given a user's complaint, diagnosis, and related comments, provide the best answer you can find. "
             "Return a JSON with four keys: 'Answer', 'Steps', 'Confidence', and 'Is_Solution'. "
             "For 'Answer': Provide the most relevant and helpful response addressing the user_complaint and diagnosis. "
             "Be concise (max 50 words). If no relevant answer is found, return 'No relevant answer found'. "
             "For 'Steps': If the answer involves clear steps, list them here (max 5 steps); otherwise, return 'No steps'. "
             "For 'Confidence': Rate your confidence from 0 to 1 that this answer correctly and completely addresses "
             "the user's complaint. 1 means you are absolutely certain this is the correct and complete answer. "
             "For 'Is_Solution': Set to true if this answer definitively solves the user's problem, otherwise false."),
            ("user", "User Complaint: {user_complaint}\nDiagnosis: {diagnosis}\nComments: {comments}")
        ])

    def _generalize_complaint(self, user_complaint):
        """
        Generalize a specific user complaint to focus on broader aspects.

        This method takes a specific user complaint and generates a more general version
        that captures the core issue without cybersecurity-specific details. It focuses
        on the broader psychological or social aspects of the complaint.

        Args:
            user_complaint (str): The original, specific user complaint.

        Returns:
            str: A generalized version of the user complaint.

        Note:
            This method uses the language model to generate the generalized complaint.
        """
        general_prompt = ChatPromptTemplate.from_messages([
            ("system",
             "Given a specific user complaint, provide a more general version that captures "
             "the core issue without specific cybersecurity details. Focus on the broader "
             "psychological or social aspects of the complaint."),
            ("user", f"Specific complaint: {user_complaint}\nProvide a more general version:"),
        ])
        general_response = general_prompt | self.llm | self.str_parser
        generalized_complaint = general_response.invoke({})
        logger.info(f"Generalized user complaint: {generalized_complaint}")
        return generalized_complaint

    def save_to_csv(self, data, file_path):
        """
        Save the processed data to a CSV file.

        This method takes the processed data and saves it to a CSV file at the specified path.
        It uses pandas DataFrame to handle the data and CSV writing.

        Args:
            data (list): A list of dictionaries, where each dictionary represents a processed post.
            file_path (str): The file path where the CSV should be saved.

        Note:
            This method logs an info message upon successful saving of the file.
        """
        df = pd.DataFrame(data)
        df.to_csv(file_path, index=False)
        logger.info(f"Data saved to {file_path}")

    # Note: Make sure to import pandas at the top of your file:
    # import pandas as pd
    def _load_checkpoint(self, checkpoint_file):
        """
        Load processed results from a checkpoint file if it exists.

        This method attempts to load previously processed results from a checkpoint file.
        If the file exists, it reads the JSON data and returns it as a list of results.
        If the file doesn't exist, it returns an empty list.

        Args:
            checkpoint_file (str): The path to the checkpoint file.

        Returns:
            list: A list of processed results if the checkpoint file exists,
                  otherwise an empty list.

        Note:
            - This method logs the number of results loaded from the checkpoint.
            - If the file exists but is empty or contains invalid JSON, a JSONDecodeError
              may be raised (not explicitly handled here).
        """
        if os.path.exists(checkpoint_file):
            with open(checkpoint_file, 'r') as f:
                results = json.load(f)
            logger.info(f"Loaded {len(results)} results from checkpoint.")
            return results
        return []

    def _save_checkpoint(self, checkpoint_file, results, current_post, total_posts):
        """
        Save the current processing results to a checkpoint file.

        This method saves the current state of processed results to a checkpoint file.
        It only saves a checkpoint every 50 posts to balance between data safety and
        performance.

        Args:
            checkpoint_file (str): The path where the checkpoint file should be saved.
            results (list): The list of processed results to save.
            current_post (int): The number of the current post being processed.
            total_posts (int): The total number of posts to be processed.

        Note:
            - Checkpoints are saved every 50 posts (when current_post is divisible by 50).
            - This method logs a message each time a checkpoint is saved.
            - If there's an error while writing the file (e.g., disk full), an exception
              may be raised (not explicitly handled here).
        """
        if current_post % 50 == 0:
            with open(checkpoint_file, 'w') as f:
                json.dump(results, f)
            logger.info(f"Checkpoint saved after processing {current_post}/{total_posts} posts.")

    def _cleanup_checkpoint(self, checkpoint_file):
        """
        Remove the checkpoint file after successful completion of processing.

        This method deletes the checkpoint file if it exists. It's typically called
        after all posts have been successfully processed to clean up temporary files.

        Args:
            checkpoint_file (str): The path to the checkpoint file to be removed.

        Note:
            - This method logs a message when the checkpoint file is removed.
            - If the file doesn't exist, no action is taken and no error is raised.
            - If there's an error while trying to remove the file (e.g., permission issues),
              an exception may be raised (not explicitly handled here).
        """
        if os.path.exists(checkpoint_file):
            os.remove(checkpoint_file)
            logger.info("Checkpoint file removed after successful completion.")

        # Example usage in a process_posts method:


