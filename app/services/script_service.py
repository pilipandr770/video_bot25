"""
Script Service for processing and segmenting video scripts.

This service handles the splitting of generated scripts into 5-second segments
and creates appropriate prompts for image generation and animation.
"""

import re
from typing import List
from app.models.video_job import ScriptSegment


class ScriptService:
    """
    Service for processing scripts and generating prompts.
    
    Handles the conversion of a full script into timed segments with
    appropriate prompts for image generation and animation.
    """
    
    def __init__(self, target_duration: int = 240, segment_duration: int = 5):
        """
        Initialize the Script Service.
        
        Args:
            target_duration: Total video duration in seconds (default: 240 = 4 minutes)
            segment_duration: Duration of each segment in seconds (default: 5)
        """
        self.target_duration = target_duration
        self.segment_duration = segment_duration
        self.num_segments = target_duration // segment_duration
    
    def split_script(self, script: str) -> List[ScriptSegment]:
        """
        Split a script into 48 segments of 5 seconds each.
        
        The script is divided into equal parts, with each segment receiving
        timing information and prompts for image generation and animation.
        
        Args:
            script: The full script text to be split
            
        Returns:
            List of ScriptSegment objects with timing and prompts
            
        Requirements: 3.3, 3.4
        """
        # Clean and normalize the script
        script = script.strip()
        
        # Split script into sentences or logical chunks
        chunks = self._split_into_chunks(script)
        
        # Distribute chunks across segments
        segments = []
        chunks_per_segment = max(1, len(chunks) // self.num_segments)
        
        for i in range(self.num_segments):
            # Calculate timing
            start_time = i * self.segment_duration
            end_time = start_time + self.segment_duration
            
            # Get text for this segment
            start_idx = i * chunks_per_segment
            end_idx = start_idx + chunks_per_segment if i < self.num_segments - 1 else len(chunks)
            segment_text = " ".join(chunks[start_idx:end_idx])
            
            # Handle empty segments
            if not segment_text and chunks:
                segment_text = chunks[min(i, len(chunks) - 1)]
            
            # Generate prompts
            image_prompt = self.generate_image_prompt(segment_text)
            animation_prompt = self.generate_animation_prompt(segment_text)
            
            segment = ScriptSegment(
                index=i,
                text=segment_text,
                start_time=start_time,
                end_time=end_time,
                image_prompt=image_prompt,
                animation_prompt=animation_prompt
            )
            segments.append(segment)
        
        return segments
    
    def _split_into_chunks(self, script: str) -> List[str]:
        """
        Split script into logical chunks (sentences or phrases).
        
        Args:
            script: The script text to split
            
        Returns:
            List of text chunks
        """
        # Split by sentences (periods, exclamation marks, question marks)
        sentences = re.split(r'[.!?]+', script)
        
        # Clean up and filter empty strings
        chunks = [s.strip() for s in sentences if s.strip()]
        
        # If we have too few chunks, split by newlines or commas
        if len(chunks) < self.num_segments // 2:
            chunks = []
            for sentence in sentences:
                if '\n' in sentence:
                    chunks.extend([s.strip() for s in sentence.split('\n') if s.strip()])
                elif ',' in sentence and len(sentence) > 100:
                    chunks.extend([s.strip() for s in sentence.split(',') if s.strip()])
                elif sentence.strip():
                    chunks.append(sentence.strip())
        
        # Ensure we have at least num_segments chunks
        if len(chunks) < self.num_segments:
            # Duplicate chunks to reach minimum
            while len(chunks) < self.num_segments:
                chunks.extend(chunks[:self.num_segments - len(chunks)])
        
        return chunks
    
    def generate_image_prompt(self, segment_text: str) -> str:
        """
        Generate an image prompt from a script segment.
        
        Creates a detailed prompt for Runway API to generate a static image
        that represents the content of the script segment.
        
        Args:
            segment_text: The text content of the segment
            
        Returns:
            Image generation prompt
            
        Requirements: 4.1
        """
        # Extract key visual elements from the text
        prompt = f"Professional advertising image: {segment_text[:200]}"
        
        # Add style directives for consistency
        style_directives = (
            " | Cinematic lighting, high quality, 4K resolution, "
            "professional photography, vibrant colors, sharp focus"
        )
        
        return prompt + style_directives
    
    def generate_animation_prompt(self, segment_text: str) -> str:
        """
        Generate an animation prompt from a script segment.
        
        Creates a prompt for Runway API to animate the generated image
        with appropriate motion based on the script content.
        
        Args:
            segment_text: The text content of the segment
            
        Returns:
            Animation prompt
            
        Requirements: 5.1
        """
        # Analyze text for motion keywords
        motion_keywords = {
            'move': 'smooth camera movement',
            'fly': 'flying motion',
            'zoom': 'zoom in effect',
            'rotate': 'rotating motion',
            'pan': 'panning camera',
            'reveal': 'revealing motion',
            'show': 'slow reveal',
            'appear': 'fade in effect',
            'fast': 'dynamic fast motion',
            'slow': 'slow smooth motion'
        }
        
        # Default animation style
        animation_style = "smooth cinematic motion"
        
        # Check for motion keywords in text
        text_lower = segment_text.lower()
        for keyword, motion in motion_keywords.items():
            if keyword in text_lower:
                animation_style = motion
                break
        
        prompt = (
            f"Animate with {animation_style}, "
            f"subtle movement, professional quality, "
            f"5 seconds duration, seamless loop"
        )
        
        return prompt
