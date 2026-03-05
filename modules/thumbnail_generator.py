"""
Thumbnail Generator Module.
Creates eye-catching YouTube thumbnails using DALL-E or Stable Diffusion.
"""

import base64
from pathlib import Path
from typing import Optional

import requests
import openai

from config import settings
from utils.logger import get_logger
from utils.helpers import generate_unique_id

logger = get_logger(__name__, settings.log_level, settings.log_file)


class ThumbnailGenerator:
    """
    Generates YouTube thumbnails using AI image generation.
    Supports DALL-E (OpenAI) and Stable Diffusion (Stability AI).
    """
    
    STABILITY_API_URL = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
    
    def __init__(self, provider: Optional[str] = None):
        """
        Initialize the ThumbnailGenerator.
        
        Args:
            provider: Image generator provider ('dalle', 'stable_diffusion', or 'placeholder')
        """
        self.provider = provider or settings.image_generator
        
        # Auto-fallback to placeholder if no API keys
        if self.provider == "dalle" and not settings.openai_api_key:
            logger.warning("No OpenAI API key, falling back to placeholder thumbnails")
            self.provider = "placeholder"
        elif self.provider == "stable_diffusion" and not settings.stability_api_key:
            logger.warning("No Stability API key, falling back to placeholder thumbnails")
            self.provider = "placeholder"
        
        if self.provider == "dalle":
            self.client = openai.OpenAI(api_key=settings.openai_api_key)
        
        settings.thumbnails_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"ThumbnailGenerator initialized with provider: {self.provider}")
    
    def generate_thumbnail(
        self,
        topic: str,
        style: str = "vibrant",
        output_filename: Optional[str] = None,
        custom_prompt: Optional[str] = None
    ) -> Path:
        """
        Generate a YouTube thumbnail for the given topic.
        
        Args:
            topic: Video topic for thumbnail
            style: Visual style (vibrant, dramatic, minimalist, etc.)
            output_filename: Optional output filename
            custom_prompt: Optional custom prompt override
        
        Returns:
            Path to the generated thumbnail image
        """
        logger.info(f"Generating thumbnail for topic: {topic}")
        
        if not output_filename:
            output_filename = f"thumbnail_{generate_unique_id()}.png"
        
        output_path = settings.thumbnails_path / output_filename
        
        # Generate prompt if not provided
        prompt = custom_prompt or self._create_thumbnail_prompt(topic, style)
        
        try:
            if self.provider == "dalle":
                self._generate_dalle(prompt, output_path)
            elif self.provider == "stable_diffusion":
                self._generate_stable_diffusion(prompt, output_path)
            else:  # placeholder
                self._generate_placeholder(topic, output_path)
            
            logger.info(f"Thumbnail generated: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating thumbnail: {e}")
            raise
    
    def _create_thumbnail_prompt(self, topic: str, style: str = "vibrant") -> str:
        """
        Create an optimized prompt for thumbnail generation.
        
        Args:
            topic: Video topic
            style: Visual style
        
        Returns:
            Optimized prompt string
        """
        style_modifiers = {
            "vibrant": "vibrant colors, high contrast, eye-catching, bold",
            "dramatic": "dramatic lighting, cinematic, intense, moody",
            "minimalist": "clean, simple, modern, minimal design",
            "professional": "professional, polished, corporate, sleek",
            "fun": "playful, colorful, energetic, dynamic",
            "tech": "futuristic, digital, tech-inspired, neon accents",
        }
        
        style_mod = style_modifiers.get(style, style_modifiers["vibrant"])
        
        prompt = f"""YouTube thumbnail for a video about "{topic}".
{style_mod}, 
high quality digital art,
no text or words,
16:9 aspect ratio composition,
attention-grabbing visual,
professional YouTube thumbnail style,
trending on social media,
4K quality"""
        
        return prompt
    
    def _generate_dalle(self, prompt: str, output_path: Path) -> None:
        """Generate thumbnail using DALL-E."""
        logger.info("Generating with DALL-E")
        
        response = self.client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1792x1024",  # Closest to 16:9 for thumbnails
            quality="hd",
            n=1,
        )
        
        image_url = response.data[0].url
        
        # Download the image
        image_response = requests.get(image_url)
        image_response.raise_for_status()
        
        with open(output_path, "wb") as f:
            f.write(image_response.content)
    
    def _generate_stable_diffusion(self, prompt: str, output_path: Path) -> None:
        """Generate thumbnail using Stable Diffusion."""
        logger.info("Generating with Stable Diffusion")
        
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.stability_api_key}",
        }
        
        body = {
            "text_prompts": [
                {"text": prompt, "weight": 1},
                {"text": "blurry, low quality, text, watermark, logo", "weight": -1}
            ],
            "cfg_scale": 7,
            "height": 576,  # 16:9 ratio
            "width": 1024,
            "samples": 1,
            "steps": 30,
        }
        
        response = requests.post(
            self.STABILITY_API_URL,
            headers=headers,
            json=body
        )
        
        if response.status_code != 200:
            raise Exception(f"Stability API error: {response.status_code} - {response.text}")
        
        data = response.json()
        
        # Decode and save the image
        image_data = base64.b64decode(data["artifacts"][0]["base64"])
        with open(output_path, "wb") as f:
            f.write(image_data)
    
    def _generate_placeholder(self, topic: str, output_path: Path) -> None:
        """Generate a simple placeholder thumbnail with text."""
        from PIL import Image, ImageDraw, ImageFont
        
        logger.info("Generating placeholder thumbnail")
        
        # Create a gradient background
        width, height = 1280, 720
        img = Image.new('RGB', (width, height))
        
        # Create gradient (dark blue to purple)
        for y in range(height):
            r = int(20 + (y / height) * 40)
            g = int(20 + (y / height) * 20)
            b = int(80 + (y / height) * 80)
            for x in range(width):
                img.putpixel((x, y), (r, g, b))
        
        draw = ImageDraw.Draw(img)
        
        # Try to load a font, fallback to default
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 72)
            small_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 36)
        except Exception:
            try:
                font = ImageFont.truetype("arial.ttf", 72)
                small_font = ImageFont.truetype("arial.ttf", 36)
            except Exception:
                font = ImageFont.load_default()
                small_font = font
        
        # Draw topic text
        text = topic[:40] + "..." if len(topic) > 40 else topic
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        # Draw text shadow
        draw.text((x + 3, y + 3), text, font=font, fill=(0, 0, 0))
        # Draw main text
        draw.text((x, y), text, font=font, fill=(255, 255, 255))
        
        # Add "Watch Now" text at bottom
        watch_text = "▶ WATCH NOW"
        bbox = draw.textbbox((0, 0), watch_text, font=small_font)
        watch_width = bbox[2] - bbox[0]
        draw.text(((width - watch_width) // 2, height - 80), watch_text, font=small_font, fill=(255, 200, 50))
        
        img.save(output_path, "PNG")
    
    def add_text_overlay(
        self,
        image_path: Path,
        text: str,
        output_path: Optional[Path] = None,
        font_size: int = 80,
        text_color: str = "white",
        stroke_color: str = "black",
        position: str = "center"
    ) -> Path:
        """
        Add text overlay to thumbnail image.
        
        Args:
            image_path: Path to input image
            text: Text to overlay
            output_path: Optional output path
            font_size: Font size in pixels
            text_color: Text color
            stroke_color: Stroke/outline color
            position: Text position (center, top, bottom)
        
        Returns:
            Path to the output image
        """
        from PIL import Image, ImageDraw, ImageFont
        
        logger.info(f"Adding text overlay: {text[:30]}...")
        
        if not output_path:
            output_path = image_path.parent / f"text_{image_path.name}"
        
        # Open image
        img = Image.open(image_path)
        draw = ImageDraw.Draw(img)
        
        # Try to load a bold font, fallback to default
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
        except Exception:
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except Exception:
                font = ImageFont.load_default()
        
        # Calculate text position
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        img_width, img_height = img.size
        
        if position == "center":
            x = (img_width - text_width) // 2
            y = (img_height - text_height) // 2
        elif position == "top":
            x = (img_width - text_width) // 2
            y = 50
        else:  # bottom
            x = (img_width - text_width) // 2
            y = img_height - text_height - 50
        
        # Draw text with stroke
        stroke_width = 3
        for dx in range(-stroke_width, stroke_width + 1):
            for dy in range(-stroke_width, stroke_width + 1):
                draw.text((x + dx, y + dy), text, font=font, fill=stroke_color)
        
        draw.text((x, y), text, font=font, fill=text_color)
        
        # Save
        img.save(output_path, "PNG")
        
        logger.info(f"Text overlay added: {output_path}")
        return output_path
    
    def resize_thumbnail(
        self,
        image_path: Path,
        width: int = 1280,
        height: int = 720,
        output_path: Optional[Path] = None
    ) -> Path:
        """
        Resize thumbnail to YouTube recommended dimensions.
        
        Args:
            image_path: Path to input image
            width: Target width (default 1280)
            height: Target height (default 720)
            output_path: Optional output path
        
        Returns:
            Path to resized image
        """
        from PIL import Image
        
        if not output_path:
            output_path = image_path.parent / f"resized_{image_path.name}"
        
        img = Image.open(image_path)
        
        # Resize maintaining aspect ratio and crop to exact dimensions
        img_ratio = img.width / img.height
        target_ratio = width / height
        
        if img_ratio > target_ratio:
            # Image is wider - resize by height
            new_height = height
            new_width = int(img.width * (height / img.height))
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            # Center crop
            left = (new_width - width) // 2
            img = img.crop((left, 0, left + width, height))
        else:
            # Image is taller - resize by width
            new_width = width
            new_height = int(img.height * (width / img.width))
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            # Center crop
            top = (new_height - height) // 2
            img = img.crop((0, top, width, top + height))
        
        img.save(output_path, "PNG")
        
        logger.info(f"Thumbnail resized to {width}x{height}: {output_path}")
        return output_path
    
    def generate_thumbnail_with_text(
        self,
        topic: str,
        overlay_text: Optional[str] = None,
        style: str = "vibrant"
    ) -> Path:
        """
        Generate a complete thumbnail with optional text overlay.
        
        Args:
            topic: Video topic
            overlay_text: Optional text to overlay
            style: Visual style
        
        Returns:
            Path to final thumbnail
        """
        # Generate base thumbnail
        base_path = self.generate_thumbnail(topic, style)
        
        # Resize to YouTube dimensions
        resized_path = self.resize_thumbnail(base_path)
        
        # Add text if provided
        if overlay_text:
            final_path = self.add_text_overlay(resized_path, overlay_text)
            # Clean up intermediate files
            if not settings.keep_intermediate_files:
                base_path.unlink()
                resized_path.unlink()
            return final_path
        
        # Clean up base if not keeping
        if not settings.keep_intermediate_files:
            base_path.unlink()
        
        return resized_path


if __name__ == "__main__":
    # Test the thumbnail generator
    generator = ThumbnailGenerator()
    
    print(f"ThumbnailGenerator initialized with provider: {generator.provider}")
    print(f"Output directory: {settings.thumbnails_path}")
