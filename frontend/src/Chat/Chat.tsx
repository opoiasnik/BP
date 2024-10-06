// @ts-ignore
import React, { useState } from 'react';
import axios from 'axios';
import { motion } from 'framer-motion';
import Message from '../Message/Message';
import './Chat.css';
import img from "../Images/send-message.png";
import newChatImg from "../Images/new-message.png";

interface Message {
    content: string;
    role: 'user' | 'assistant';
}

const Chat: React.FC = () => {
    const [messages, setMessages] = useState<Message[]>([]);
    const [inputValue, setInputValue] = useState('');

    const handleSend = async (messageContent: string) => {
        const newMessage: Message = { content: messageContent, role: 'user' };
        setMessages([...messages, newMessage]);

        try {
            const response = await axios.post('http://localhost:5000/api/chat', {
                query: messageContent,
            });

            const assistantMessage: Message = {
                content: response.data.summary,
                role: 'assistant',
            };
            setMessages((prevMessages) => [...prevMessages, assistantMessage]);
        } catch (error) {
            console.error('Ошибка при отправке запроса:', error);
        }
    };

    return (
        <div className="chat-container">
            <div className="chat-sidebar">
                <div className="chat-sidebar-header">
                    <h3 className="chat-sidebar-title">Your Chats</h3>
                    <img src={newChatImg} alt="New Chat" className="new-chat-img" />
                </div>
                <hr className="chat-divider" />
                <ul className="chat-list">
                    <li className="chat-list-item">Chat 1</li>
                    <li className="chat-list-item">Chat 2</li>
                </ul>
            </div>

            <div className="chat-main">
                <div className="chat-messages">
                    {messages.map((message, index) => (
                        <motion.div
                            key={index}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.3 }}
                        >
                            <Message content={message.content} role={message.role} />
                        </motion.div>
                    ))}
                </div>

                {/* Поле ввода сообщения */}
                <form
                    className="chat-input-container"
                    onSubmit={(e) => {
                        e.preventDefault();
                        handleSend(inputValue);
                        setInputValue('');
                    }}
                >
                    <input
                        type="text"
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        className="chat-input"
                        placeholder="Write your message"
                    />

                    <button type="submit" className="chat-send-button">
                        <img src={img} alt="Send" className="send-img" />
                    </button>
                </form>
            </div>
        </div>
    );
};

export default Chat;
