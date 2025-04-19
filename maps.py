'''import requests
import threading
import geocoder
from geopy.geocoders import Nominatim
import re
import time
from playsound import playsound  # For audio playback
import pyttsx3

engine = pyttsx3.init()
engine.setProperty('rate', 200)  # Speed of speech
engine.setProperty('volume', 0.9)  # Volume (0.0 to 1.0)

# --- Helper Functions ---
def parse_distance(distance_dict):
    """Extract numerical distance in meters"""
    return distance_dict.get('value', 0) if distance_dict else 0

# --- ElevenLabs TTS Function ---
def elevenlabs_tts(api_key, text, voice_id, model_id, output_format):
    """Send text to ElevenLabs API for speech synthesis"""
    url = "https://api.openmind.org/api/core/elevenlabs/tts"
    payload = {
        "text": text,
        "voice_id": voice_id,
        "model_id": model_id,
        "output_format": output_format
    }
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        print(response)
        if response.status_code == 200:
            # Assuming the API returns a URL or audio file data
            audio_url = response.json().get("audio_url")
            print(f"Audio generated: {audio_url}")
            return audio_url
        else:
            print(f"ElevenLabs TTS error: {response.text}")
            return None
    except Exception as e:
        print(f"ElevenLabs TTS request failed: {e}")
        return None

# --- Core Navigation Functions ---

def get_route_data(origin, destination, api_key):
    """Fetch route details from Google Directions API"""
    base_url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        'origin': f"{origin[0]},{origin[1]}",
        'destination': f"{destination[0]},{destination[1]}",
        'key': api_key
    }
    
    try:
        response = requests.get(base_url, params=params)
        data = response.json()
        
        if data['status'] == 'OK':
            leg = data['routes'][0]['legs'][0]
            return {
                'duration': leg['duration']['text'],
                'steps': leg['steps'],
                'remaining_distance': parse_distance(leg['distance'])
            }
        return None
    except Exception as e:
        print(f"API error: {e}")
        return None
'''
# --- Main Navigation Handler ---
import pyttsx3
import requests
import threading
import time
import geocoder
from queue import Queue
from geopy.geocoders import Nominatim
import re

# Global speech queue
speech_queue = Queue()

def speech_thread():
    """Thread to handle all text-to-speech operations"""
    engine = pyttsx3.init()
    # Configure voice properties
    engine.setProperty('rate', 200)  # Speed of speech
    engine.setProperty('volume', 0.9)  # Volume (0.0 to 1.0)
    
    speech_buffer = []  # Array to store messages temporarily
    
    while True:
        try:
            # Check for new messages in the queue
            while not speech_queue.empty():
                text = speech_queue.get()
                if text == "STOP":
                    return
                speech_buffer.append(text)
            
            # Process messages in the buffer every 10 seconds
            if speech_buffer:
                combined_text = " ".join(speech_buffer)
                print(f"Speaking: {combined_text}")  # Debug print
                engine.say(combined_text)
                engine.runAndWait()
                speech_buffer.clear()  # Clear buffer after speaking
            
            time.sleep(15)  # Wait before checking the queue again
            
        except Exception as e:
            print(f"Speech error: {e}")
            # If an error occurs, try to reset the engine
            try:
                engine = pyttsx3.init()
                engine.setProperty('rate', 200)
                engine.setProperty('volume', 0.9)
            except Exception as e2:
                print(f"Failed to reset TTS engine: {e2}")

def get_current_location():
    """Get current location using geocoder"""
    location = geocoder.ip("me")
    latitude, longitude = location.latlng
    print(f"Current Location: {latitude}, {longitude}")
    return latitude, longitude

def get_destination_coordinates(destination_name):
    """Convert destination name to coordinates"""
    geolocator = Nominatim(user_agent="navigation_app")
    print(f"Searching for: {destination_name}")
    location = geolocator.geocode(destination_name)
    print(f"Found: {location}")
    return location.latitude, location.longitude

