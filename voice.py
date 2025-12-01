"""
CogniVera Voice Module
======================

This module handles speech recognition and text-to-speech synthesis.
Integrates OpenAI Whisper for ASR and TTS for vocal interaction.

Reference: https://doi.org/10.1109/ACCESS.2025.3565918
"""

import os
import logging
import time
from datetime import datetime
from typing import Optional

import speech_recognition as sr
import soundfile as sf
import sounddevice as sd
import openai

# Configure logging
logger = logging.getLogger(__name__)


class VoiceHandler:
    """
    Handles voice input/output for human-robot interaction.

    Provides speech-to-text (via Whisper) and text-to-speech (via OpenAI TTS)
    capabilities for conversational robot interface.

    Attributes:
        recognizer: SpeechRecognition recognizer instance
        dev_mode (bool): Development mode (skip greeting)
        greeting_active (bool): Enable greeting message
    """

    def __init__(
            self,
            api_key: Optional[str] = None,
            dev_mode: bool = False,
            greeting_active: bool = True
    ):
        """
        Initialize voice handler.

        Args:
            api_key (str, optional): OpenAI API key
            dev_mode (bool): Enable development mode (skip greeting). Default: False
            greeting_active (bool): Enable greeting message. Default: True
        """
        # Set API key
        if api_key is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")

        openai.api_key = api_key

        # Initialize speech recognizer
        self.recognizer = sr.Recognizer()
        self.recognizer.pause_threshold = 1.0

        # Voice settings
        self.dev_mode = dev_mode
        self.greeting_active = greeting_active
        self.greeting_shown = False  # Track if greeting was shown

        # Audio files
        self.audio_input_file = "audio_input.wav"
        self.audio_output_file = "audio_output.opus"

        logger.info("VoiceHandler initialized successfully")

    def speech_to_text(self) -> str:
        """
        Capture microphone input and convert to text using Whisper.

        Shows greeting message on first call if greeting_active=True.

        Returns:
            str: Recognized text or "NULL" if recognition failed
        """
        # Show greeting on first call
        if not self.greeting_shown and self.greeting_active:
            self._show_greeting()
            self.greeting_shown = True

        try:
            with sr.Microphone() as source:
                logger.info("Listening for input...")
                print("🎤 Listening...")

                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=30)

            # Save audio to file
            with open(self.audio_input_file, "wb") as f:
                f.write(audio.get_wav_data())

            # Transcribe with Whisper
            logger.info("Transcribing audio...")
            with open(self.audio_input_file, 'rb') as audio_file:
                transcript = openai.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="en"
                )

            text = transcript.text
            logger.info(f"Transcribed: {text}")
            return text

        except sr.UnknownValueError:
            logger.warning("Could not understand audio")
            return "NULL"
        except sr.RequestError as e:
            logger.error(f"Speech recognition error: {str(e)}")
            return "NULL"
        except Exception as e:
            logger.error(f"Error in speech_to_text: {str(e)}")
            return "NULL"

    def text_to_speech(self, text: str, voice: str = "nova") -> None:
        """
        Convert text to speech and play audio.

        Args:
            text (str): Text to synthesize
            voice (str): Voice name (nova, alloy, echo, fable, onyx, shimmer)
        """
        try:
            if not text:
                logger.warning("Empty text provided to TTS")
                return

            logger.info(f"Generating speech: {text[:50]}...")

            # Generate speech
            response = openai.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text,
            )

            # Save to file
            response.stream_to_file(self.audio_output_file)

            # Play audio
            self._play_audio(self.audio_output_file)

        except Exception as e:
            logger.error(f"Error in text_to_speech: {str(e)}")

    def _show_greeting(self) -> None:
        """Display greeting message based on current hour."""
        hour = datetime.now().hour

        if 0 <= hour < 12:
            greeting = "Good Morning!"
        elif 12 <= hour < 18:
            greeting = "Good Afternoon!"
        else:
            greeting = "Good Evening!"

        if self.dev_mode:
            message = "Hello"
        else:
            message = (
                f"Hello! {greeting} "
                "I am PRODIGI, the conversational cobot from FAST-LAB at Thammasat University. "
                "How can I help you today?"
            )

        self.text_to_speech(message)

    def _play_audio(self, file_path: str) -> None:
        """
        Play audio file using sounddevice.

        Args:
            file_path (str): Path to audio file
        """
        try:
            if not os.path.exists(file_path):
                logger.error(f"Audio file not found: {file_path}")
                return

            # Read audio file
            data, samplerate = sf.read(file_path)

            # Play audio
            logger.debug(f"Playing audio: {file_path}")
            sd.play(data, samplerate)
            sd.wait()

        except Exception as e:
            logger.error(f"Error playing audio: {str(e)}")

    def disable_greeting(self) -> None:
        """Disable greeting message."""
        self.greeting_active = False

    def enable_greeting(self) -> None:
        """Enable greeting message."""
        self.greeting_active = True


# Legacy alias for backward compatibility
Voice = VoiceHandler