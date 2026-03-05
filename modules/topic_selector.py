"""
Topic Selector Module.
Uses LLM to analyze trending topics and select the best one for video content.
"""

from typing import Optional

import openai

from config import settings
from utils.logger import get_logger

logger = get_logger(__name__, settings.log_level, settings.log_file)

# Topic selection prompt template
TOPIC_SELECTION_PROMPT = """You are an expert YouTube content strategist. Analyze the following trending topics and select the BEST ONE for creating a viral, engaging 60-second YouTube video.

TRENDING TOPICS:
{topics_list}

SELECTION CRITERIA:
1. **Viral Potential**: Topics that evoke curiosity, emotion, or surprise
2. **Visual Appeal**: Topics that can be illustrated with stock footage
3. **Broad Appeal**: Topics interesting to a wide audience
4. **Evergreen Potential**: Topics that won't become irrelevant quickly
5. **Safe Content**: Avoid controversial, political, or sensitive topics

RESPOND IN THIS EXACT FORMAT:
SELECTED_TOPIC: [The exact topic name]
REASON: [2-3 sentences explaining why this topic is best]
ANGLE: [Specific angle or hook for the video]
KEYWORDS: [5 relevant keywords for stock footage, comma-separated]
TONE: [Recommended tone: educational, entertaining, inspiring, shocking, etc.]

Select the single best topic now:"""


class TopicSelector:
    """
    Selects the best trending topic for video content using LLM analysis.
    Supports both Anthropic (Claude) and OpenAI models.
    """
    
    def __init__(self, provider: Optional[str] = None):
        """
        Initialize the TopicSelector.
        
        Args:
            provider: LLM provider ('groq' or 'openai')
        """
        self.provider = provider or settings.llm_provider
        
        if self.provider == "groq":
            self.client = openai.OpenAI(
                api_key=settings.groq_api_key,
                base_url="https://api.groq.com/openai/v1"
            )
            self.model = "llama-3.3-70b-versatile"
        else:
            self.client = openai.OpenAI(api_key=settings.openai_api_key)
            self.model = "gpt-4-turbo-preview"
        
        logger.info(f"TopicSelector initialized with provider: {self.provider}")
    
    def _format_topics_list(self, topics: list[dict]) -> str:
        """Format topics list for the prompt."""
        formatted = []
        for topic in topics:
            formatted.append(f"{topic['rank']}. {topic['topic']}")
        return "\n".join(formatted)
    
    def _parse_response(self, response_text: str) -> dict:
        """Parse the LLM response into structured data."""
        result = {
            "selected_topic": "",
            "reason": "",
            "angle": "",
            "keywords": [],
            "tone": "",
        }
        
        lines = response_text.strip().split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith("SELECTED_TOPIC:"):
                result["selected_topic"] = line.replace("SELECTED_TOPIC:", "").strip()
            elif line.startswith("REASON:"):
                result["reason"] = line.replace("REASON:", "").strip()
            elif line.startswith("ANGLE:"):
                result["angle"] = line.replace("ANGLE:", "").strip()
            elif line.startswith("KEYWORDS:"):
                keywords_str = line.replace("KEYWORDS:", "").strip()
                result["keywords"] = [k.strip() for k in keywords_str.split(",")]
            elif line.startswith("TONE:"):
                result["tone"] = line.replace("TONE:", "").strip()
        
        return result
    
    def select_topic(self, topics: list[dict]) -> dict:
        """
        Select the best topic from a list of trending topics.
        
        Args:
            topics: List of trending topics with metadata
        
        Returns:
            Dictionary with selected topic and analysis
        """
        if not topics:
            raise ValueError("No topics provided for selection")
        
        logger.info(f"Selecting best topic from {len(topics)} candidates")
        
        # Format the prompt
        topics_list = self._format_topics_list(topics)
        prompt = TOPIC_SELECTION_PROMPT.format(topics_list=topics_list)
        
        try:
            response = self._call_llm(prompt)
            
            # Parse the response
            result = self._parse_response(response)
            
            # Validate we got a topic
            if not result["selected_topic"]:
                # Fallback to first topic
                logger.warning("Could not parse selected topic, using first topic")
                result["selected_topic"] = topics[0]["topic"]
                result["keywords"] = [topics[0]["topic"]]
            
            logger.info(f"Selected topic: {result['selected_topic']}")
            logger.info(f"Angle: {result['angle']}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error selecting topic: {e}")
            # Fallback to first topic
            return {
                "selected_topic": topics[0]["topic"],
                "reason": "Fallback selection due to error",
                "angle": f"Interesting facts about {topics[0]['topic']}",
                "keywords": [topics[0]["topic"]],
                "tone": "educational",
            }
    
    def _call_llm(self, prompt: str) -> str:
        """Call LLM API (works for both Grok and OpenAI)."""
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    
    def refine_topic(self, topic: str, context: Optional[str] = None) -> dict:
        """
        Refine a topic with additional context or constraints.
        
        Args:
            topic: The topic to refine
            context: Additional context or constraints
        
        Returns:
            Refined topic analysis
        """
        refine_prompt = f"""Refine this topic for a 60-second YouTube video:

TOPIC: {topic}
{f'CONTEXT: {context}' if context else ''}

Provide:
1. A specific, engaging angle
2. 5 keywords for stock footage
3. Recommended tone
4. A hook to grab attention in the first 3 seconds

Format your response as:
ANGLE: [specific angle]
KEYWORDS: [comma-separated keywords]
TONE: [tone]
HOOK: [attention-grabbing hook]"""

        try:
            response = self._call_llm(refine_prompt)
            
            result = {
                "topic": topic,
                "angle": "",
                "keywords": [],
                "tone": "",
                "hook": "",
            }
            
            for line in response.strip().split("\n"):
                line = line.strip()
                if line.startswith("ANGLE:"):
                    result["angle"] = line.replace("ANGLE:", "").strip()
                elif line.startswith("KEYWORDS:"):
                    result["keywords"] = [k.strip() for k in line.replace("KEYWORDS:", "").split(",")]
                elif line.startswith("TONE:"):
                    result["tone"] = line.replace("TONE:", "").strip()
                elif line.startswith("HOOK:"):
                    result["hook"] = line.replace("HOOK:", "").strip()
            
            return result
            
        except Exception as e:
            logger.error(f"Error refining topic: {e}")
            return {
                "topic": topic,
                "angle": f"Fascinating facts about {topic}",
                "keywords": [topic],
                "tone": "educational",
                "hook": f"Did you know this about {topic}?",
            }


if __name__ == "__main__":
    # Test the topic selector
    test_topics = [
        {"rank": 1, "topic": "Solar Eclipse 2024"},
        {"rank": 2, "topic": "AI Technology"},
        {"rank": 3, "topic": "Climate Change"},
        {"rank": 4, "topic": "Space Exploration"},
        {"rank": 5, "topic": "Cryptocurrency"},
    ]
    
    selector = TopicSelector()
    result = selector.select_topic(test_topics)
    
    print("\n=== Topic Selection Result ===")
    print(f"Selected: {result['selected_topic']}")
    print(f"Reason: {result['reason']}")
    print(f"Angle: {result['angle']}")
    print(f"Keywords: {result['keywords']}")
    print(f"Tone: {result['tone']}")
