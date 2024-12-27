# Receptionist AI Web Application

This is a Flask-based web application that integrates various APIs, including OpenAI's GPT-4, Google Cloud's Speech-to-Text, Google Calendar, and Twilio for SMS notifications. The app can transcribe audio to text, interact with users through a conversational AI model, and schedule appointments while sending SMS reminders.

## Features

- **Voice to Text**: Convert audio files to text using Google Cloud Speech-to-Text API.
- **Conversational AI**: Engage with a receptionist AI using OpenAI's GPT-4 for natural language interactions.
- **Appointment Scheduling**: Schedule appointments and add them to Google Calendar with the specified timezone.
- **SMS Reminders**: Send SMS reminders about scheduled appointments via Twilio API.

## Requirements

To run this project, ensure you have the following credentials and environment variables set up:

1. **OpenAI API Key**: Used to interact with the OpenAI GPT-4 model.
2. **Twilio API Key**: Required to send SMS notifications.
3. **Google Cloud Credentials**: Service account credentials for accessing Google APIs (including Google Calendar and Speech-to-Text).
4. **Client Secret for OAuth2 Authentication**: Credentials for Google OAuth2 to authenticate and manage Google Calendar events.

### Required Environment Variables

You must configure the following environment variables for the application to function:

- `OPENAI_API_KEY` - Your OpenAI API key for interacting with GPT-4.
- `TWILIO_ACCOUNT_SID` - Your Twilio account SID for SMS functionality.
- `TWILIO_AUTH_TOKEN` - Your Twilio auth token for authentication.
- `TWILIO_PHONE_NUMBER` - Your Twilio phone number.
- `CLIENT_SECRET_FILE` - Path to the Google OAuth2 client secret file (`credentials.json`).
- `SERVICE_ACCOUNT_FILE` - Path to the Google Cloud service account credentials file (`service_account.json`).
