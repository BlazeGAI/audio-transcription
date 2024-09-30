import streamlit as st
import zipfile
import os
import tempfile
from pydub import AudioSegment
import speech_recognition as sr

# Function to extract audio files and transcribe
def extract_and_transcribe(zip_file):
    r = sr.Recognizer()
    transcript_dict = {}

    # Create a temporary directory to extract the files
    with tempfile.TemporaryDirectory() as tmp_dir:
        with zipfile.ZipFile(zip_file, 'r') as z:
            z.extractall(tmp_dir)
        
        # Walk through the extracted files
        for root, dirs, files in os.walk(tmp_dir):
            for file in files:
                if file.endswith(('.wav', '.mp3', '.flac', '.m4a')):
                    file_path = os.path.join(root, file)
                    
                    # Handle .m4a and other formats using pydub and export as wav
                    if file.endswith('.m4a'):
                        audio = AudioSegment.from_file(file_path, format='m4a')
                    else:
                        audio = AudioSegment.from_file(file_path)

                    # Convert the audio to wav format for compatibility with SpeechRecognition
                    wav_audio_path = os.path.join(tmp_dir, file.split('.')[0] + '.wav')
                    audio.export(wav_audio_path, format='wav')
                    
                    # Use SpeechRecognition to transcribe the audio
                    with sr.AudioFile(wav_audio_path) as source:
                        audio_data = r.record(source)
                        try:
                            text = r.recognize_google(audio_data)
                            transcript_dict[file] = text
                        except sr.UnknownValueError:
                            transcript_dict[file] = "Transcription failed: Audio unclear."
                        except sr.RequestError:
                            transcript_dict[file] = "Transcription failed: API error."
    
    return transcript_dict

# Streamlit interface
st.title("Audio Transcription Application")
st.write("Upload a ZIP file containing audio files (.wav, .mp3, .flac, .m4a).")

uploaded_file = st.file_uploader("Choose a ZIP file", type="zip")

if uploaded_file is not None:
    st.write("Processing the uploaded file...")

    # Transcribe audio files from ZIP
    transcriptions = extract_and_transcribe(uploaded_file)
    
    # Display the transcriptions
    st.write("Transcription Results:")
    for file_name, transcription in transcriptions.items():
        st.write(f"**{file_name}**")
        st.write(transcription)

    # Save the transcription to a text file
    if st.button("Download Transcription"):
        transcription_file = "transcription.txt"
        with open(transcription_file, "w") as f:
            for file_name, transcription in transcriptions.items():
                f.write(f"File: {file_name}\n")
                f.write(f"{transcription}\n\n")

        with open(transcription_file, "rb") as f:
            st.download_button("Download Transcriptions", f, file_name="transcriptions.txt")
