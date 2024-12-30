import speech_recognition as sr
import pyttsx3
import google.generativeai as genai

engine = pyttsx3.init()

# Converts text to speech and plays it.
def speak(text):
    engine.say(text)
    engine.runAndWait()

# Captures audio input from the microphone and converts it to text.
def get_audio():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            print("Processing...")
            text = recognizer.recognize_google(audio)
            print(f"You said: {text}")
            return text
        except sr.UnknownValueError:
            print("Sorry, I couldn't understand what you said.")
            speak("Sorry, I couldn't understand what you said.")
        except sr.RequestError as e:
            print(f"Error with speech recognition service: {e}")
            speak("There was an error with the speech recognition service.")
        return None

# Sends input text to the Gemini API and returns the response.
def call_gemini_api(input_text):
    try:
        genai.configure(api_key="AIzaSyDh4KmcNagXwFmLKLSfoAEy1lcYY9oADDE")
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(input_text)
        print(f"Gemini Response: {response.text}")
        return response.text
    except Exception as e:
        print(f"Error with Gemini API: {e}")
        return "Sorry, there was an error processing your request."

# Main function to handle continuous speech recognition and API interaction.
def main():
    while True:
        input_text = get_audio()
        if input_text:
            response = call_gemini_api(input_text)
            speak(response)

if __name__ == "__main__":
    print("Starting Gemini interaction...")
    main()
