import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import gsap from 'gsap';
import { useLazySendChatQuestionQuery } from '../store/api/chatApi';
import AssistantIcon from '../assets/call-center.png'; // Импорт иконки ассистента

interface ChatMessage {
    sender: string;
    text: string;
}

const HomePage: React.FC = () => {
    const [sendChatQuestion, { isLoading, isFetching }] = useLazySendChatQuestionQuery();
    const [message, setMessage] = useState<string>('');
    const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);

    const location = useLocation();
    const navigate = useNavigate();
    const state = (location.state as any) || {};

    const isNewChat = state.newChat === true;
    const selectedChat = state.selectedChat
        ? (state.selectedChat as { id: number; chat: string; created_at: string })
        : null;
    const selectedChatId = selectedChat ? selectedChat.id : null;

    useEffect(() => {
        if (isNewChat) {
            setChatHistory([]);
        } else if (selectedChat) {
            const lines = selectedChat.chat.split('\n').filter((line) => line.trim() !== '');
            const loadedChatHistory = lines.map((line) => {
                if (line.startsWith('User:')) {
                    return { sender: 'User', text: line.replace('User:', '').trim() };
                } else if (line.startsWith('Bot:')) {
                    return { sender: 'Assistant', text: line.replace('Bot:', '').trim() };
                } else {
                    return { sender: 'Info', text: line.trim() };
                }
            });
            setChatHistory(loadedChatHistory);
        }
    }, [isNewChat, selectedChat]);

    async function onSubmit() {
        if (!message.trim()) return;

        const newUserMessage: ChatMessage = { sender: 'User', text: message };
        setChatHistory((prev) => [...prev, newUserMessage]);
        const userMessage = message;
        setMessage('');

        const storedUser = localStorage.getItem('user');
        const email = storedUser ? JSON.parse(storedUser).email : '';

        const question = selectedChatId
            ? { query: userMessage, chatId: selectedChatId, email }
            : { query: userMessage, email };

        try {
            const res = await sendChatQuestion(question).unwrap();

            let bestAnswer = res.response.best_answer;
            if (typeof bestAnswer !== 'string') {
                bestAnswer = String(bestAnswer);
            }
            bestAnswer = bestAnswer
                .replace(/[*#]/g, '')
                .replace(/(\d\.\s)/g, '\n\n$1')
                .replace(/:\s-/g, ':\n-');

            const assistantMessage: ChatMessage = {
                sender: 'Assistant',
                text: bestAnswer,
            };

            setChatHistory((prev) => [...prev, assistantMessage]);

            if (!selectedChatId && res.response.chatId) {
                const chatString = chatHistory
                    .map((msg) => (msg.sender === 'User' ? 'User: ' : 'Bot: ') + msg.text)
                    .join('\n');
                navigate(`/dashboard/chat/${res.response.chatId}`, {
                    replace: true,
                    state: {
                        selectedChat: {
                            id: res.response.chatId,
                            chat: chatString,
                            created_at: new Date().toISOString(),
                        },
                    },
                });
            }
        } catch (error) {
            console.error('Error:', error);
            setChatHistory((prev) => [
                ...prev,
                { sender: 'Assistant', text: 'Что-то пошло не так' },
            ]);
        }
    }

    const groupedMessages = chatHistory.reduce((acc: { sender: string; text: string }[], message) => {
        const lastGroup = acc[acc.length - 1];
        if (lastGroup && lastGroup.sender === message.sender) {
            lastGroup.text += `\n${message.text}`;
        } else {
            acc.push({ sender: message.sender, text: message.text });
        }
        return acc;
    }, []);

    return (
        <div className="w-full h-full flex flex-col justify-end items-center p-4 gap-8">
            <div className="w-full overflow-y-auto no-scrollbar h-full p-2 border-gray-200 mb-4">
                {groupedMessages.length > 0 ? (
                    groupedMessages.map((msg, index) => (
                        <div
                            key={index}
                            className={`flex ${
                                msg.sender === 'User' ? 'justify-end' : 'justify-start'
                            } mb-2 items-start`}
                        >
                            {msg.sender === 'Assistant' && (
                                <div className="flex items-start">
                                    <img
                                        src={AssistantIcon}
                                        alt="Assistant Icon"
                                        className="w-12 h-12 mr-3 rounded-full object-cover"
                                        style={{ flexShrink: 0 }}
                                    />
                                </div>
                            )}
                            <div
                                className={`p-3 rounded-lg max-w-md ${
                                    msg.sender === 'User'
                                        ? 'bg-blue-500 text-white'
                                        : 'bg-gray-200 text-gray-800'
                                }`}
                                style={{ whiteSpace: 'pre-wrap' }}
                            >
                                {msg.text.split('\n').map((line, i) => (
                                    <p key={i}>{line}</p>
                                ))}
                            </div>
                        </div>
                    ))
                ) : (
                    <div className="w-full h-full items-center flex flex-col gap-2 justify-center">
                        <h1 className="text-xl" id="firstheading">
                            Start a New Chat
                        </h1>
                    </div>
                )}
                {(isLoading || isFetching) && (
                    <div className="flex justify-start mb-2 items-start">
                        <div className="flex items-start">
                            <img
                                src={AssistantIcon}
                                alt="Assistant Icon"
                                className="w-12 h-12 mr-3 rounded-full object-cover"
                                style={{ flexShrink: 0 }}
                            />
                        </div>
                        <div className="p-2 rounded-lg max-w-md bg-gray-200 text-gray-800">
                            <p className="flex items-center">
                                I'm thinking <span className="loader ml-2"></span>
                            </p>
                        </div>
                    </div>
                )}
            </div>

            <div id="input" className="w-2/3 rounded-xl drop-shadow-2xl mb-20">
                <div className="flex">
                    <input
                        placeholder="Waiting for your question..."
                        value={message}
                        onChange={(e) => setMessage(e.target.value)}
                        className="w-full px-5 py-2 rounded-l-xl outline-none"
                        type="text"
                    />
                    <button
                        disabled={isLoading || isFetching}
                        onClick={onSubmit}
                        className="bg-black rounded-r-xl px-4 py-2 text-white font-semibold hover:bg-slate-700"
                    >
                        Send
                    </button>
                </div>
            </div>
        </div>
    );
};

export default HomePage;
