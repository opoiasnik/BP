import React, { useEffect, useState, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useLazySendChatQuestionQuery } from '../store/api/chatApi';
import callCenterIcon from '../assets/call-center.png';

interface ChatMessage {
    sender: string;
    text: string;
}

const HomePage: React.FC = () => {
    const [sendChatQuestion, { isLoading, isFetching }] = useLazySendChatQuestionQuery();
    const [message, setMessage] = useState('');
    const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const location = useLocation();
    const navigate = useNavigate();
    const state = (location.state as any) || {};

    const isNewChat = state.newChat === true;
    const selectedChat = state.selectedChat || null;
    const selectedChatId = selectedChat ? selectedChat.id : null;

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [chatHistory, isLoading, isFetching]);

    useEffect(() => {
        if (!isNewChat && selectedChat && selectedChat.chat) {
            const messages: ChatMessage[] = selectedChat.chat
                .split(/(?=^(User:|Bot:))/m)
                .map((msg) => {
                    const trimmed = msg.trim();
                    const sender = trimmed.startsWith('User:') ? 'User' : 'Assistant';
                    return {
                        sender,
                        text: trimmed.replace(/^User:|^Bot:/, '').trim(),
                    };
                });
            setChatHistory(messages);
        } else {
            setChatHistory([]);
        }
    }, [isNewChat, selectedChat]);

    /**
     * Функция форматирования сообщения.
     * Если в ответе отсутствуют символы перевода строки, пытаемся разбить текст по нумерованным пунктам.
     */
    const formatMessage = (text: string) => {
        let lines: string[] = [];

        if (text.includes('\n')) {
            lines = text.split('\n');
        } else {
            lines = text.split(/(?=\d+\.\s+)/);
        }

        lines = lines.map((line) => line.trim()).filter((line) => line !== '');
        if (lines.length === 0) return null;

        return lines.map((line, index) => {
            if (/^\d+\.\s*/.test(line)) {
                const colonIndex = line.indexOf(':');
                if (colonIndex !== -1) {
                    const firstPart = line.substring(0, colonIndex);
                    const rest = line.substring(colonIndex + 1);
                    return (
                        <div key={index} className="mb-1">
                            <strong>{firstPart.trim()}</strong>: {rest.trim()}
                        </div>
                    );
                } else {
                    return (
                        <div key={index} className="mb-1">
                            <strong>{line}</strong>
                        </div>
                    );
                }
            }
            return <div key={index}>{line}</div>;
        });
    };

    const onSubmit = async () => {
        if (!message.trim()) return;
        const userMessage = message.trim();
        setMessage('');
        setChatHistory((prev) => [...prev, { sender: 'User', text: userMessage }]);

        const storedUser = localStorage.getItem('user');
        const email = storedUser ? JSON.parse(storedUser).email : '';
        const payload = selectedChatId
            ? { query: userMessage, chatId: selectedChatId, email }
            : { query: userMessage, email };

        try {
            const res = await sendChatQuestion(payload).unwrap();
            let bestAnswer = res.response.best_answer;
            if (typeof bestAnswer !== 'string') {
                bestAnswer = String(bestAnswer);
            }
            bestAnswer = bestAnswer.trim();

            if (bestAnswer) {
                setChatHistory((prev) => [...prev, { sender: 'Assistant', text: bestAnswer }]);
            }

            if (!selectedChatId && res.response.chatId) {
                const updatedChatHistory = [...chatHistory, { sender: 'User', text: userMessage }];
                if (bestAnswer) {
                    updatedChatHistory.push({ sender: 'Assistant', text: bestAnswer });
                }
                const chatString = updatedChatHistory
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
    };

    return (
        <div className="flex flex-col justify-end items-center p-4 gap-8 h-full w-full">
            <div className="w-full p-2 rounded overflow-y-auto h-full mb-4">
                {chatHistory.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-full">
                        <h1 className="text-xl">Start a New Chat</h1>
                    </div>
                ) : (
                    chatHistory.map((msg, index) => {
                        const formattedMessage = formatMessage(msg.text);
                        if (!formattedMessage) return null;
                        return (
                            <div
                                key={index}
                                className={`flex mb-2 ${msg.sender === 'User' ? 'justify-end' : 'justify-start items-start'}`}
                            >
                                {msg.sender === 'Assistant' && (
                                    <img
                                        src={callCenterIcon}
                                        alt="Call Center Icon"
                                        className="w-6 h-6 mr-2"
                                    />
                                )}
                                <div
                                    className={`p-3 rounded-lg max-w-md ${
                                        msg.sender === 'User'
                                            ? 'bg-blue-500 text-white'
                                            : 'bg-gray-200 text-gray-800'
                                    }`}
                                >
                                    {formattedMessage}
                                </div>
                            </div>
                        );
                    })
                )}

                {(isLoading || isFetching) && (
                    <div className="flex mb-2 justify-start items-start">
                        <img src={callCenterIcon} alt="Call Center Icon" className="w-6 h-6 mr-2" />
                        <div className="p-3 rounded-lg max-w-md bg-gray-200 text-gray-800 flex items-center">
                            <svg
                                className="animate-spin h-5 w-5 mr-3 text-gray-500"
                                xmlns="http://www.w3.org/2000/svg"
                                fill="none"
                                viewBox="0 0 24 24"
                            >
                                <circle
                                    className="opacity-25"
                                    cx="12"
                                    cy="12"
                                    r="10"
                                    stroke="currentColor"
                                    strokeWidth="4"
                                ></circle>
                                <path
                                    className="opacity-75"
                                    fill="currentColor"
                                    d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
                                ></path>
                            </svg>
                            <span>Assistant is typing...</span>
                        </div>
                    </div>
                )}

                <div ref={messagesEndRef} />
            </div>

            <div className="w-2/3 mb-20">
                <div className="flex">
                    <input
                        type="text"
                        placeholder="Waiting for your question..."
                        value={message}
                        onChange={(e) => setMessage(e.target.value)}
                        disabled={isLoading || isFetching}
                        className="w-full px-5 py-2 rounded-l-xl outline-none border border-gray-300"
                    />
                    <button
                        onClick={onSubmit}
                        disabled={isLoading || isFetching}
                        className="bg-black text-white font-semibold px-4 py-2 rounded-r-xl hover:bg-gray-800 disabled:opacity-50"
                    >
                        Send
                    </button>
                </div>
            </div>
        </div>
    );
};

export default HomePage;
