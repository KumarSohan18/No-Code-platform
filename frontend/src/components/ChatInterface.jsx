import React, { useState, useEffect } from 'react'
import ApiService from '../services/api'
import './ChatInterface.css'

function ChatInterface({ workflowId, onClose }) {
  const [sessionId, setSessionId] = useState(null)
  const [messages, setMessages] = useState([])
  const [inputMessage, setInputMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    console.log('ChatInterface mounted with workflowId:', workflowId);
    if (workflowId) {
      createChatSession()
    }
  }, [workflowId])

  const createChatSession = async () => {
    try {
      setLoading(true)
      console.log('Creating chat session for workflowId:', workflowId)
      const session = await ApiService.createChatSession(workflowId)
      console.log('Chat session created:', session)
      setSessionId(session.session_id)
      setError(null)
    } catch (error) {
      console.error('Failed to create chat session:', error)
      setError('Failed to create chat session: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  const sendMessage = async () => {
    if (!sessionId || !inputMessage.trim() || loading) return

    const messageContent = inputMessage.trim()
    const userMessage = {
      type: 'user',
      content: messageContent,
      timestamp: new Date().toISOString()
    }

    setMessages(prev => [...prev, userMessage])
    setInputMessage('')
    setLoading(true)

    try {
      console.log('Sending message:', messageContent, 'to session:', sessionId)
      const response = await ApiService.sendMessage(sessionId, messageContent)
      console.log('Message response:', response)
      
      const aiMessage = {
        type: 'ai',
        content: response.message,
        timestamp: new Date().toISOString(),
        executionLog: response.execution_log,
        processingTime: response.processing_time
      }

      setMessages(prev => [...prev, aiMessage])
      setError(null)
    } catch (error) {
      console.error('Failed to send message:', error)
      setError('Failed to send message: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  if (loading && !sessionId) {
    return (
      <div className="chat-interface">
        <div className="chat-header">
          <h3>Chat Interface</h3>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>
        <div className="chat-loading">
          <p>Creating chat session...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="chat-interface">
      <div className="chat-header">
        <h3>Chat Interface</h3>
        <button className="close-btn" onClick={onClose}>×</button>
      </div>

      {error && (
        <div className="chat-error">
          <p>{error}</p>
          <button onClick={createChatSession}>Retry</button>
        </div>
      )}

      <div className="chat-messages">
        {messages.length === 0 ? (
          <div className="chat-empty">
            <p>Start a conversation with your AI workflow!</p>
          </div>
        ) : (
          messages.map((message, index) => (
            <div key={index} className={`message ${message.type}`}>
              <div className="message-content">
                {message.content}
              </div>
              <div className="message-meta">
                <span className="message-time">
                  {new Date(message.timestamp).toLocaleTimeString()}
                </span>
                {message.processingTime && (
                  <span className="processing-time">
                    ({message.processingTime}ms)
                  </span>
                )}
              </div>
              {message.executionLog && (
                <details className="execution-log">
                  <summary>Execution Log</summary>
                  <pre>{JSON.stringify(message.executionLog, null, 2)}</pre>
                </details>
              )}
            </div>
          ))
        )}
        {loading && (
          <div className="message ai">
            <div className="message-content">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="chat-input">
        <textarea
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Type your message..."
          disabled={loading}
          rows={2}
        />
        <button 
          onClick={() => {
            console.log('Send button clicked!', { inputMessage, sessionId, loading });
            sendMessage();
          }} 
          disabled={!inputMessage.trim() || loading}
          className="send-btn"
          style={{
            backgroundColor: (!inputMessage.trim() || loading) ? '#ccc' : '#3b82f6',
            cursor: (!inputMessage.trim() || loading) ? 'not-allowed' : 'pointer'
          }}
        >
          {loading ? 'Sending...' : 'Send'}
        </button>
      </div>
      
      {/* Debug info */}
      <div style={{ fontSize: '12px', color: '#666', padding: '10px' }}>
        Debug: sessionId={sessionId ? 'exists' : 'null'}, inputMessage='{inputMessage}', loading={loading.toString()}
      </div>
    </div>
  )
}

export default ChatInterface
