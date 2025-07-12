#!/usr/bin/env python3
"""
Tests for Reddit Frustration Scraper
"""

import json
import os
import tempfile
import unittest
from unittest.mock import Mock, patch, MagicMock

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reddit_frustration_scraper import RedditFrustrationScraper


class TestRedditFrustrationScraper(unittest.TestCase):
    """Test cases for the Reddit Frustration Scraper."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_config = {
            "reddit_api": {
                "client_id": "test_client_id",
                "client_secret": "test_client_secret",
                "user_agent": "test_user_agent"
            },
            "scraping": {
                "subreddits": ["test_subreddit"],
                "keywords": ["frustrat", "annoying", "irritat"],
                "post_limit": 10,
                "time_filter": "week"
            },
            "output": {
                "format": "json",
                "filename": "test_output.json",
                "include_comments": False,
                "max_comments": 5
            },
            "filters": {
                "min_score": 1,
                "min_comments": 0,
                "exclude_nsfw": True,
                "exclude_deleted": True
            }
        }
        
        # Create temporary config file
        self.temp_config_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        json.dump(self.test_config, self.temp_config_file)
        self.temp_config_file.close()
    
    def tearDown(self):
        """Clean up test fixtures."""
        os.unlink(self.temp_config_file.name)
        
        # Clean up test output file if it exists
        if os.path.exists("test_output.json"):
            os.remove("test_output.json")
    
    @patch('reddit_frustration_scraper.praw.Reddit')
    def test_initialization(self, mock_reddit):
        """Test scraper initialization."""
        mock_reddit_instance = Mock()
        mock_reddit.return_value = mock_reddit_instance
        
        scraper = RedditFrustrationScraper(self.temp_config_file.name)
        
        self.assertEqual(scraper.config, self.test_config)
        mock_reddit.assert_called_once_with(
            client_id="test_client_id",
            client_secret="test_client_secret",
            user_agent="test_user_agent"
        )
    
    def test_load_config_file_not_found(self):
        """Test loading config when file doesn't exist."""
        with self.assertRaises(FileNotFoundError):
            RedditFrustrationScraper("nonexistent_config.json")
    
    @patch('reddit_frustration_scraper.praw.Reddit')
    def test_contains_frustration_keywords(self, mock_reddit):
        """Test keyword detection in text."""
        mock_reddit_instance = Mock()
        mock_reddit.return_value = mock_reddit_instance
        
        scraper = RedditFrustrationScraper(self.temp_config_file.name)
        
        # Test positive cases
        self.assertTrue(scraper._contains_frustration_keywords("This is so frustrating!"))
        self.assertTrue(scraper._contains_frustration_keywords("Very annoying situation"))
        self.assertTrue(scraper._contains_frustration_keywords("I'm getting irritated"))
        
        # Test negative cases
        self.assertFalse(scraper._contains_frustration_keywords("This is a happy post"))
        self.assertFalse(scraper._contains_frustration_keywords("Great day today"))
    
    @patch('reddit_frustration_scraper.praw.Reddit')
    def test_meets_filter_criteria(self, mock_reddit):
        """Test filtering criteria."""
        mock_reddit_instance = Mock()
        mock_reddit.return_value = mock_reddit_instance
        
        scraper = RedditFrustrationScraper(self.temp_config_file.name)
        
        # Create mock submission
        mock_submission = Mock()
        mock_submission.score = 5
        mock_submission.num_comments = 2
        mock_submission.over_18 = False
        mock_submission.selftext = "Test post"
        
        # Test passing criteria
        self.assertTrue(scraper._meets_filter_criteria(mock_submission))
        
        # Test failing score criteria
        mock_submission.score = 0
        self.assertFalse(scraper._meets_filter_criteria(mock_submission))
        
        # Test failing NSFW criteria
        mock_submission.score = 5
        mock_submission.over_18 = True
        self.assertFalse(scraper._meets_filter_criteria(mock_submission))
    
    @patch('reddit_frustration_scraper.praw.Reddit')
    def test_scrape_subreddit(self, mock_reddit):
        """Test scraping a subreddit."""
        mock_reddit_instance = Mock()
        mock_reddit.return_value = mock_reddit_instance
        
        # Create mock submissions
        mock_submission1 = Mock()
        mock_submission1.id = "test1"
        mock_submission1.title = "This is frustrating"
        mock_submission1.selftext = "Really annoying situation"
        mock_submission1.score = 10
        mock_submission1.num_comments = 5
        mock_submission1.created_utc = 1234567890
        mock_submission1.url = "https://reddit.com/test1"
        mock_submission1.permalink = "/r/test/comments/test1"
        mock_submission1.author = "test_user"
        mock_submission1.over_18 = False
        
        mock_submission2 = Mock()
        mock_submission2.id = "test2"
        mock_submission2.title = "Happy post"
        mock_submission2.selftext = "Great day"
        mock_submission2.score = 5
        mock_submission2.num_comments = 2
        mock_submission2.created_utc = 1234567891
        mock_submission2.url = "https://reddit.com/test2"
        mock_submission2.permalink = "/r/test/comments/test2"
        mock_submission2.author = "test_user2"
        mock_submission2.over_18 = False
        
        # Mock subreddit
        mock_subreddit = Mock()
        mock_subreddit.top.return_value = [mock_submission1, mock_submission2]
        mock_reddit_instance.subreddit.return_value = mock_subreddit
        
        scraper = RedditFrustrationScraper(self.temp_config_file.name)
        posts = scraper.scrape_subreddit("test_subreddit")
        
        # Should only return the frustrating post
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0]['title'], "This is frustrating")
        self.assertEqual(posts[0]['id'], "test1")
    
    @patch('reddit_frustration_scraper.praw.Reddit')
    def test_save_data_json(self, mock_reddit):
        """Test saving data to JSON file."""
        mock_reddit_instance = Mock()
        mock_reddit.return_value = mock_reddit_instance
        
        scraper = RedditFrustrationScraper(self.temp_config_file.name)
        
        test_posts = [
            {
                "id": "test1",
                "title": "Test Post",
                "score": 10
            }
        ]
        
        scraper.save_data(test_posts)
        
        # Check if file was created
        self.assertTrue(os.path.exists("test_output.json"))
        
        # Check file contents
        with open("test_output.json", 'r') as f:
            saved_data = json.load(f)
        
        self.assertEqual(saved_data, test_posts)
    
    @patch('reddit_frustration_scraper.praw.Reddit')
    def test_get_top_comments(self, mock_reddit):
        """Test getting top comments."""
        mock_reddit_instance = Mock()
        mock_reddit.return_value = mock_reddit_instance
        
        scraper = RedditFrustrationScraper(self.temp_config_file.name)
        
        # Create mock comments
        mock_comment1 = Mock()
        mock_comment1.id = "comment1"
        mock_comment1.body = "First comment"
        mock_comment1.score = 5
        mock_comment1.author = "commenter1"
        
        mock_comment2 = Mock()
        mock_comment2.id = "comment2"
        mock_comment2.body = "Second comment"
        mock_comment2.score = 3
        mock_comment2.author = "commenter2"
        
        # Mock submission with comments
        mock_submission = Mock()
        mock_submission.comments = [mock_comment1, mock_comment2]
        mock_submission.comments.replace_more = Mock()
        
        comments = scraper._get_top_comments(mock_submission)
        
        self.assertEqual(len(comments), 2)
        self.assertEqual(comments[0]['body'], "First comment")
        self.assertEqual(comments[1]['body'], "Second comment")


if __name__ == '__main__':
    unittest.main()
