"""
SEO Generator Module.
Generates optimized titles, descriptions, and tags for YouTube videos.
"""

from typing import Optional

import openai

from config import settings
from utils.logger import get_logger

logger = get_logger(__name__, settings.log_level, settings.log_file)

# SEO generation prompt template
SEO_PROMPT = """You are an expert YouTube SEO specialist. Generate optimized metadata for a YouTube video.

VIDEO TOPIC: {topic}
VIDEO ANGLE: {angle}
SCRIPT SUMMARY: {script_summary}

Generate the following:

1. **TITLE** (max 60 characters):
   - Include primary keyword near the beginning
   - Create curiosity or urgency
   - Use power words (Amazing, Shocking, Secret, etc.)
   - Avoid clickbait that doesn't deliver

2. **DESCRIPTION** (150-200 words):
   - First 150 characters are crucial (shown in search)
   - Include primary and secondary keywords naturally
   - Add timestamps if applicable
   - Include a call-to-action
   - Add relevant hashtags at the end (3-5)

3. **TAGS** (15-20 tags):
   - Mix of broad and specific keywords
   - Include topic variations
   - Add related trending terms
   - Include common misspellings if relevant

FORMAT YOUR RESPONSE EXACTLY AS:
TITLE: [Your title here]

DESCRIPTION:
[Your description here]

TAGS: [tag1, tag2, tag3, ...]

Generate the SEO metadata now:"""


class SEOGenerator:
    """
    Generates SEO-optimized metadata for YouTube videos.
    Uses LLM to create engaging titles, descriptions, and tags.
    """
    
    def __init__(self, provider: Optional[str] = None):
        """
        Initialize the SEOGenerator.
        
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
        
        logger.info(f"SEOGenerator initialized with provider: {self.provider}")
    
    def generate_metadata(
        self,
        topic: str,
        angle: str,
        script: str
    ) -> dict:
        """
        Generate SEO-optimized metadata for a video.
        
        Args:
            topic: Video topic
            angle: Specific angle or perspective
            script: Full video script
        
        Returns:
            Dictionary with title, description, and tags
        """
        logger.info(f"Generating SEO metadata for topic: {topic}")
        
        # Create script summary (first 500 chars)
        script_summary = script[:500] + "..." if len(script) > 500 else script
        
        # Format prompt
        prompt = SEO_PROMPT.format(
            topic=topic,
            angle=angle,
            script_summary=script_summary
        )
        
        try:
            response = self._call_llm(prompt)
            
            # Parse the response
            metadata = self._parse_response(response)
            
            # Validate and clean
            metadata = self._validate_metadata(metadata, topic)
            
            logger.info(f"Generated title: {metadata['title']}")
            logger.info(f"Generated {len(metadata['tags'])} tags")
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error generating SEO metadata: {e}")
            # Return fallback metadata
            return self._generate_fallback_metadata(topic, angle)
    
    def _call_llm(self, prompt: str) -> str:
        """Call LLM API (works for both Grok and OpenAI)."""
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=2048,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    
    def _parse_response(self, response: str) -> dict:
        """Parse the LLM response into structured metadata."""
        metadata = {
            "title": "",
            "description": "",
            "tags": []
        }
        
        lines = response.strip().split("\n")
        current_section = None
        description_lines = []
        
        for line in lines:
            line = line.strip()
            
            if line.startswith("TITLE:"):
                metadata["title"] = line.replace("TITLE:", "").strip()
                current_section = None
            elif line.startswith("DESCRIPTION:"):
                current_section = "description"
            elif line.startswith("TAGS:"):
                tags_str = line.replace("TAGS:", "").strip()
                # Parse tags (comma or bracket separated)
                tags_str = tags_str.strip("[]")
                metadata["tags"] = [t.strip().strip('"\'') for t in tags_str.split(",") if t.strip()]
                current_section = None
            elif current_section == "description" and line:
                description_lines.append(line)
        
        metadata["description"] = "\n".join(description_lines)
        
        return metadata
    
    def _validate_metadata(self, metadata: dict, topic: str) -> dict:
        """Validate and clean the generated metadata."""
        # Ensure title is not too long
        if len(metadata["title"]) > 100:
            metadata["title"] = metadata["title"][:97] + "..."
        
        # Ensure we have a title
        if not metadata["title"]:
            metadata["title"] = f"Amazing Facts About {topic} You Need to Know"
        
        # Ensure we have a description
        if not metadata["description"]:
            metadata["description"] = f"Discover fascinating insights about {topic}. Don't forget to like and subscribe for more content!\n\n#shorts #{topic.replace(' ', '')}"
        
        # Ensure we have tags
        if not metadata["tags"]:
            metadata["tags"] = [
                topic,
                topic.lower(),
                "facts",
                "interesting",
                "viral",
                "trending",
                "shorts",
                "youtube shorts"
            ]
        
        # Clean tags
        metadata["tags"] = [
            tag.strip().lower()
            for tag in metadata["tags"]
            if tag.strip() and len(tag.strip()) <= 30
        ][:20]  # Max 20 tags
        
        return metadata
    
    def _generate_fallback_metadata(self, topic: str, angle: str) -> dict:
        """Generate fallback metadata if LLM fails."""
        return {
            "title": f"Incredible {topic} Facts That Will Blow Your Mind",
            "description": f"""Discover amazing facts about {topic}!

