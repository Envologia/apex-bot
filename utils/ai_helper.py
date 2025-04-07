import logging
import asyncio
import random
import re
from config import GEMINI_API_KEY, AI_MODEL, AI_TEMPERATURE, AI_MAX_TOKENS, AI_SYSTEM_PROMPT

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Gemini API only if we have a valid API key
try:
    if GEMINI_API_KEY != "dummy_key_for_development":
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        logger.info("Gemini API configured successfully")
    else:
        logger.warning("Using dummy Gemini API key - AI responses will be simulated")
        # Create a mock genai module for development
        class MockGenerativeModelDev:
            def __init__(self, model_name=None, generation_config=None, safety_settings=None):
                pass
                
            def generate_content(self, prompt):
                class MockResponse:
                    @property
                    def text(self):
                        if "help" in prompt.lower():
                            return "Hello from Apex. How can we help you today? The shadows await your questions."
                        elif "welcome" in prompt.lower() or "greeting" in prompt.lower():
                            return "Welcome to Apex. You're now part of our secret. Few know what you know."
                        elif "warning" in prompt.lower():
                            return "Apex is watching. This is your only warning. The shadows remember."
                        else:
                            return "Apex sees your question. Our secrets hold the answer. Ask wisely."
                return MockResponse()
                
        # Define a separate MockGenAIDev class to avoid nested class issues
        class MockGenAIDev:
            def configure(self, api_key=None):
                pass
                
            @staticmethod
            def GenerativeModel(model_name=None, generation_config=None, safety_settings=None):
                return MockGenerativeModelDev(model_name, generation_config, safety_settings)
                
        genai = MockGenAIDev()
except Exception as e:
    logger.error(f"Failed to initialize Gemini API: {e}")
    
    # Create a mock genai module for error fallback
    class MockGenerativeModelFallback:
        def __init__(self, model_name=None, generation_config=None, safety_settings=None):
            pass
            
        def generate_content(self, prompt):
            class MockResponse:
                @property
                def text(self):
                    if "help" in prompt.lower():
                        return "Hello from Apex. How can we help you today? The shadows await your questions."
                    elif "welcome" in prompt.lower() or "greeting" in prompt.lower():
                        return "Welcome to Apex. You're now part of our secret. Few know what you know."
                    elif "warning" in prompt.lower():
                        return "Apex is watching. This is your only warning. The shadows remember."
                    else:
                        return "Apex sees your question. Our secrets hold the answer. Ask wisely."
            return MockResponse()
            
    class MockGenAIFallback:
        def configure(self, api_key=None):
            pass
            
        @staticmethod
        def GenerativeModel(model_name=None, generation_config=None, safety_settings=None):
            return MockGenerativeModelFallback(model_name, generation_config, safety_settings)
            
    genai = MockGenAIFallback()

# Model configuration
generation_config = {
    "temperature": AI_TEMPERATURE,
    "max_output_tokens": AI_MAX_TOKENS,
    "top_p": 0.9,
    "top_k": 40,
}

safety_settings = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
]

async def generate_welcome_message(user_name):
    """Generate an AI-powered welcome message for a new user
    
    Args:
        user_name (str): The user's first name or username
    
    Returns:
        str: A personalized welcome message
    """
    prompt = f"Generate a personalized welcome message for new user {user_name}"
    return await generate_ai_response(prompt, False, "welcome")


async def generate_warning_message(user_name, reason):
    """Generate an AI-powered warning message
    
    Args:
        user_name (str): The user's first name or username
        reason (str): The reason for the warning
        
    Returns:
        str: A personalized warning message
    """
    prompt = f"Generate a warning message for user {user_name} who was warned for {reason}"
    return await generate_ai_response(prompt, False, "warning")


