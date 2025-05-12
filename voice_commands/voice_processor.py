import speech_recognition as sr
import pyttsx3
import time
from datetime import datetime
import threading
import re
import os
from typing import Tuple, List, Optional, Dict, Any

class VoiceProcessor:
    """Processes voice commands for the risk assessment application"""
    
    def __init__(self):
        # Initialize the recognizer
        self.recognizer = sr.Recognizer()
        
        # Initialize text-to-speech engine
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', 150)  # Speed of speech
            self.engine.setProperty('volume', 0.9)  # Volume (0.0 to 1.0)
            # Set Italian voice if available
            voices = self.engine.getProperty('voices')
            for voice in voices:
                if 'italian' in voice.name.lower():
                    self.engine.setProperty('voice', voice.id)
                    break
        except Exception as e:
            print(f"Error initializing text-to-speech engine: {e}")
            self.engine = None
        
        # Store command history
        self.command_history = []
        
        # Command mappings (Italian)
        self.command_patterns = {
            r'genera\s+valutazione\s+rischi': 'generate_risk_assessment',
            r'mostra\s+dashboard': 'show_dashboard',
            r'mostra\s+gestione\s+rischi': 'show_risk_management',
            r'mostra\s+configurazione\s+agenti': 'show_agent_configuration',
            r'mostra\s+comandi\s+vocale': 'show_voice_commands',
            r'filtra\s+per\s+livello\s+strategico': 'filter_strategic',
            r'filtra\s+per\s+livello\s+progetto': 'filter_project',
            r'filtra\s+per\s+livello\s+operativo': 'filter_operational',
            r'mostra\s+tutti\s+i\s+rischi': 'show_all_risks',
            r'salva\s+i\s+dati': 'save_data',
            r'salva\s+la\s+valutazione': 'save_data',
            r'salva\s+valutazione\s+rischi': 'save_data',
            r'mostra\s+rischi\s+principali': 'show_top_risks',
            r'aggiungi\s+.*\s+rischio': 'add_risk',
            r'modifica\s+.*\s+rischio': 'edit_risk',
        }
    
    def listen_for_command(self) -> Optional[str]:
        """
        Listen for a voice command through the microphone
        
        Returns:
            The recognized command as a string, or None if recognition fails
        """
        # Record the command history with timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        try:
            with sr.Microphone() as source:
                print("In ascolto...")
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                # Listen for audio input
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
                
                # Recognize speech using Google Speech Recognition with Italian language
                command = self.recognizer.recognize_google(audio, language='it-IT')
                print(f"Comando riconosciuto: {command}")
                
                # Save command to history
                self.command_history.append((command, timestamp))
                
                # Give audio feedback if text-to-speech is available
                if self.engine:
                    self.engine.say(f"Ho capito: {command}")
                    self.engine.runAndWait()
                
                return command
                
        except sr.WaitTimeoutError:
            print("Nessun comando vocale rilevato")
            return None
        except sr.UnknownValueError:
            print("Impossibile comprendere l'audio")
            return None
        except sr.RequestError as e:
            print(f"Errore nella richiesta: {e}")
            return None
        except Exception as e:
            print(f"Errore nel riconoscimento vocale: {e}")
            return None
    
    def process_command(self, command: str) -> Dict[str, Any]:
        """
        Process a voice command and return the action to take
        
        Args:
            command: The recognized voice command
            
        Returns:
            Dictionary with action details
        """
        command = command.lower().strip()
        result = {
            "success": False,
            "action": None,
            "parameters": {},
            "message": "Comando non riconosciuto"
        }
        
        # Match command against patterns
        for pattern, action in self.command_patterns.items():
            if re.search(pattern, command):
                result["success"] = True
                result["action"] = action
                result["message"] = f"Esecuzione comando: {action}"
                
                # Extract parameters if needed
                if action == 'filter_strategic':
                    result["parameters"] = {"level": "Strategic"}
                elif action == 'filter_project':
                    result["parameters"] = {"level": "Project"}
                elif action == 'filter_operational':
                    result["parameters"] = {"level": "Operational"}
                
                # Give audio feedback if text-to-speech is available
                if self.engine:
                    self.engine.say(result["message"])
                    self.engine.runAndWait()
                
                return result
        
        # If no pattern matched
        if self.engine:
            self.engine.say("Mi dispiace, non ho capito il comando")
            self.engine.runAndWait()
        
        return result
    
    def speak_text(self, text: str) -> None:
        """
        Speak the given text using text-to-speech
        
        Args:
            text: The text to speak
        """
        if self.engine:
            self.engine.say(text)
            self.engine.runAndWait()


# Wrapper function for voice command processing outside of class
def process_voice_command():
    """Process a single voice command and return the result"""
    processor = VoiceProcessor()
    command = processor.listen_for_command()
    if command:
        return processor.process_command(command)
    return {"success": False, "message": "Nessun comando rilevato"}


if __name__ == "__main__":
    # Test the voice processor
    processor = VoiceProcessor()
    print("Pronuncia un comando...")
    command = processor.listen_for_command()
    if command:
        result = processor.process_command(command)
        print(f"Risultato: {result}")
    else:
        print("Nessun comando rilevato") 