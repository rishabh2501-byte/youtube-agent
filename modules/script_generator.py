"""
Script Generator Module.
Generates engaging YouTube video scripts using LLM.
"""

from typing import Optional

import openai

from config import settings
from utils.logger import get_logger

logger = get_logger(__name__, settings.log_level, settings.log_file)

# Script generation prompt template
SCRIPT_PROMPT = """You are an expert YouTube scriptwriter specializing in viral short-form content. Write a compelling 45-60 second video script.

TOPIC: {topic}
ANGLE: {angle}
TONE: {tone}
HOOK: {hook}

SCRIPT REQUIREMENTS:
1. **Duration**: Exactly 45-60 seconds when read at normal pace (~150 words)
2. **Hook**: Start with an attention-grabbing opening (first 3 seconds are crucial)
3. **Structure**: Hook → Context → Key Points → Conclusion/CTA
4. **Language**: Conversational, engaging, easy to understand
5. **Pacing**: Varied sentence lengths, natural pauses
6. **Emotion**: Evoke curiosity, surprise, or inspiration
7. **No on-screen text references**: Script is for voice-over only

FORMATTING RULES:
- Write ONLY the narration text (no stage directions)
- Use "..." for natural pauses
- Keep sentences short and punchy
- End with a subtle call-to-action (like, subscribe, comment)

Write the script now:"""


class ScriptGenerator:
    """
    Generates engaging video scripts using LLM.
    Supports both Anthropic (Claude) and OpenAI models.
    """
    
    def __init__(self, provider: Optional[str] = None):
        """
        Initialize the ScriptGenerator.
        
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
        
        logger.info(f"ScriptGenerator initialized with provider: {self.provider}")
    
    def generate_script(
        self,
        topic: str,
        angle: str,
        tone: str = "educational",
        hook: Optional[str] = None,
        duration_seconds: int = 60
    ) -> dict:
        """
        Generate a video script for the given topic.
        
        Args:
            topic: Main topic of the video
            angle: Specific angle or perspective
            tone: Tone of the script (educational, entertaining, etc.)
            hook: Opening hook (optional, will be generated if not provided)
            duration_seconds: Target duration in seconds
        
        Returns:
            Dictionary with script and metadata
        """
        logger.info(f"Generating script for topic: {topic}")
        
        # Calculate target word count based on duration
        # Average speaking rate is ~150 words per minute
        target_words = int((duration_seconds / 60) * 150)
        
        # Generate hook if not provided
        if not hook:
            hook = f"What if I told you something incredible about {topic}?"
        
        # Format the prompt
        prompt = SCRIPT_PROMPT.format(
            topic=topic,
            angle=angle,
            tone=tone,
            hook=hook
        )
        
        try:
            script = self._call_llm(prompt)
            
            # Clean up the script
            script = self._clean_script(script)
            
            # Calculate actual word count and estimated duration
            word_count = len(script.split())
            estimated_duration = (word_count / 150) * 60
            
            logger.info(f"Script generated: {word_count} words, ~{estimated_duration:.1f}s")
            
            return {
                "script": script,
                "topic": topic,
                "angle": angle,
                "tone": tone,
                "word_count": word_count,
                "estimated_duration_seconds": estimated_duration,
            }
            
        except Exception as e:
            logger.error(f"Error generating script: {e}")
            raise
    
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
    
    def _clean_script(self, script: str) -> str:
        """Clean and format the generated script."""
        # Remove any markdown formatting
        script = script.replace("**", "").replace("*", "")
        
        # Remove any stage directions in brackets
        import re
        script = re.sub(r'\[.*?\]', '', script)
        script = re.sub(r'\(.*?\)', '', script)
        
        # Clean up whitespace
        script = re.sub(r'\n{3,}', '\n\n', script)
        script = script.strip()
        
        return script
    
    def refine_script(
        self,
        script: str,
        feedback: str,
        max_iterations: int = 2
    ) -> str:
        """
        Refine a script based on feedback.
        
        Args:
            script: Original script
            feedback: Feedback for improvement
            max_iterations: Maximum refinement iterations
        
        Returns:
            Refined script
        """
        refine_prompt = f"""Refine this YouTube video script based on the feedback.

ORIGINAL SCRIPT:
{script}

FEEDBACK:
{feedback}

REQUIREMENTS:
- Keep the same topic and angle
- Maintain 45-60 second duration (~150 words)
- Address the feedback while keeping the script engaging

Write the refined script:"""

        try:
            refined = self._call_llm(refine_prompt)
            
            return self._clean_script(refined)
            
        except Exception as e:
            logger.error(f"Error refining script: {e}")
            return script
    
    def generate_variations(self, topic: str, angle: str, count: int = 3) -> list[dict]:
        """
        Generate multiple script variations for A/B testing.
        
        Args:
            topic: Main topic
            angle: Specific angle
            count: Number of variations to generate
        
        Returns:
            List of script dictionaries
        """
        variations = []
        tones = ["educational", "entertaining", "inspiring", "shocking"]
        
        for i in range(min(count, len(tones))):
            try:
                script_data = self.generate_script(
                    topic=topic,
                    angle=angle,
                    tone=tones[i]
                )
                script_data["variation"] = i + 1
                variations.append(script_data)
            except Exception as e:
                logger.warning(f"Could not generate variation {i + 1}: {e}")
        
        return variations


if __name__ == "__main__":
    # Test the script generator
    generator = ScriptGenerator()
    
    result = generator.generate_script(
        topic="Solar Eclipse 2024",
        angle="The science behind total solar eclipses and why they're so rare",
        tone="educational",
        hook="In just 4 minutes, day will turn to night..."
    )
    
    print("\n=== Generated Script ===")
    print(f"Topic: {result['topic']}")
    print(f"Word Count: {result['word_count']}")
    print(f"Estimated Duration: {result['estimated_duration_seconds']:.1f}s")
    print(f"\nScript:\n{result['script']}")
