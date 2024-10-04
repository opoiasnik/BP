import React, { useState } from 'react';
import axios from 'axios';
import Message from './Message';
import InputField from './InputField';
import './styles.css'

interface Message {
    content: string;
    role: 'user' | 'assistant';
}

const Chat: React.FC = () => {
    const [messages, setMessages] = useState<Message[]>([]);

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
            <div className="messages">
                {messages.map((message, index) => (
                    <Message key={index} content={message.content} role={message.role} />
                ))}
            </div>
            <InputField onSend={handleSend} />
        </div>
    );
};

export default Chat;
