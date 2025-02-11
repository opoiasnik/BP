import React, { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import gsap from 'gsap';
import { useGSAP } from '@gsap/react';
import { useLazySendChatQuestionQuery } from '../store/api/chatApi';
import callCenterIcon from '../assets/call-center.png';

interface ChatMessage {
    sender: string;
    text: string;
}

const NewChatPage: React.FC = () => {
    const [sendChatQuestion, { isLoading, isFetching }] = useLazySendChatQuestionQuery();
    const [message, setMessage] = useState<string>('');
    const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
    const navigate = useNavigate();
    const messagesEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [chatHistory, isLoading, isFetching]);

    useEffect(() => {
        setChatHistory([]);
    }, []);

    async function onSubmit() {
        if (!message.trim()) return;

        const newUserMessage: ChatMessage = { sender: 'User', text: message };
        const updatedHistory = [...chatHistory, newUserMessage];
        setChatHistory(updatedHistory);
        const userMessage = message;
        setMessage('');

        const storedUser = localStorage.getItem('user');
        const email = storedUser ? JSON.parse(storedUser).email : '';

        const question = { query: userMessage, email };

        try {
            const res = await sendChatQuestion(question).unwrap();
            console.log('Response from server:', res);

            let bestAnswer = res.response.best_answer;
            if (typeof bestAnswer !== 'string') {
                bestAnswer = String(bestAnswer);
            }
            bestAnswer = bestAnswer.trim();

            const newAssistantMessage: ChatMessage = { sender: 'Assistant', text: bestAnswer };
            const newUpdatedHistory = [...updatedHistory, newAssistantMessage];
            setChatHistory(newUpdatedHistory);

            if (res.response.chatId) {
                const chatString = newUpdatedHistory
                    .map(msg => (msg.sender === 'User' ? 'User: ' : 'Bot: ') + msg.text)
                    .join('\n');
                navigate(`/dashboard/chat/${res.response.chatId}`, {
                    replace: true,
                    state: {
                        selectedChat: {
                            id: res.response.chatId,
                            chat: chatString,
                            created_at: new Date().toISOString()
                        }
                    }
                });
            }
        } catch (error) {
            console.error('Error:', error);
            setChatHistory(prev => [
                ...prev,
                { sender: 'Assistant', text: 'Что-то пошло не так' }
            ]);
        }
    }

    useGSAP(() => {
        gsap.from('#input', { opacity: 0, y: 5, ease: 'power2.inOut', duration: 0.5 });
    }, []);

    return (
        <div className="flex flex-col justify-end items-center p-4 gap-8 h-full w-full">
            <div className="w-full p-2  rounded overflow-y-auto h-full mb-4">
                {chatHistory.length > 0 ? (
                    <>
                        {chatHistory.map((msg, index) => (
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
                                    className={`p-3 rounded-lg max-w-md flex ${
                                        msg.sender === 'User'
                                            ? 'bg-blue-500 text-white'
                                            : 'bg-gray-200 text-gray-800'
                                    }`}
                                    style={{ whiteSpace: 'normal' }}
                                >
                                    {msg.text.split('\n').map((line, i) => (
                                        <p key={i}>{line}</p>
                                    ))}
                                </div>
                            </div>
                        ))}

                        {(isLoading || isFetching) && (
                            <div className="flex mb-2 justify-start items-start">
                                <img
                                    src={callCenterIcon}
                                    alt="Call Center Icon"
                                    className="w-6 h-6 mr-2"
                                />
                                <div
                                    className="p-3 rounded-lg max-w-md flex bg-gray-200 text-gray-800"
                                    style={{ whiteSpace: 'normal' }}
                                >
                                    <div className="flex items-center">
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
                            </div>
                        )}
                    </>
                ) : (
                    <div className="w-full h-full flex flex-col gap-2 items-center justify-center">
                        <h1 className="text-xl" id="firstheading">
                            Start a New Chat
                        </h1>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            <div id="input" className="w-2/3 mb-20">
                <div className="flex">
                    <input
                        type="text"
                        placeholder="Type your message..."
                        value={message}
                        onChange={(e) => setMessage(e.target.value)}
                        className="w-full px-5 py-2 rounded-l-xl outline-none border border-gray-300"
                    />
                    <button
                        disabled={isLoading || isFetching}
                        onClick={onSubmit}
                        className="bg-black text-white font-semibold px-4 py-2 rounded-r-xl hover:bg-slate-700"
                    >
                        Send
                    </button>
                </div>
            </div>
        </div>
    );
};

export default NewChatPage;
