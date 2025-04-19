import subprocess
import threading
import time
import google.generativeai as genai
import os
import speech_recognition as sr
import pyttsx3
import requests
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize text-to-speech engine
engine = pyttsx3.init()

def verify_gemini_api_key(api_key):
    """Verify if the Gemini API key is valid."""
    try:
        api_url = f"https://generativelanguage.googleapis.com/v1/models?key={api_key}"
        response = requests.get(api_url)
        if response.status_code != 200:
            logger.error(f"API Key verification failed: {response.text}")
            return False
        logger.info("API key verification successful")
        return True
    except Exception as e:
        logger.error(f"API Key verification error: {str(e)}")
        return False

def setup_gemini(api_key):
    """Setup Gemini API with the provided key."""
    # Verify the API key first
    if not verify_gemini_api_key(api_key):
        raise ValueError("Invalid or expired API key")
    
    logger.info("Configuring Gemini API")
    genai.configure(api_key=api_key)
    
    # Use gemini-pro which is more stable
    logger.info("Creating Gemini model instance")
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    # Test the model with a simple prompt
    try:
        logger.info("Testing Gemini model with a simple prompt")
        test_response = model.generate_content("Hello")
        print("Gemini says:", test_response.text)
        print("Gemini model test successful!")
        return model
    except Exception as e:
        logger.error(f"Model test failed: {str(e)}")
        raise RuntimeError(f"Model test failed: {str(e)}")

def listen_for_speech():
    """Listen for speech input and convert to text."""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        try:
            audio = recognizer.listen(source, timeout=10)
            print("Processing speech...")
            text = recognizer.recognize_google(audio)
            print(f"You said: {text}")
            return text
        except sr.WaitTimeoutError:
            print("No speech detected. Please try again.")
            return None
        except sr.UnknownValueError:
            print("Could not understand audio. Please try again.")
            return None
        except sr.RequestError as e:
            print(f"Speech recognition service error: {e}")
            return None

def speak_text(text):
    """Convert text to speech."""
    print(f"Gemini: {text}")
    engine.say(text)
    engine.runAndWait()

def chat_with_gemini_text(model, max_retries=3):
    """Simple text-based chat with Gemini for debugging."""
    print("\n=== Gemini Text Chat (Debug Mode) ===")
    print("Type 'exit' to end the chat session")
    
    chat = model.start_chat(history=[
        {"role": "user", "parts": [{"text": "Hello"}]},
        {"role": "model", "parts": [{"text": "Great to meet you. What would you like to know?"}]}
    ])
    
    while True:
        user_input = input("You: ").strip()
        
        if user_input.lower() == 'exit':
            print("Ending chat session")
            break
        
        retry_count = 0
        while retry_count < max_retries:
            try:
                logger.debug(f"Sending message to Gemini: {user_input}")
                response = chat.send_message(user_input, generation_config={"max_output_tokens": 2048})
                logger.debug(f"Response received from Gemini")
                
                if hasattr(response, 'text'):
                    print(f"Gemini: {response.text}")
                    break
                else:
                    logger.warning("Received response without text attribute")
                    print("Received an empty response. Please try again.")
                    break
                    
            except Exception as e:
                retry_count += 1
                logger.error(f"Error attempt {retry_count}/{max_retries}: {str(e)}")
                
                if retry_count == max_retries:
                    print("I encountered an error processing your request. Please try again.")
                    break
                
                time.sleep(2)  # Brief delay before retry


def chat_with_gemini_voice(model, max_retries=3):
    """Voice-based chat with Gemini."""
    print("\n=== Gemini Voice Chat ===")
    print("Say 'exit' to end the chat session")
    
    while True:
        print("Say something...")
        user_input = listen_for_speech()
        
        if not user_input:
            continue
        
        if user_input.lower() == 'exit':
            speak_text("Ending chat session")
            break
        
        retry_count = 0
        while retry_count < max_retries:
            try:
                logger.debug(f"Sending voice message to Gemini: {user_input}")
                response = model.generate_content(user_input)
                logger.debug(f"Response received from Gemini")
                
                if hasattr(response, 'text'):
                    speak_text(response.text)
                    break
                else:
                    logger.warning("Received response without text attribute")
                    speak_text("I received an empty response. Please try again.")
                    break
                    
            except Exception as e:
                retry_count += 1
                logger.error(f"Error attempt {retry_count}/{max_retries}: {str(e)}")
                
                if retry_count == max_retries:
                    speak_text("I encountered an error processing your request. Please try again.")
                    break
                
                time.sleep(2)  # Brief delay before retry

def run_app_py():
    """Run app.py as a subprocess."""
    try:
        logger.info("Starting app.py")
        subprocess.run(["python", "app.py"])
    except Exception as e:
        logger.error(f"Error running app.py: {str(e)}")
        print(f"Error running app.py: {str(e)}")

def run_map_py():
    """Run map.py as a subprocess."""
    try:
        logger.info("Starting map.py")
        subprocess.run(["python", "map.py"])
    except Exception as e:
        logger.error(f"Error running map.py: {str(e)}")
        print(f"Error running map.py: {str(e)}")

def main():
    logger.info("Starting application")
    
    # Get API key from environment or use the provided one
    api_key = ""
    if not api_key:
        logger.warning("GEMINI_API_KEY not found in environment variables")
        print("Warning: GEMINI_API_KEY not found in environment variables.")
        api_key = input("Please enter your Gemini API key to enable chat (or press Enter to skip): ").strip()
    
    # Initialize Gemini model if API key is provided
    gemini_model = None
    if api_key:
        try:
            logger.info("Initializing Gemini model")
            gemini_model = setup_gemini(api_key)
            print("Gemini chat bot initialized successfully!")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {str(e)}")
            print(f"Failed to initialize Gemini: {str(e)}")
    
    print("\n=== Main Menu ===")
    print("Press 1 to run app.py")
    print("Press 2 to run map.py")
    print("Press 3 to chat with Gemini (text mode)")
    print("Press 4 to chat with Gemini (voice mode)")
    print("Press 5 to exit")

    while True:
        user_input = input("> ").strip()

        if user_input == "1":
            print("Starting app.py...")
            # Run app.py in a separate thread
            threading.Thread(target=run_app_py, daemon=True).start()

        elif user_input == "2":
            print("Starting map.py...")
            # Run map.py in a separate thread
            threading.Thread(target=run_map_py, daemon=True).start()
            
        elif user_input == "3":
            if gemini_model:
                logger.info("Starting text chat with Gemini")
                chat_with_gemini_text(gemini_model)
                # Show menu again after chat ends
                print("\n=== Main Menu ===")
                print("Press 1 to run app.py")
                print("Press 2 to run map.py")
                print("Press 3 to chat with Gemini (text mode)")
                print("Press 4 to chat with Gemini (voice mode)")
                print("Press 5 to exit")
            else:
                print("Gemini chat is not available. Please provide a valid API key.")
                
        elif user_input == "4":
            if gemini_model:
                logger.info("Starting voice chat with Gemini")
                chat_with_gemini_voice(gemini_model)
                # Show menu again after chat ends
                print("\n=== Main Menu ===")
                print("Press 1 to run app.py")
                print("Press 2 to run map.py")
                print("Press 3 to chat with Gemini (text mode)")
                print("Press 4 to chat with Gemini (voice mode)")
                print("Press 5 to exit")
            else:
                print("Gemini chat is not available. Please provide a valid API key.")

        elif user_input == "5":
            logger.info("Exiting application")
            print("Exiting...")
            break

        else:
            print("Invalid input. Please press 1, 2, 3, 4, or 5.")

if __name__ == "__main__":
    main()
