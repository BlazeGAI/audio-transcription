import streamlit as st
import zipfile
import os
import tempfile
from pydub import AudioSegment
import speech_recognition as sr
import subprocess

def process_audio_file(file_path, r):
    try:
        file_format = file_path.split('.')[-1].lower()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_wav:
            temp_wav_path = temp_wav.name

        if file_format == 'm4a':
            # Use FFmpeg to convert m4a to wav
            subprocess.run(['ffmpeg', '-i', file_path, '-acodec', 'pcm_s16le', '-ar', '44100', temp_wav_path], check=True)
        else:
            audio = AudioSegment.from_file(file_path, format=file_format)
            audio.export(temp_wav_path, format='wav')

        with sr.AudioFile(temp_wav_path) as source:
            audio_data = r.record(source)
            try:
                text = r.recognize_google(audio_data)
                return text
            except sr.UnknownValueError:
                return "Transcription failed: Audio unclear."
            except sr.RequestError:
                return "Transcription failed: API error."
    except Exception as e:
        return f"Error processing file: {str(e)}"
    finally:
        if 'temp_wav_path' in locals():
            os.unlink(temp_wav_path)
def extract_and_transcribe(uploaded_file):
    r = sr.Recognizer()
    transcript_dict = {}

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_zip:
            temp_zip.write(uploaded_file.read())
            temp_zip_path = temp_zip.name

        with tempfile.TemporaryDirectory() as tmp_dir:
            with zipfile.ZipFile(temp_zip_path, 'r') as z:
                z.extractall(tmp_dir)
            
            for root, dirs, files in os.walk(tmp_dir):
                for file in files:
                    if file.lower().endswith(('.wav', '.mp3', '.flac', '.m4a')):
                        file_path = os.path.join(root, file)
                        transcript_dict[file] = process_audio_file(file_path, r)
        
        os.unlink(temp_zip_path)
    except zipfile.BadZipFile:
        # If it's not a zip file, try processing it as a single audio file
        transcript_dict[uploaded_file.name] = process_audio_file(temp_zip_path, r)
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
    
    return transcript_dict

# Streamlit interface
st.title("Audio Transcription Application")
st.write("Upload a ZIP file containing audio files or a single audio file (.wav, .mp3, .flac, .m4a).")
uploaded_file = st.file_uploader("Choose a file", type=["zip", "wav", "mp3", "flac", "m4a"])

if uploaded_file is not None:
    st.write("Processing the uploaded file...")
    transcriptions = extract_and_transcribe(uploaded_file)
    
    if transcriptions:
        st.write("Transcription Results:")
        for file_name, transcription in transcriptions.items():
            st.write(f"**{file_name}**")
            st.write(transcription)
        
        if st.button("Download Transcription"):
            transcription_text = "\n\n".join([f"File: {file_name}\n{transcription}" for file_name, transcription in transcriptions.items()])
            st.download_button("Download Transcriptions", transcription_text, file_name="transcriptions.txt")
    else:
        st.error("No transcriptions were generated. Please check your input file.")
