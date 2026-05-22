// frontend/src/hooks/useVoiceAssistant.js
import { useState, useEffect } from 'react';

export const useVoiceAssistant = (onSpeechResult) => {
  const [isListening, setIsListening] = useState(false);
  const [recognition, setRecognition] = useState(null);

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recog = new SpeechRecognition();
      recog.continuous = false;
      recog.interimResults = false;
      recog.lang = 'en-US';

      recog.onresult = (event) => {
        const text = event.results[0][0].transcript;
        if (onSpeechResult) onSpeechResult(text);
        setIsListening(false);
      };

      recog.onerror = () => {
        setIsListening(false);
      };

      recog.onend = () => {
        setIsListening(false);
      };

      setRecognition(recog);
    }
  }, [onSpeechResult]);

  const startListening = () => {
    if (recognition) {
      setIsListening(true);
      recognition.start();
    } else {
      alert("Speech recognition is not supported in this browser.");
    }
  };

  const stopListening = () => {
    if (recognition) {
      recognition.stop();
      setIsListening(false);
    }
  };

  const speak = (text) => {
    if ('speechSynthesis' in window) {
      // Cancel previous utterances to avoid queuing delays
      window.speechSynthesis.cancel();
      const utterance = new SynthesisUtterance(text);
      utterance.rate = 1.0;
      utterance.pitch = 1.0;
      window.speechSynthesis.speak(utterance);
    }
  };

  return { isListening, startListening, stopListening, speak };
};

// Handle standard or webkit synthesis
const SynthesisUtterance = window.SpeechSynthesisUtterance || window.webkitSpeechSynthesisUtterance || SpeechSynthesisUtterance;
