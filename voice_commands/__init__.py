"""
Voice command processing for automotive risk assessment.

This package provides voice recognition and processing functionality
to enable hands-free control of the risk assessment application.
"""

from .voice_processor import VoiceProcessor, process_voice_command

__all__ = [
    'VoiceProcessor',
    'process_voice_command'
] 