# Speech-to-Text and Gemini API Interaction

This project combines speech recognition and text-to-speech functionality with the Gemini API to create a conversational interface. The application listens to user input via a microphone, processes it into text, sends the text to the Gemini API, and then speaks the response back to the user.

## Features

- **Speech Recognition:** Converts spoken words into text using the `speech_recognition` library.
- **Text-to-Speech:** Converts Gemini API responses into spoken words using `pyttsx3`.
- **Gemini API Integration:** Sends user input to the Gemini API and retrieves a generative AI response.

## Prerequisites

- Python 3.6 or higher
- A working microphone for audio input
- An API key for the Gemini service
