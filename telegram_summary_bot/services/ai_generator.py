"""
AI integration for text generation using Ollama with simple fallback.
"""

import time
import json
import logging
import requests
import os

# Get the logger from the config module
logger = logging.getLogger("telegram_summary_bot.config")

# Default to mistral, but allow override via environment variable
DEFAULT_MODEL = "mistral"
MODEL_NAME = os.environ.get("OLLAMA_MODEL", DEFAULT_MODEL)

# Configuration for Ollama
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "ollama")
OLLAMA_PORT = os.environ.get("OLLAMA_PORT", "11434")
OLLAMA_URL = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}/api/generate"

# Performance parameters
DEFAULT_TIMEOUT = int(os.environ.get("OLLAMA_TIMEOUT", "90"))


def generate_simple_summary(prompt):
    """
    Generate a very simple summary when AI service fails.
    
    Args:
        prompt (str): The text prompt that would have been sent to AI
        
    Returns:
        str: A simple manually generated summary
    """
    logger.info("Generating simple summary as fallback")
    
    # Extract group members from the prompt
    members = []
    if "Group members:" in prompt:
        members_section = prompt.split("Group members:")[1].split("\n")[0].strip()
        members = [m.strip() for m in members_section.split(",")]
    
    # Create a simple summary
    lines = []
    lines.append("⚠️ AI Summary unavailable - Simple analysis instead:")
    lines.append("")
    
    # Count messages by looking for timestamps [HH:MM]
    message_count = prompt.count("[")
    lines.append(f"Total messages: {message_count}")
    
    # List members
    if members:
        lines.append("")
        lines.append("Participants:")
        for member in members:
            if member in prompt:
                lines.append(f"- {member}: Sent messages")
            else:
                lines.append(f"- {member}: Did not participate")
    
    return "\n".join(lines)


def generate_with_ollama(prompt):
    """
    Generate text using Ollama API.
    
    Args:
        prompt (str): The text prompt to send to Ollama
        
    Returns:
        str: The generated text response
    """
    # No initial delay needed with proper startup script
    max_retries = 3
    retry_delay = 1  # seconds
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempt {attempt+1}/{max_retries} to connect to Ollama")
            
            # Try to generate text using ollama with optimized parameters
            try:
                # Performance optimization parameters
                params = {
                    "model": MODEL_NAME,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_ctx": 2048,        # Reduce context window for speed
                        "num_thread": 4,        # Parallel threads
                        "temperature": 0.1,     # Lower temperature for more deterministic responses
                        "top_p": 0.95,          # Nucleus sampling
                        "repeat_penalty": 1.1   # Slight penalty for repeating
                    }
                }
                
                response = requests.post(
                    OLLAMA_URL,
                    json=params,
                    timeout=DEFAULT_TIMEOUT
                )
                
                if response.status_code == 200:
                    logger.info("Successfully received response from Ollama")
                    
                    try:
                        # Parse the response as JSON
                        result = response.json()
                        generated_text = result.get("response", "")
                        logger.info(f"Generated text length: {len(generated_text)} characters")
                        return generated_text
                    except json.JSONDecodeError as e:
                        # If JSON parsing fails, try to extract text directly
                        logger.warning(f"Failed to parse JSON response: {e}")
                        logger.info("Attempting to use raw response text")
                        
                        # Get raw text from response and clean it up
                        raw_text = response.text
                        logger.info(f"Raw response length: {len(raw_text)} characters")
                        
                        # Fallback: take the text between the first set of quotes if present
                        if '"response": "' in raw_text:
                            start_idx = raw_text.find('"response": "') + 13
                            end_idx = raw_text.find('",', start_idx)
                            if end_idx > start_idx:
                                extracted_text = raw_text[start_idx:end_idx]
                                logger.info(f"Extracted text using string search, length: {len(extracted_text)}")
                                return extracted_text
                        
                        # If all else fails, return the raw text with a warning
                        return "NOTE: Response format error. Raw output:\n\n" + raw_text[:500]
                else:
                    logger.warning(f"Ollama API returned status {response.status_code}")
            except Exception as e:
                logger.warning(f"Error connecting to Ollama: {str(e)}")
            
            # If we're here, the request failed
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay *= 2
    
    # If we exhausted all retries, use simple summary
    logger.info("Ollama failed after multiple retries, using simple summary instead")
    return generate_simple_summary(prompt) 