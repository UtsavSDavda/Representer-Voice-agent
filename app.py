import streamlit as st
import numpy as np
import sounddevice as sd
import soundfile as sf
import tempfile
import os
import requests
import threading
import queue
import time

class AudioRecorder:
    def __init__(self, sample_rate=16000, channels=1, block_duration=0.5):
        self.sample_rate = sample_rate
        self.channels = channels
        self.block_duration = block_duration
        self.recording_queue = queue.Queue()
        self.is_recording = False
        self.recording_thread = None
        self.max_recording_duration = 30  # Maximum recording duration in seconds

    def record_audio(self):
        """Continuous audio recording method"""
        try:
            with sd.InputStream(
                samplerate=self.sample_rate, 
                channels=self.channels,
                dtype='float32'
            ) as stream:
                while self.is_recording:
                    # Read audio block
                    audio_block, overflowed = stream.read(int(self.sample_rate * self.block_duration))
                    
                    if overflowed:
                        st.warning("Audio buffer overflow. Some data might be lost.")
                    
                    # Put block in queue
                    self.recording_queue.put(audio_block)
        except Exception as e:
            st.error(f"Recording error: {e}")
            self.is_recording = False

    def start_recording(self):
        """Start recording audio"""
        # Reset queue
        while not self.recording_queue.empty():
            self.recording_queue.get()
        
        # Set recording flag
        self.is_recording = True
        
        # Start recording thread
        self.recording_thread = threading.Thread(target=self.record_audio)
        self.recording_thread.start()

    def stop_recording(self):
        """Stop recording and save audio"""
        # Stop recording
        self.is_recording = False
        
        # Wait for recording thread to finish
        if self.recording_thread:
            self.recording_thread.join(timeout=2)
        
        # Collect all recorded blocks
        recorded_blocks = []
        while not self.recording_queue.empty():
            recorded_blocks.append(self.recording_queue.get())
        
        # Combine blocks
        if recorded_blocks:
            audio_data = np.concatenate(recorded_blocks, axis=0)
            
            # Create a temporary WAV file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav', mode='wb') as temp_file:
                sf.write(temp_file.name, audio_data, self.sample_rate)
                return temp_file.name
        
        return None

def main():
    st.title("Live Voice Query Agent")

    # Initialize audio recorder
    if 'recorder' not in st.session_state:
        st.session_state.recorder = AudioRecorder()
    
    # Initialize recording state
    if 'is_recording' not in st.session_state:
        st.session_state.is_recording = False

    # Recording UI
    col1, col2 = st.columns(2)
    
    with col1:
        # Start Recording Button
        if st.button("Start Recording"):
            try:
                st.session_state.recorder.start_recording()
                st.session_state.is_recording = True
                st.success("Recording started... Speak now!")
            except Exception as e:
                st.error(f"Failed to start recording: {e}")

    with col2:
        # Stop Recording Button
        if st.button("Stop Recording"):
            if st.session_state.is_recording:
                try:
                    # Stop recording and get audio file
                    audio_file_path = st.session_state.recorder.stop_recording()
                    st.session_state.is_recording = False
                    
                    if audio_file_path:
                        # Process the recorded audio
                        try:
                            # Send to FastAPI backend
                            with open(audio_file_path, 'rb') as f:
                                files = {'file': f}
                                response = requests.post(
                                    "http://localhost:8000/process-audio/", 
                                    files=files
                                )
                            
                            if response.status_code == 200:
                                output_audio_path = "response.mp3"
                                with open(output_audio_path, "wb") as f:
                                    f.write(response.content)
                                
                                st.success("✅ Audio Processed! Click below to listen.")
                                st.audio(output_audio_path, format="audio/mp3")
                            
                            else:
                                st.error(f"Error processing audio: {response.text}")
                        
                        except requests.RequestException as e:
                            st.error(f"Network error: {e}")
                        except Exception as e:
                            st.error(f"Processing error: {e}")
                        
                        finally:
                            # Clean up temporary audio file
                            if os.path.exists(audio_file_path):
                                os.unlink(audio_file_path)
                    else:
                        st.warning("No audio recorded.")
                except Exception as e:
                    st.error(f"Recording stop error: {e}")
            else:
                st.warning("No active recording to stop.")

    if st.session_state.is_recording:
        st.warning("🔴 Recording in progress...")

    with st.expander("System Information"):
        st.write("Audio Input Devices:", sd.query_devices())
        st.write("Default Input Device:", sd.default.device[0])

if __name__ == "__main__":
    main()