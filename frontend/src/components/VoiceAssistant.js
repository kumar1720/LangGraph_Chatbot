// frontend/src/components/VoiceAssistant.js
import React, { useState, useEffect, useRef } from 'react';
import { Box, Paper, IconButton, Button, Typography } from '@mui/material';
import MicIcon from '@mui/icons-material/Mic';
import MicOffIcon from '@mui/icons-material/MicOff';
import CallEndIcon from '@mui/icons-material/CallEnd';
import VolumeUpIcon from '@mui/icons-material/VolumeUp';
import VolumeOffIcon from '@mui/icons-material/VolumeOff';
import CloseIcon from '@mui/icons-material/Close';
import { useNavigate } from 'react-router-dom';

import { useVoiceAssistant } from '../hooks/useVoiceAssistant';
import streamingService from '../services/streamingService';

const VoiceAssistant = () => {
  const navigate = useNavigate();
  const [messages, setMessages] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const [currentResponse, setCurrentResponse] = useState('');
  const [chatId, setChatId] = useState('');
  const [isSpeakingState, setIsSpeakingState] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  
  const messagesEndRef = useRef(null);

  useEffect(() => {
    setChatId(`voice_chat_${Date.now()}`);
  }, []);

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, currentResponse]);

  // Handle final speech results from standard browser speech-to-text
  const handleSpeechResult = async (text) => {
    if (!text.trim()) return;

    // Add user message
    const userMsg = {
      id: `user-${Date.now()}`,
      text: text,
      isUser: true,
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, userMsg]);

    // Query standard API
    let responseText = '';
    setCurrentResponse('');
    
    try {
      streamingService.startStream(text, chatId, {
        onChunk: (chunk) => {
          responseText += chunk;
          setCurrentResponse(responseText);
        },
        onComplete: () => {
          // Add assistant message
          const assistantMsg = {
            id: `assistant-${Date.now()}`,
            text: responseText,
            isUser: false,
            timestamp: new Date().toISOString()
          };
          setMessages(prev => [...prev, assistantMsg]);
          setCurrentResponse('');

          // Speech synthesis to vocalize response
          if (!isMuted) {
            setIsSpeakingState(true);
            speak(responseText);
          }
        },
        onError: (err) => {
          console.error("Voice completion error: ", err);
          const errorMsg = {
            id: `error-${Date.now()}`,
            text: "Failed to get a response from assistant. Please try again.",
            isSystem: true,
            isError: true,
            timestamp: new Date().toISOString()
          };
          setMessages(prev => [...prev, errorMsg]);
        }
      });
    } catch (e) {
      console.error(e);
    }
  };

  const { isListening, startListening, stopListening, speak } = useVoiceAssistant(handleSpeechResult);

  const handleStartCall = () => {
    setIsConnected(true);
    setMessages([
      {
        id: `system-${Date.now()}`,
        text: 'Voice assistant connected. Click the mic and start talking!',
        isSystem: true,
        timestamp: new Date().toISOString()
      }
    ]);
  };

  const handleDisconnect = () => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    stopListening();
    setIsConnected(false);
    setIsSpeakingState(false);
    setMessages([]);
  };

  const handleClose = () => {
    handleDisconnect();
    navigate('/chat');
  };

  const toggleListen = () => {
    if (isListening) {
      stopListening();
    } else {
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
      setIsSpeakingState(false);
      startListening();
    }
  };

  useEffect(() => {
    // Monitor voice speaking changes
    const timer = setInterval(() => {
      if ('speechSynthesis' in window) {
        setIsSpeakingState(window.speechSynthesis.speaking);
      }
    }, 500);
    return () => clearInterval(timer);
  }, []);

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const renderMessage = (message) => {
    if (message.isSystem) {
      return (
        <Box 
          key={message.id} 
          sx={{ 
            textAlign: 'center', 
            py: 1.5, 
            my: 2,
            borderTop: '1px dashed rgba(0, 0, 0, 0.1)',
            borderBottom: '1px dashed rgba(0, 0, 0, 0.1)'
          }}
        >
          <Box component="div" sx={{ 
            fontStyle: 'italic',
            typography: 'caption',
            color: message.isError ? 'error.main' : 'text.secondary'
          }}>
            {message.text}
          </Box>
        </Box>
      );
    }

    return (
      <Box 
        key={message.id} 
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: message.isUser ? 'flex-end' : 'flex-start',
          mb: 2.5,
          maxWidth: '85%',
          alignSelf: message.isUser ? 'flex-end' : 'flex-start',
        }}
      >
        <Box sx={{ 
          display: 'flex', 
          alignItems: 'center', 
          mb: 0.5,
          ml: message.isUser ? 0 : 1,
          mr: message.isUser ? 1 : 0
        }}>
          <Typography variant="caption" sx={{ fontWeight: 'medium', color: 'text.secondary' }}>
            {message.isUser ? 'You' : 'Assistant'}
          </Typography>
          <Typography variant="caption" sx={{ ml: 1, opacity: 0.8, color: 'text.secondary' }}>
            {formatTime(message.timestamp)}
          </Typography>
        </Box>
        <Paper 
          elevation={message.isUser ? 1 : 2} 
          sx={{
            p: 2,
            width: 'fit-content',
            maxWidth: '100%',
            bgcolor: message.isUser ? 'grey.100' : 'primary.light',
            color: message.isUser ? 'text.primary' : 'primary.contrastText',
            borderRadius: message.isUser ? '16px 16px 4px 16px' : '16px 16px 16px 4px',
            lineHeight: 1.5
          }}
        >
          <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
            {message.text}
          </Typography>
        </Paper>
      </Box>
    );
  };

  return (
    <Paper 
      elevation={3} 
      sx={{ 
        width: '100%', 
        maxWidth: 700, 
        mx: 'auto', 
        height: '70vh', 
        display: 'flex', 
        flexDirection: 'column',
        overflow: 'hidden',
        borderRadius: 2
      }}
    >
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h5">Voice Assistant</Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {isConnected && (
            <IconButton onClick={() => setIsMuted(!isMuted)}>
              {isMuted ? <VolumeOffIcon color="error" /> : <VolumeUpIcon color="primary" />}
            </IconButton>
          )}
          <IconButton onClick={handleClose} sx={{ color: 'text.secondary', '&:hover': { color: 'text.primary' } }}>
            <CloseIcon />
          </IconButton>
        </Box>
      </Box>
      
      {isConnected ? (
        <>
          <Box sx={{ 
            flexGrow: 1, 
            overflowY: 'auto', 
            mb: 2, 
            p: 2,
            display: 'flex',
            flexDirection: 'column'
          }}>
            {messages.length === 1 && !currentResponse && (
              <Box sx={{ 
                p: 4, 
                display: 'flex', 
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                flexGrow: 1
              }}>
                <MicIcon sx={{ fontSize: 48, color: 'primary.main', opacity: 0.6, mb: 2 }} />
                <Typography variant="body1" sx={{ fontWeight: 'medium', mb: 1, textAlign: 'center' }}>
                  Voice Assistant Active
                </Typography>
                <Typography variant="body2" sx={{ textAlign: 'center', color: 'text.secondary' }}>
                  Click the microphone button below and start speaking.
                </Typography>
              </Box>
            )}
            
            {messages.length > 0 && (
              <Box sx={{ width: '100%' }}>
                {messages.map(renderMessage)}
              </Box>
            )}

            {currentResponse && (
              <Box 
                sx={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'flex-start',
                  mb: 2.5,
                  maxWidth: '85%',
                  alignSelf: 'flex-start',
                }}
              >
                <Typography variant="caption" sx={{ fontWeight: 'medium', color: 'text.secondary', mb: 0.5, ml: 1 }}>
                  Assistant (Speaking...)
                </Typography>
                <Paper 
                  elevation={2} 
                  sx={{
                    p: 2,
                    bgcolor: 'primary.light',
                    color: 'primary.contrastText',
                    borderRadius: '16px 16px 16px 4px',
                    lineHeight: 1.5
                  }}
                >
                  <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                    {currentResponse}...
                  </Typography>
                </Paper>
              </Box>
            )}

            <div ref={messagesEndRef} />
          </Box>
          
          <Box sx={{ 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center', 
            borderTop: 1,
            borderColor: 'divider',
            pt: 3,
            pb: 2,
            gap: 3
          }}>
            <IconButton 
              color={isListening ? "secondary" : "primary"}
              onClick={toggleListen}
              size="large"
              sx={{ 
                p: 3, 
                border: 2, 
                borderColor: isListening ? 'secondary.main' : 'primary.main',
                boxShadow: isListening ? '0 0 15px rgba(156, 39, 176, 0.5)' : 'none',
                transition: 'all 0.3s ease',
                '&:hover': {
                  transform: 'scale(1.05)'
                }
              }}
            >
              {isListening ? <MicIcon /> : <MicOffIcon />}
            </IconButton>
            
            <Button 
              variant="contained" 
              color="primary" 
              startIcon={<CallEndIcon />}
              onClick={handleDisconnect}
              sx={{
                px: 4,
                py: 1.2,
                borderRadius: 28,
                backgroundColor: '#5C6BC0',
                '&:hover': {
                  backgroundColor: '#3F51B5',
                  transform: 'translateY(-2px)'
                },
                transition: 'all 0.2s ease'
              }}
            >
              End Call
            </Button>
          </Box>
          {isSpeakingState && (
            <Typography variant="caption" color="primary" align="center" sx={{ display: 'block', pb: 1 }}>
              🔊 Speaking response...
            </Typography>
          )}
          {isListening && (
            <Typography variant="caption" color="secondary" align="center" sx={{ display: 'block', pb: 1 }}>
              🎙️ Listening to you...
            </Typography>
          )}
        </>
      ) : (
        <Box sx={{ 
          display: 'flex', 
          flexDirection: 'column', 
          alignItems: 'center', 
          justifyContent: 'center',
          flexGrow: 1,
          gap: 3 
        }}>
          <MicIcon sx={{ fontSize: 64, color: 'primary.main', opacity: 0.8 }} />
          <Typography variant="h6">100% Free Browser Voice Assistant</Typography>
          <Typography variant="body1" sx={{ color: 'text.secondary', maxWidth: '80%', textAlign: 'center' }}>
            Offloads 100% of the speech-to-text and voice generation to your local browser using the Web Speech API. Completely secure and free.
          </Typography>
          <Button 
            variant="contained" 
            color="primary" 
            size="large"
            onClick={handleStartCall}
            sx={{ 
              py: 1.5, 
              px: 4, 
              borderRadius: 28,
              boxShadow: 3,
              '&:hover': {
                transform: 'translateY(-2px)'
              },
              transition: 'all 0.3s ease'
            }}
            startIcon={<MicIcon />}
          >
            Start Voice Assistant
          </Button>
        </Box>
      )}
    </Paper>
  );
};

export default VoiceAssistant;