In this video, we explore {angle}.

Don't forget to:
👍 Like this video
🔔 Subscribe for more content
💬 Comment your thoughts below

#shorts #{topic.replace(' ', '')} #facts #viral""",
            "tags": [
                topic.lower(),
                "facts",
                "interesting facts",
                "did you know",
                "amazing",
                "viral",
                "trending",
                "shorts",
                "youtube shorts",
                "education",
                "learning",
                "knowledge"
            ]
        }
    
    def generate_hashtags(self, topic: str, count: int = 5) -> list[str]:
        """
        Generate relevant hashtags for a topic.
        
        Args:
            topic: Video topic
            count: Number of hashtags to generate
        
        Returns:
            List of hashtags
        """
        prompt = f"""Generate {count} trending and relevant YouTube hashtags for a video about: {topic}

Rules:
- No spaces in hashtags
- Mix of popular and niche tags
- Include #shorts if applicable
- Format: #hashtag1 #hashtag2 ...

Hashtags:"""

        try:
            response = self._call_llm(prompt)
            
            # Extract hashtags
            import re
            hashtags = re.findall(r'#\w+', response)
            return hashtags[:count]
            
        except Exception as e:
            logger.error(f"Error generating hashtags: {e}")
            return [f"#{topic.replace(' ', '')}", "#shorts", "#viral", "#trending", "#facts"]
    
    def optimize_title(self, title: str, keywords: list[str]) -> str:
        """
        Optimize an existing title for better SEO.
        
        Args:
            title: Original title
            keywords: Target keywords
        
        Returns:
            Optimized title
        """
        prompt = f"""Optimize this YouTube title for better SEO and click-through rate:

Original Title: {title}
Target Keywords: {', '.join(keywords)}

Rules:
- Keep under 60 characters
- Include primary keyword near the start
- Make it compelling and curiosity-inducing
- Avoid clickbait

Optimized Title:"""

        try:
            response = self._call_llm(prompt)
            
            # Extract the title (first non-empty line)
            for line in response.strip().split("\n"):
                line = line.strip()
                if line and not line.startswith("Optimized"):
                    return line[:100]
            
            return title
            
        except Exception as e:
            logger.error(f"Error optimizing title: {e}")
            return title


if __name__ == "__main__":
    # Test the SEO generator
    generator = SEOGenerator()
    
    test_script = """
    Did you know that honey never spoils? Archaeologists have found 3000-year-old honey 
    in Egyptian tombs that was still perfectly edible. The secret lies in honey's unique 
    chemistry. Its low moisture content and acidic pH create an environment where bacteria 
    simply cannot survive.
    """
    
    metadata = generator.generate_metadata(
        topic="Honey Facts",
        angle="Why honey never spoils",
        script=test_script
    )
    
    print("\n=== Generated SEO Metadata ===")
    print(f"Title: {metadata['title']}")
    print(f"\nDescription:\n{metadata['description']}")
    print(f"\nTags: {metadata['tags']}")
