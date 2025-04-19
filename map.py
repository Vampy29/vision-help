import pyttsx3
import requests
import threading
import time
import geocoder
from queue import Queue
from geopy.geocoders import Nominatim
import re
import speech_recognition as sr

# Global speech queue
speech_queue = Queue()
recognizer = sr.Recognizer()
def get_voice_input():
    """Get voice input from the user"""
    with sr.Microphone() as source:
        print("Listening for destination...")
        audio = recognizer.listen(source)
        time.sleep(5)
        try:
            text = recognizer.recognize_google(audio)
            print(f"You said: {text}")
            return text
        except sr.UnknownValueError:
            print("Sorry, I didn't understand that.")
            return None
        except sr.RequestError:
            print("Sorry, there was an error with the speech recognition service.")
            return None
        
def speech_thread():
    """Thread to handle all text-to-speech operations"""
    speech_buffer = []  # Array to store messages temporarily
    
    while True:
        try:
            # Check for new messages in the queue
            while not speech_queue.empty():
                text = speech_queue.get()
                if text == "STOP":
                    return
                speech_buffer.append(text)
            
            # Process messages in the buffer
            if speech_buffer:
                combined_text = " ".join(speech_buffer)
                print(f"Speaking: {combined_text}")  # Debug print
                
                # Create a new engine instance for each speech operation
                engine = pyttsx3.init()
                engine.setProperty('rate', 200)
                engine.setProperty('volume', 0.9)
                
                engine.say(combined_text)
                engine.runAndWait()
                
                # Clean up the engine
                del engine
                
                speech_buffer.clear()  # Clear buffer after speaking
            
            time.sleep(15)  # Wait before checking the queue again
            
        except Exception as e:
            print(f"Speech error: {e}")
            # No need to reset - we'll create a new instance next time
            time.sleep(1)  # Brief pause after an error



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
                print(1, instruction)
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
    
    #speech_queue.put("Please say your destination.")
    destination_name = None
    while destination_name is None:
        destination_name = get_voice_input()
        time.sleep(10)
        if destination_name is None:
            speech_queue.put("I didn't catch that. Please try again.")
    
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
        
        print("Navigation started. Say 'stop' to end navigation.")
        
        # Main loop for user input
        while True:
            user_input = get_voice_input()
            if user_input and user_input.lower() == 'stop':
                stop_event.set()
                speech_queue.put("Navigation stopped.")
                time.sleep(20)  # Give time for the last message to be spoken
                speech_queue.put("STOP")
                print("Navigation stopped.")
                break
    
    except Exception as e:
        print(f"Error: {e}")
        speech_queue.put("An error occurred. Please try again.")
        time.sleep(20)  # Give time for the error message to be spoken
        speech_queue.put("STOP")
    
    # Wait for speech thread to finish
    speech_thread_handle.join(timeout=5)
    print("Application closed.")

if __name__ == "__main__":
    main()