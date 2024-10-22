import React, { useState } from 'react';
import axios from 'axios';
import { motion } from 'framer-motion';
import Message from '../Message/Message';
import './Chat.css';
import img from '../Images/send-message.png';
import newChatImg from '../Images/new-message.png';
import ChatItem from '../ChatItem/ChatItem';

interface Message {
    content: string;
    role: 'user' | 'assistant';
}

const Chat: React.FC = () => {
    const [messages, setMessages] = useState<Message[]>([]);
    const [inputValue, setInputValue] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const handleSend = async (messageContent: string) => {
        if (messageContent.trim() === '') return;

        const newMessage: Message = { content: messageContent, role: 'user' };
        setMessages([...messages, newMessage]);
        setInputValue('');
        setIsLoading(true);

        try {
            const response = await axios.post('http://localhost:5000/api/chat', {
                query: messageContent,
            });

            const assistantMessages: Message[] = [];

            const { vector_search, text_search } = response.data;

            // Обработка результатов векторного поиска
            if (vector_search && vector_search.summaries) {
                if (vector_search.summaries.small) {
                    const smallContent = Array.isArray(vector_search.summaries.small)
                        ? vector_search.summaries.small.join('\n')
                        : vector_search.summaries.small;
                    assistantMessages.push({
                        content: `**Ответ от маленькой модели (векторный поиск):**\n${smallContent}`,
                        role: 'assistant',
                    });
                }

                if (vector_search.summaries.large) {
                    const largeContent = Array.isArray(vector_search.summaries.large)
                        ? vector_search.summaries.large.join('\n')
                        : vector_search.summaries.large;
                    assistantMessages.push({
                        content: `**Ответ от большой модели (векторный поиск):**\n${largeContent}`,
                        role: 'assistant',
                    });
                }
            }

            // Обработка результатов текстового поиска
            if (text_search && text_search.summaries) {
                if (text_search.summaries.small) {
                    const smallContent = Array.isArray(text_search.summaries.small)
                        ? text_search.summaries.small.join('\n')
                        : text_search.summaries.small;
                    assistantMessages.push({
                        content: `**Ответ от маленькой модели (текстовый поиск):**\n${smallContent}`,
                        role: 'assistant',
                    });
                }

                if (text_search.summaries.large) {
                    const largeContent = Array.isArray(text_search.summaries.large)
                        ? text_search.summaries.large.join('\n')
                        : text_search.summaries.large;
                    assistantMessages.push({
                        content: `**Ответ от большой модели (текстовый поиск):**\n${largeContent}`,
                        role: 'assistant',
                    });
                }
            }

            setMessages((prevMessages) => [...prevMessages, ...assistantMessages]);
        } catch (error) {
            console.error('Ошибка при отправке запроса:', error);
            setMessages((prevMessages) => [
                ...prevMessages,
                {
                    content: 'Произошла ошибка при получении ответа от сервера.',
                    role: 'assistant',
                },
            ]);
        } finally {
            setIsLoading(false);
        }
    };

    // Остальной код остается без изменений

    const fullfillChatItems = () => {
        const countOfChats: number = 10;
        const chatItems: JSX.Element[] = [];
        for (let i = 1; i < countOfChats; i++) {
            chatItems.push(
                <ChatItem
                    index={i}
                    key={i}
                    onMouseDownEvent={handleMouseDown}
                    onMouseMoveEvent={handleMouseMove}
                    onMouseUpEvent={handleMouseUp}
                />
            );
        }
        return chatItems;
    };

    const handleMouseDown = () => {
        console.log('mouseDown');
    };
    const handleMouseMove = () => {
        console.log('mouseMove');
    };
    const handleMouseUp = () => {
        console.log('mouseUp');
    };

    return (
        <div className="chat-container">
            <div className="chat-sidebar">
                <div className="chat-sidebar-header">
                    <h3 className="chat-sidebar-title">Your Chats</h3>
                    <img src={newChatImg} alt="New Chat" className="new-chat-img" />
                </div>
                <hr className="chat-divider" />
                <ul className="chat-list">{fullfillChatItems()}</ul>
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
                    {isLoading && (
                        <motion.div
                            key="loading"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="loading-message"
                        >
                            <Message content="Загрузка..." role="assistant" />
                        </motion.div>
                    )}
                </div>

                {/* Поле ввода сообщения */}
                <form
                    className="chat-input-container"
                    onSubmit={(e) => {
                        e.preventDefault();
                        handleSend(inputValue);
                    }}
                >
                    <input
                        type="text"
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        className="chat-input"
                        placeholder="Напишите ваше сообщение"
                    />

                    <button type="submit" className="chat-send-button" disabled={isLoading}>
                        <img src={img} alt="Send" className="send-img" />
                    </button>
                </form>
            </div>
        </div>
    );
};

export default Chat;
