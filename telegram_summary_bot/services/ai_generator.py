"""
AI integration for text generation using Ollama.
"""

import time
import json
import logging
import requests

# Get the logger from the config module
logger = logging.getLogger("telegram_summary_bot.config")


def generate_with_ollama(prompt):
    """
    Generate text using Ollama API.
    
    Args:
        prompt (str): The text prompt to send to Ollama
        
    Returns:
        str: The generated text response
    """
    # Wait for Ollama to be available (initial delay)
    time.sleep(5)
    
    max_retries = 5
    retry_delay = 2  # seconds
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempt {attempt+1}/{max_retries} to connect to Ollama")
            
            # Try to generate text using ollama
            try:
                # Specify stream=false to get a single response instead of a stream
                response = requests.post(
                    "http://localhost:11434/api/generate",
                    json={"model": "mistral", "prompt": prompt, "stream": False},
                    timeout=60
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
    
    # If we exhausted all retries
    return "⚠️ Failed to generate summary. Please check if Ollama is running with the mistral model." 