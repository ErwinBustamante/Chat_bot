import React, { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import saraAvatar from '../img/sara-avatar.jpg'; 
import documentoPreviewImage from '../img/image.png'; 
import "../css/Chat_bot.css";
import "../css/Carga.css";
import Registro from './Registro';

const Chat = () => {
  const [messages, setMessages] = useState([
    {
      text: "¡Hola! Soy Sara, asesora de la Universidad Bolivariana del Ecuador. ¿En qué puedo ayudarte hoy?",
      sender: "bot",
      timestamp: new Date()
    }
  ]);
  const [inputText, setInputText] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [showRegistro, setShowRegistro] = useState(false);
  const messagesEndRef = useRef(null);

  const primaryColor = "#d32f2f";

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const toggleRegistro = () => {
    setShowRegistro(!showRegistro);
  };

  const sendMessage = async () => {
    if (!inputText.trim()) return;

    const userMessage = { 
      text: inputText, 
      sender: "user", 
      timestamp: new Date() 
    };
    setMessages(prev => [...prev, userMessage]);
    setInputText("");
    setIsTyping(true);

    try {
      const response = await fetch("http://localhost:5000/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: inputText }),
      });

      if (!response.ok) throw new Error(`Error: ${response.status}`);

      const data = await response.json();
      console.log("Respuesta completa del backend:", data);
      
      const newBotMessage = { 
        text: data.response, 
        sender: "bot", 
        timestamp: new Date(),
        documentos: data.documentos
      };
      
      setMessages(prev => [...prev, newBotMessage]);

      // Solo sugerir registro si no hay documentos adjuntos
   
        setTimeout(() => {
          setMessages(prev => [...prev, {
            text: "¿Deseas registrarte ahora? [Registro ✍️](#registro)",
            sender: "bot",
            timestamp: new Date()
          }]);
        }, 1000);
      

    } catch (error) {
      console.error("Error al enviar el mensaje:", error);
      setMessages(prev => [...prev, {
        text: "Lo siento, hubo un error al procesar tu mensaje. Por favor intenta nuevamente.",
        sender: "bot",
        timestamp: new Date()
      }]);
    } finally {
      setIsTyping(false);
    }
  };

  const CustomLink = ({ children, href }) => {
    if (href === "#registro") {
      return (
        <button 
          className="register-button"
          onClick={toggleRegistro}
          style={{
            background: 'none',
            border: 'none',
            color: primaryColor,
            textDecoration: 'underline',
            cursor: 'pointer',
            padding: 0,
            font: 'inherit',
            display: 'inline'
          }}
        >
          {children}
        </button>
      );
    }
    return <a href={href} target="_blank" rel="noopener noreferrer">{children}</a>;
  };

  const CustomTable = ({ children }) => {
    return (
      <div className="table-container" style={{ width: '100%', overflowX: 'auto' }}>
        {children}
      </div>
    );
  };

  const formatTime = (date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const renderDocumentos = (documentos) => {
    return (
      <div className="documentos-carrera">
        <h4>Documentos relacionados:</h4>
        <div className="documentos-grid">
          {documentos.map((doc, idx) => (
            <div key={idx} className="documento-preview">
              <a 
                href={`http://localhost:5000/documentos/${doc.id}`}
                target="_blank"
                rel="noopener noreferrer"
                className="documento-link"
              >
                <div className="documento-image-container">
                  <img 
                    src={documentoPreviewImage} 
                    alt={`Preview de ${doc.nombre}`}
                    className="documento-thumbnail"
                  />
                  <div className="documento-hover-overlay">
                    <span className="eye-icon">👁️</span>
                  </div>
                </div>
                <span className="documento-nombre">{doc.nombre}</span>
              </a>
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="chat-app-container">
      <div className="top-navbar">
        <a 
          href="https://www.ube.edu.ec/" 
          target="_blank" 
          rel="noopener noreferrer" 
          className="nav-link"
        >
          LA UBE
        </a>
        <a 
          href="https://ube.edu.ec/Oferta_academica" 
          target="_blank" 
          rel="noopener noreferrer" 
          className="nav-link"
        >
          EDUCACIÓN
        </a>
        <a 
          href="https://investigacion.ube.edu.ec/" 
          target="_blank" 
          rel="noopener noreferrer" 
          className="nav-link"
        >
          INVESTIGACIÓN
        </a>
        <a 
          href="https://ube.edu.ec/Vinculacion" 
          target="_blank" 
          rel="noopener noreferrer" 
          className="nav-link"
        >
          VINCULACIÓN
        </a>
        <a 
          href="https://crai.ube.edu.ec/" 
          target="_blank" 
          rel="noopener noreferrer" 
          className="nav-link"
        >
          CRAI
        </a>
        <a 
          href="https://ube.edu.ec/Admisiones" 
          target="_blank" 
          rel="noopener noreferrer" 
          className="nav-link"
        >
          ADMISIONES
        </a>
      </div>
      
      <div className="chat-area">
        {showRegistro && (
          <div className="modal-overlay">
            <div className="modal-content">
              <Registro onClose={toggleRegistro} />
            </div>
          </div>
        )}

        <div className="chat-header" style={{ backgroundColor: primaryColor }}>
          <img 
            src={saraAvatar} 
            alt="Sara" 
            className="profile-image"
            onError={(e) => {
              e.target.onerror = null; 
              e.target.src = 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" fill="%23ffffff"><circle cx="50" cy="40" r="30"/><circle cx="50" cy="100" r="40"/></svg>';
            }}
          />
          <div className="header-info">
            <div className="profile-name">Sara - Asesora Universitaria</div>
            <div className="status">En línea</div>
          </div>
        </div>

        <div className="messages-container">
          {messages.map((msg, index) => (
            <div
              key={index}
              className={`message-container ${msg.sender === "user" ? "user-message-container" : ""}`}
            >
              {msg.sender === "bot" && (
                <img 
                  src={saraAvatar} 
                  alt="Sara" 
                  className="bot-profile-image"
                  onError={(e) => {
                    e.target.onerror = null; 
                    e.target.src = 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" fill="%23ffffff"><circle cx="50" cy="40" r="30"/><circle cx="50" cy="100" r="40"/></svg>';
                  }}
                />
              )}
              
              <div className={`message ${msg.sender === "user" ? "user-message" : "bot-message"}`}>
                {msg.sender === "bot" ? (
                  <>
                    <ReactMarkdown 
                      components={{
                        a: CustomLink,
                        table: CustomTable,
                        th: ({ children }) => <th style={{ textAlign: 'left' }}>{children}</th>,
                        td: ({ children }) => <td style={{ textAlign: 'left' }}>{children}</td>
                      }}
                    >
                      {msg.text}
                    </ReactMarkdown>
                    {msg.documentos && renderDocumentos(msg.documentos)}
                  </>
                ) : (
                  msg.text
                )}
                <div className="timestamp">{formatTime(msg.timestamp)}</div>
              </div>
            </div>
          ))}

          {isTyping && (
            <div className="message-container">
              <img 
                src={saraAvatar} 
                alt="Sara" 
                className="bot-profile-image"
                onError={(e) => {
                  e.target.onerror = null; 
                  e.target.src = 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" fill="%23ffffff"><circle cx="50" cy="40" r="30"/><circle cx="50" cy="100" r="40"/></svg>';
                }}
              />
              <div className="message bot-message">
                <div className="typing-animation">
                  <div className="typing-dot"></div>
                  <div className="typing-dot"></div>
                  <div className="typing-dot"></div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
        
        <div className="input-container">
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyPress={(e) => e.key === "Enter" && sendMessage()}
            className="chat-input"
            placeholder="Escribe un mensaje..."
          />
          <button onClick={sendMessage} className="send-button">
            <svg viewBox="0 0 24 24" width="24" height="24" className="send-icon">
              <path fill="currentColor" d="M1.101 21.757L23.8 12.028 1.101 2.3l.011 7.912 13.623 1.816-13.623 1.817-.011 7.912z"></path>
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
};

export default Chat;