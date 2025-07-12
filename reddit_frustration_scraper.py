#!/usr/bin/env python3
"""
Reddit Frustration Scraper

A tool to scrape frustration-related posts from Reddit communities.
"""

import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

import praw
import pandas as pd
from prawcore.exceptions import ResponseException, OAuthException


class RedditFrustrationScraper:
    """Main scraper class for collecting frustration-related Reddit posts."""
    
    def __init__(self, config_path: str = "config.json"):
        """Initialize the scraper with configuration."""
        self.config = self._load_config(config_path)
        self.reddit = self._initialize_reddit()
        self.logger = self._setup_logging()
        
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file."""
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        return config
    
    def _initialize_reddit(self) -> praw.Reddit:
        """Initialize Reddit API client."""
        reddit_config = self.config['reddit_api']
        
        try:
            reddit = praw.Reddit(
                client_id=reddit_config['client_id'],
                client_secret=reddit_config['client_secret'],
                user_agent=reddit_config['user_agent']
            )
            
            # Test authentication
            reddit.user.me()
            
        except OAuthException as e:
            print(f"Reddit API authentication failed: {e}")
            sys.exit(1)
            
        return reddit
    
    def _setup_logging(self) -> logging.Logger:
        """Set up logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def _contains_frustration_keywords(self, text: str) -> bool:
        """Check if text contains frustration-related keywords."""
        keywords = self.config['scraping']['keywords']
        text_lower = text.lower()
        
        return any(keyword.lower() in text_lower for keyword in keywords)
    
    def _meets_filter_criteria(self, submission) -> bool:
        """Check if submission meets filtering criteria."""
        filters = self.config['filters']
        
        # Check score
        if submission.score < filters['min_score']:
            return False
        
        # Check comment count
        if submission.num_comments < filters['min_comments']:
            return False
        
        # Check NSFW
        if filters['exclude_nsfw'] and submission.over_18:
            return False
        
        # Check if deleted
        if filters['exclude_deleted'] and submission.selftext == '[deleted]':
            return False
        
        return True
    
    def scrape_subreddit(self, subreddit_name: str) -> List[Dict]:
        """Scrape posts from a specific subreddit."""
        posts = []
        scraping_config = self.config['scraping']
        
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            self.logger.info(f"Scraping r/{subreddit_name}")
            
            # Get posts based on time filter
            if scraping_config['time_filter'] == 'week':
                submissions = subreddit.top('week', limit=scraping_config['post_limit'])
            elif scraping_config['time_filter'] == 'month':
                submissions = subreddit.top('month', limit=scraping_config['post_limit'])
            else:
                submissions = subreddit.hot(limit=scraping_config['post_limit'])
            
            for submission in submissions:
                # Check if post contains frustration keywords
                if (self._contains_frustration_keywords(submission.title) or 
                    self._contains_frustration_keywords(submission.selftext)):
                    
                    # Check if post meets filter criteria
                    if self._meets_filter_criteria(submission):
                        post_data = {
                            'id': submission.id,
                            'title': submission.title,
                            'selftext': submission.selftext,
                            'score': submission.score,
                            'num_comments': submission.num_comments,
                            'created_utc': submission.created_utc,
                            'subreddit': subreddit_name,
                            'url': submission.url,
                            'permalink': f"https://reddit.com{submission.permalink}",
                            'author': str(submission.author) if submission.author else '[deleted]'
                        }
                        
                        # Add comments if requested
                        if self.config['output']['include_comments']:
                            post_data['comments'] = self._get_top_comments(submission)
                        
                        posts.append(post_data)
            
        except ResponseException as e:
            self.logger.error(f"Error scraping r/{subreddit_name}: {e}")
        
        return posts
    
    def _get_top_comments(self, submission) -> List[Dict]:
        """Get top comments for a submission."""
        comments = []
        max_comments = self.config['output']['max_comments']
        
        submission.comments.replace_more(limit=0)
        
        for comment in submission.comments[:max_comments]:
            if hasattr(comment, 'body'):
                comments.append({
                    'id': comment.id,
                    'body': comment.body,
                    'score': comment.score,
                    'author': str(comment.author) if comment.author else '[deleted]'
                })
        
        return comments
    
    def scrape_all_subreddits(self) -> List[Dict]:
        """Scrape all configured subreddits."""
        all_posts = []
        subreddits = self.config['scraping']['subreddits']
        
        for subreddit in subreddits:
            posts = self.scrape_subreddit(subreddit)
            all_posts.extend(posts)
            self.logger.info(f"Found {len(posts)} frustration posts in r/{subreddit}")
        
        return all_posts
    
    def save_data(self, posts: List[Dict]):
        """Save scraped data to file."""
        output_config = self.config['output']
        filename = output_config['filename']
        
        if output_config['format'] == 'json':
            with open(filename, 'w') as f:
                json.dump(posts, f, indent=2)
        
        elif output_config['format'] == 'csv':
            df = pd.DataFrame(posts)
            csv_filename = filename.replace('.json', '.csv')
            df.to_csv(csv_filename, index=False)
            
        self.logger.info(f"Saved {len(posts)} posts to {filename}")
    
    def run(self):
        """Main execution method."""
        self.logger.info("Starting Reddit frustration scraper")
        
        # Scrape all subreddits
        posts = self.scrape_all_subreddits()
        
        if posts:
            # Save data
            self.save_data(posts)
            
            # Print summary
            print(f"\n=== Scraping Complete ===")
            print(f"Total posts found: {len(posts)}")
            print(f"Subreddits scraped: {', '.join(self.config['scraping']['subreddits'])}")
            print(f"Data saved to: {self.config['output']['filename']}")
        else:
            self.logger.warning("No posts found matching criteria")


def main():
    """Main entry point."""
    try:
        scraper = RedditFrustrationScraper()
        scraper.run()
    except KeyboardInterrupt:
        print("\nScraping interrupted by user")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