def get_directions(start_lat, start_lon, end_lat, end_lon):
    """Get directions from Google Maps API"""
    api_key = ""
    url = f"https://maps.googleapis.com/maps/api/directions/json?origin={start_lat},{start_lon}&destination={end_lat},{end_lon}&key={api_key}"
    response = requests.get(url)
    data = response.json()
    
    # Extract travel time
    travel_time = data['routes'][0]['legs'][0]['duration']['text']
    print(f"Travel Time: {travel_time}")
    
    # Extract steps
    steps = data['routes'][0]['legs'][0]['steps']
    return travel_time, steps

def clean_html(text):
    """Remove HTML tags from text"""
    return re.sub('<.*?>', ' ', text).replace('  ', ' ').strip()

def navigation_thread(destination_lat, destination_lon, stop_event):
    """Thread that handles navigation updates"""
    while not stop_event.is_set():
        try:
            current_lat, current_lon = get_current_location()
            travel_time, directions = get_directions(current_lat, current_lon, destination_lat, destination_lon)
            
            # Queue travel time announcement
            speech_queue.put(f"Your travel time will be {travel_time}.")
            
            # Wait before giving directions
            time.sleep(3)
            
            # Only speak the first direction
            if directions:
                instruction = clean_html(directions[0]['html_instructions'])
                distance = directions[0].get('distance', {}).get('text', 'Unknown distance')
                speech_queue.put(f"{instruction}. You will need to travel {distance}.")
            
            # Wait a minute before the next update
            time.sleep(60)
            
        except Exception as e:
            print(f"Error in navigation: {e}")
            speech_queue.put("I encountered an error getting directions.")
            time.sleep(10)

def main():
    # Start the speech thread first
    speech_thread_handle = threading.Thread(target=speech_thread, daemon=True)
    speech_thread_handle.start()
    
    print("GPS Navigation System")
    print("---------------------")
    
    destination_name = input("Enter destination name: ")
    
    try:
        # Announce that we're searching
        speech_queue.put(f"Searching for {destination_name}.")
        
        destination_lat, destination_lon = get_destination_coordinates(destination_name)
        
        # Announce that destination was found
        speech_queue.put(f"Destination found. Starting navigation to {destination_name}.")
        
        stop_event = threading.Event()
        
        # Start the navigation thread
        nav_thread = threading.Thread(
            target=navigation_thread,
            args=(destination_lat, destination_lon, stop_event),
            daemon=True
        )
        nav_thread.start()
        
        print("Navigation started. Enter 'stop' to end navigation.")
        
        # Main loop for user input
        while True:
            user_input = input("> ")
            if user_input.lower() == 'stop':
                stop_event.set()
                speech_queue.put("Navigation stopped.")
                time.sleep(2)  # Give time for the last message to be spoken
                speech_queue.put("STOP")
                print("Navigation stopped.")
                break
    
    except Exception as e:
        print(f"Error: {e}")
        speech_queue.put("An error occurred. Please try again.")
        time.sleep(2)  # Give time for the error message to be spoken
        speech_queue.put("STOP")
    
    # Wait for speech thread to finish
    speech_thread_handle.join(timeout=5)
    print("Application closed.")

if __name__ == "__main__":
    main()
    '''
    ELEVENLABS_API_KEY = ""
    
    VOICE_ID = "pNInz6obpgDQGcFmaJgB"
    OUTPUT_FORMAT = "mp3_22050_32"
    MODEL_ID = "eleven_turbo_v2"
    
    DESTINATION = "San Francisco"
    
    speech_buffer = []
    speech_lock = threading.Lock()
    
    #nav_stop_event = start_navigation(speech_buffer, GOOGLE_API_KEY, ELEVENLABS_API_KEY, VOICE_ID, MODEL_ID, OUTPUT_FORMAT, DESTINATION, speech_lock)

    try:
        while True:
            time.sleep(1)  # Keep the program running until interrupted
            
    except KeyboardInterrupt:
        #nav_stop_event.set()
        print("Navigation stopped.")'''
