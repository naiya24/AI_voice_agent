import os
import re
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from flask import Flask, request, jsonify
from google.auth.transport.requests import Request
from google.cloud import texttospeech, speech
from google.oauth2 import service_account
from httplib2 import Credentials
from twilio.rest import Client
import openai
import logging
import pickle
from datetime import datetime
import pytz

logging.basicConfig(level=logging.INFO)
os.environ["GRPC_VERBOSITY"] = "ERROR"

app = Flask(__name__)

openai.api_key = os.getenv('OPENAI_API_KEY')
twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID')
twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN')
twilio_phone_number = os.getenv('TWILIO_PHONE_NUMBER')
CLIENT_SECRET_FILE = os.getenv('CLIENT_SECRET_FILE', 'credentials.json')
SERVICE_ACCOUNT_FILE = os.getenv('SERVICE_ACCOUNT_FILE', 'service_account.json')
SCOPES = ['https://www.googleapis.com/auth/calendar']

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = SERVICE_ACCOUNT_FILE
text_to_speech_client = texttospeech.TextToSpeechClient()
speech_to_text_client = speech.SpeechClient()
twilio_client = Client(twilio_account_sid, twilio_auth_token)

# Load credentials from file if available, otherwise return None
def load_credentials():
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            return pickle.load(token)
    logging.warning("No credentials found. User needs to authenticate.")
    return None

# Save credentials to file for future use
def save_credentials(creds):
    with open('token.pickle', 'wb') as token:
        pickle.dump(creds, token)

# Authenticate Google account and manage token refresh if necessary
def authenticate_google_account():
    creds = load_credentials()
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        save_credentials(creds)
    return creds

conversation_history = []

# Convert voice (audio) to text using Google Speech-to-Text API
@app.route('/voice_to_text', methods=['POST'])
def voice_to_text():
    try:
        audio_file = request.files['audio']
        if not audio_file:
            return jsonify({'error': 'No audio file provided'}), 400

        audio_content = audio_file.read()
        recognition_audio = speech.RecognitionAudio(content=audio_content)

        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code="en-US",
        )

        response = speech_to_text_client.recognize(config=config, audio=recognition_audio)
        transcript = response.results[0].alternatives[0].transcript
        logging.info(f"Transcribed text: {transcript}")
        return jsonify({"text": transcript}), 200

    except Exception as e:
        logging.error(f"Error during voice-to-text conversion: {e}")
        return jsonify({'error': 'Failed to process the audio. Please try again.'}), 500

# Handle conversation with the receptionist AI model
@app.route('/chat_with_receptionist', methods=['POST'])
def chat_with_receptionist():
    try:
        user_message = request.get_json().get('message')
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400

        conversation_history.append({"role": "user", "content": user_message})
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=conversation_history,
            max_tokens=200
        )
        ai_response = response['choices'][0]['message']['content'].strip()
        conversation_history.append({"role": "assistant", "content": ai_response})

        audio_file = generate_audio(ai_response)
        return jsonify({'response': ai_response, 'audio_file': audio_file}), 200

    except Exception as e:
        logging.error(f"Error during AI conversation: {e}")
        return jsonify({'error': 'An error occurred during the conversation.'}), 500

# Generate audio file from text using Google Text-to-Speech API
def generate_audio(text):
    try:
        synthesis_input = texttospeech.SynthesisInput(text=text)
        voice = texttospeech.VoiceSelectionParams(language_code="en-US", name="en-US-Wavenet-D")
        audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)

        response = text_to_speech_client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config,
        )
        audio_file = "response.mp3"
        with open(audio_file, "wb") as out:
            out.write(response.audio_content)
        logging.info(f"Audio response saved as: {audio_file}")
        return audio_file
    except Exception as e:
        logging.error(f"Error generating audio: {e}")
        return None

# Convert appointment time to a specific timezone
def schedule_appointment_with_timezone(appointment_time, timezone="UTC"):
    timezone_obj = pytz.timezone(timezone)
    appointment_time_obj = datetime.fromisoformat(appointment_time).replace(tzinfo=pytz.UTC)
    localized_time = appointment_time_obj.astimezone(timezone_obj)
    return localized_time.isoformat()

# Schedule an appointment and save it to Google Calendar
@app.route('/schedule_appointment', methods=['POST'])
def schedule_appointment():
    try:
        data = request.get_json()
        patient_name = data.get('patient_name')
        patient_phone = data.get('patient_phone')
        appointment_time = data.get('appointment_time')

        if not patient_name or not patient_phone or not appointment_time:
            return jsonify({'error': 'Missing required fields'}), 400

        if not validate_phone_number(patient_phone):
            return jsonify({'error': 'Invalid phone number format. Use E.164 format.'}), 400

        creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        service = googleapiclient.discovery.build("calendar", "v3", credentials=creds)

        localized_time = schedule_appointment_with_timezone(appointment_time)

        event = {
            'summary': f"Appointment with {patient_name}",
            'start': {'dateTime': localized_time, 'timeZone': 'UTC'},
            'end': {'dateTime': localized_time, 'timeZone': 'UTC'},
        }
        event_result = service.events().insert(calendarId='primary', body=event).execute()
        send_sms_reminder(patient_phone, appointment_time)

        return jsonify({'message': 'Appointment scheduled successfully', 'event': event_result}), 200

    except Exception as e:
        logging.error(f"Error scheduling appointment: {e}")
        return jsonify({'error': 'Failed to schedule appointment.'}), 500

# Send SMS reminder using Twilio API
def send_sms_reminder(phone, appointment_time):
    try:
        message = twilio_client.messages.create(
            body=f"Your appointment is scheduled for {appointment_time}.",
            from_=twilio_phone_number,
            to=phone
        )
        return message.sid
    except Exception as e:
        logging.error(f"Failed to send SMS: {e}")
        raise

# Validate phone number format using regular expression
def validate_phone_number(phone):
    pattern = re.compile(r"^\+?[1-9]\d{1,14}$")
    return pattern.match(phone)

# Global error handler for unexpected exceptions
@app.errorhandler(Exception)
def handle_exception(e):
    logging.error(f"Error occurred: {str(e)}")
    return jsonify({'error': 'Something went wrong. Please contact support.'}), 500

if __name__ == '__main__':
    app.run(debug=True)
