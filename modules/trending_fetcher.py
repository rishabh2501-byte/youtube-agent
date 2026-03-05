"""
Trending Topics Fetcher Module.
Fetches trending topics from Google Trends using pytrends.
"""

from datetime import datetime
from typing import Optional

from pytrends.request import TrendReq

from config import settings
from utils.logger import get_logger

logger = get_logger(__name__, settings.log_level, settings.log_file)


class TrendingFetcher:
    """
    Fetches trending topics from Google Trends.
    Uses pytrends library to access Google Trends data.
    """
    
    def __init__(self, region: Optional[str] = None):
        """
        Initialize the TrendingFetcher.
        
        Args:
            region: ISO 3166-1 alpha-2 country code (e.g., 'US', 'GB', 'IN')
        """
        self.region = region or settings.trending_region
        self.pytrends = TrendReq(hl='en-US', tz=360)
        logger.info(f"TrendingFetcher initialized for region: {self.region}")
    
    def fetch_daily_trends(self, limit: Optional[int] = None) -> list[dict]:
        """
        Fetch daily trending searches from Google Trends.
        
        Args:
            limit: Maximum number of trends to return
        
        Returns:
            List of trending topics with metadata
        """
        limit = limit or settings.trending_topics_count
        
        try:
            logger.info(f"Fetching daily trends for region: {self.region}")
            
            # Get trending searches
            trending_df = self.pytrends.trending_searches(pn=self.region.lower())
            
            trends = []
            for idx, row in trending_df.head(limit).iterrows():
                topic = row[0] if isinstance(row, (list, tuple)) else str(row.values[0])
                trends.append({
                    "rank": idx + 1,
                    "topic": topic,
                    "source": "google_trends_daily",
                    "region": self.region,
                    "fetched_at": datetime.now().isoformat(),
                })
            
            logger.info(f"Fetched {len(trends)} trending topics")
            return trends
            
        except Exception as e:
            logger.error(f"Error fetching daily trends: {e}")
            raise
    
    def fetch_realtime_trends(self, category: str = "all") -> list[dict]:
        """
        Fetch real-time trending topics.
        
        Args:
            category: Category filter (all, entertainment, business, etc.)
        
        Returns:
            List of real-time trending topics
        """
        try:
            logger.info(f"Fetching real-time trends for category: {category}")
            
            # Get real-time trending searches
            realtime_df = self.pytrends.realtime_trending_searches(pn=self.region)
            
            trends = []
            for idx, row in realtime_df.head(settings.trending_topics_count).iterrows():
                trends.append({
                    "rank": idx + 1,
                    "topic": row.get("title", row.get("entityNames", ["Unknown"])[0]),
                    "source": "google_trends_realtime",
                    "region": self.region,
                    "fetched_at": datetime.now().isoformat(),
                })
            
            logger.info(f"Fetched {len(trends)} real-time trends")
            return trends
            
        except Exception as e:
            logger.warning(f"Real-time trends not available: {e}")
            # Fallback to daily trends
            return self.fetch_daily_trends()
    
    def get_interest_over_time(self, keywords: list[str], timeframe: str = "today 1-m") -> dict:
        """
        Get interest over time for specific keywords.
        
        Args:
            keywords: List of keywords to analyze (max 5)
            timeframe: Time range for analysis
        
        Returns:
            Dictionary with interest data for each keyword
        """
        try:
            # Limit to 5 keywords (Google Trends limit)
            keywords = keywords[:5]
            
            logger.info(f"Fetching interest over time for: {keywords}")
            
            self.pytrends.build_payload(keywords, timeframe=timeframe, geo=self.region)
            interest_df = self.pytrends.interest_over_time()
            
            if interest_df.empty:
                return {kw: 0 for kw in keywords}
            
            # Calculate average interest for each keyword
            interest_scores = {}
            for keyword in keywords:
                if keyword in interest_df.columns:
                    interest_scores[keyword] = float(interest_df[keyword].mean())
                else:
                    interest_scores[keyword] = 0
            
            return interest_scores
            
        except Exception as e:
            logger.error(f"Error fetching interest over time: {e}")
            return {kw: 0 for kw in keywords}
    
    def get_related_queries(self, keyword: str) -> dict:
        """
        Get related queries for a keyword.
        
        Args:
            keyword: Keyword to find related queries for
        
        Returns:
            Dictionary with top and rising related queries
        """
        try:
            logger.info(f"Fetching related queries for: {keyword}")
            
            self.pytrends.build_payload([keyword], geo=self.region)
            related = self.pytrends.related_queries()
            
            result = {"top": [], "rising": []}
            
            if keyword in related:
                if related[keyword]["top"] is not None:
                    result["top"] = related[keyword]["top"]["query"].tolist()[:10]
                if related[keyword]["rising"] is not None:
                    result["rising"] = related[keyword]["rising"]["query"].tolist()[:10]
            
            return result
            
        except Exception as e:
            logger.error(f"Error fetching related queries: {e}")
            return {"top": [], "rising": []}
    
    def fetch_all_trends(self) -> list[dict]:
        """
        Fetch trends from multiple sources and combine them.
        
        Returns:
            Combined list of trending topics
        """
        all_trends = []
        
        # Fetch daily trends
        try:
            daily = self.fetch_daily_trends()
            all_trends.extend(daily)
        except Exception as e:
            logger.warning(f"Could not fetch daily trends: {e}")
        
        # Fetch real-time trends
        try:
            realtime = self.fetch_realtime_trends()
            # Add only unique topics
            existing_topics = {t["topic"].lower() for t in all_trends}
            for trend in realtime:
                if trend["topic"].lower() not in existing_topics:
                    all_trends.append(trend)
                    existing_topics.add(trend["topic"].lower())
        except Exception as e:
            logger.warning(f"Could not fetch real-time trends: {e}")
        
        logger.info(f"Total unique trends fetched: {len(all_trends)}")
        return all_trends


if __name__ == "__main__":
    # Test the trending fetcher
    fetcher = TrendingFetcher()
    trends = fetcher.fetch_daily_trends(limit=10)
    
    print("\n=== Daily Trending Topics ===")
    for trend in trends:
        print(f"{trend['rank']}. {trend['topic']}")
