// @ts-ignore
import React, { useState } from 'react';
import axios from 'axios';
import { motion } from 'framer-motion';
import Message from '../Message/Message';
import './Chat.css';
import img from "../Images/send-message.png";
import newChatImg from "../Images/new-message.png";
import ChatItem from "../ChatItem/ChatItem";

interface Message {
    content: string;
    role: 'user' | 'assistant';
}
interface ChatItemProps {
    index: number;
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
    const fullfillChatItems = () => {
        let countOfChats:number = 10;
        const chatItems: JSX.Element[] = [];
        for (let i = 1; i < countOfChats; i++){
            chatItems.push(<ChatItem index={i} key={i} onMouseDownEvent={handleMouseDown} onMouseMoveEvent={handleMouseMove} onMouseUpEvent={handleMouseUp}  />)
        }
        return chatItems;
    }
    const addEventListenerChatItem = (elements: HTMLElement[]) => {
        elements.forEach(item => {
            item.addEventListener('mousedown', () => {

            })
        })
    }
    const handleMouseDown = () => {
        console.log('mouseDown');
    }
    const handleMouseMove = () => {
        console.log('mouseMove');
    }
    const handleMouseUp = () => {
        console.log('mouseUp');
    }

    return (
        <div className="chat-container">
            <div className="chat-sidebar">
                <div className="chat-sidebar-header">
                    <h3 className="chat-sidebar-title">Your Chats</h3>
                    <img src={newChatImg} alt="New Chat" className="new-chat-img" />
                </div>
                <hr className="chat-divider" />
                <ul className="chat-list">
                    {fullfillChatItems()}
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