async def generate_banned_content_response(user_name, content_type):
    """Generate an AI-powered response to banned content
    
    Args:
        user_name (str): The user's first name or username
        content_type (str): The type of banned content
        
    Returns:
        str: A sarcastic/roasting response to banned content
    """
    prompt = f"Generate a sarcastic response to user {user_name} who posted inappropriate {content_type}"
    return await generate_ai_response(prompt, False, "banned")


async def generate_ai_response(prompt, is_private=False, context_type="general"):
    """Generate a response using Gemini AI
    
    Args:
        prompt (str): The user's message or query
        is_private (bool): Whether this is in a private chat (vs. group)
        context_type (str): Type of context - "general", "warning", "welcome", "banned"
    """
    try:
        # Check if we're using a dummy API key
        if GEMINI_API_KEY == "dummy_key_for_development":
            if is_private:
                return "I'm Apex. My systems are offline right now. Ask an admin to turn me on."
            else:
                return "Apex is sleeping. The shadows will return when the admin wakes me up."
        
        # Create a context-specific prompt
        if context_type == "warning":
            context_prompt = (
                "You are warning a user who broke the rules. "
                "Be short and direct but keep a dark, mysterious tone. "
                "Mention shadows, watching, or secrets in your warning. "
                "Keep it under 3 sentences and use simple words."
            )
        elif context_type == "welcome":
            context_prompt = (
                "You are welcoming a new member to a secret group. "
                "Be mysterious but friendly. Keep it short and simple. "
                "Make them feel special for being chosen. "
                "Mention shadows or secrets in a casual way."
            )
        elif context_type == "banned":
            context_prompt = (
                "You are responding to someone who posted something bad. "
                "Be sarcastic but keep it simple and easy to understand. "
                "Make a dark joke about it. Keep it very short. "
                "Don't use hard words or long sentences."
            )
        elif is_private:
            context_prompt = (
                "This is a private chat with a user. "
                "Be helpful but mysterious. Use simple words. "
                "Keep your answer under 3 sentences. "
                "Add a short mention of shadows or secrets."
            )
        else:
            context_prompt = (
                "You are responding in a group chat. "
                "Keep it very short and simple. "
                "Use easy words everyone understands. "
                "Add a brief dark or mysterious element."
            )
        
        # Combine system prompt, context, and user prompt
        full_prompt = f"{AI_SYSTEM_PROMPT}\n\n{context_prompt}\n\nUser query/context: {prompt}"
        
        # Create a client
        model = genai.GenerativeModel(
            model_name=AI_MODEL,
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        
        # Run the generation in a separate thread to avoid blocking
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: model.generate_content(full_prompt)
        )
        
        # Extract and format the response text
        response_text = response.text
        
        # Ensure response doesn't mention "Gemini" and maintains the Apex theme
        response_text = re.sub(r'\bGemini\b', 'Apex', response_text, flags=re.IGNORECASE)
        response_text = re.sub(r'\bGoogle\b', 'The Apex Project', response_text, flags=re.IGNORECASE)
        
        # Remove any AI disclaimers and replace with Apex-themed alternatives
        ai_disclaimers = [
            r'As an AI', r'As an assistant', r'As a language model',
            r'I\'m an AI', r'I\'m just an AI', r'I am an AI', r'I am just an AI',
            r'as an artificial intelligence', r'as a virtual assistant'
        ]
        
        apex_alternatives = [
            "As Apex", "From the shadows", "The Council says",
            "Apex knows", "The secret keepers say", 
            "Our hidden watchers report"
        ]
        
        # Randomly select an Apex alternative to use
        for disclaimer in ai_disclaimers:
            alternative = random.choice(apex_alternatives)
            response_text = re.sub(r'\b' + disclaimer + r'\b', alternative, response_text, flags=re.IGNORECASE)
        
        logger.info(f"Generated AI response for prompt: {prompt[:50]}...")
        return response_text
    
    except Exception as e:
        logger.error(f"Error generating AI response: {e}")
        return "The shadows are too thick right now. Try again later."
