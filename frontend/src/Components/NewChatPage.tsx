import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import gsap from "gsap";
import { useGSAP } from "@gsap/react";
import { useLazySendChatQuestionQuery } from "../store/api/chatApi";

interface ChatMessage {
    sender: string;
    text: string;
}

const NewChatPage: React.FC = () => {
    const [sendChatQuestion, { isLoading, isFetching }] = useLazySendChatQuestionQuery();
    const [message, setMessage] = useState<string>('');
    const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
    const navigate = useNavigate();

    // Новый чат: всегда начинаем с пустой истории
    useEffect(() => {
        setChatHistory([]);
    }, []);

    async function onSubmit() {
        if (!message.trim()) return;

        // Добавляем сообщение пользователя в локальное состояние
        const newUserMessage: ChatMessage = { sender: 'User', text: message };
        const updatedHistory = [...chatHistory, newUserMessage];
        setChatHistory(updatedHistory);
        const userMessage = message;
        setMessage('');

        // Получаем email пользователя из localStorage (если требуется)
        const storedUser = localStorage.getItem('user');
        const email = storedUser ? JSON.parse(storedUser).email : '';

        // Так как это новый чат, не передаем chatId
        const question = { query: userMessage, email };

        try {
            const res = await sendChatQuestion(question).unwrap();
            console.log("Response from server:", res);

            let bestAnswer = res.response.best_answer;
            if (typeof bestAnswer !== "string") {
                bestAnswer = String(bestAnswer);
            }
            bestAnswer = bestAnswer
                .replace(/[*#]/g, "")
                .replace(/(\d\.\s)/g, "\n\n$1")
                .replace(/:\s-/g, ":\n-");

            const newAssistantMessage: ChatMessage = { sender: 'Assistant', text: bestAnswer };
            const newUpdatedHistory = [...updatedHistory, newAssistantMessage];
            setChatHistory(newUpdatedHistory);

            // Если сервер возвращает новый chatId, обновляем URL и state,
            // чтобы отобразить созданный новый чат (и сохранить историю для последующей загрузки)
            if (res.response.chatId) {
                const chatString = newUpdatedHistory
                    .map(msg => (msg.sender === 'User' ? "User: " : "Bot: ") + msg.text)
                    .join("\n");
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
            console.error("Error:", error);
            setChatHistory(prev => [...prev, { sender: 'Assistant', text: "Что-то пошло не так" }]);
        }
    }

    useGSAP(() => {
        gsap.from('#input', { opacity: 0, y: 5, ease: 'power2.inOut', duration: 0.5 });
    }, []);

    return (
        <div className='w-full h-full flex flex-col justify-end items-center p-4 gap-8'>
            {/* Область отображения истории чата */}
            <div className="w-full overflow-y-auto no-scrollbar h-full p-2 border-gray-200 mb-4">
                {chatHistory.length > 0 ? (
                    <>
                        {chatHistory.map((msg, index) => (
                            <div key={index} className={`flex ${msg.sender === 'User' ? 'justify-end' : 'justify-start'} mb-2`}>
                                <div className={`p-2 rounded-lg max-w-md ${msg.sender === 'User' ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-800'}`}>
                                    {msg.text.split("\n").map((line, i) => (
                                        <p key={i}>{line}</p>
                                    ))}
                                </div>
                            </div>
                        ))}
                        {(isLoading || isFetching) && (
                            <div className="flex justify-start mb-2">
                                <div className="p-2 rounded-lg max-w-md bg-gray-200 text-gray-800">
                                    <p className="flex items-center">
                                        I'm thinking <div className="loader" style={{ marginLeft: '8px' }}></div>
                                    </p>
                                </div>
                            </div>
                        )}
                    </>
                ) : (
                    <div className="w-full h-full items-center flex flex-col gap-2 justify-center">
                        <h1 className="text-xl" id="firstheading">
                            Start a New Chat
                        </h1>
                    </div>
                )}
            </div>

            {/* Область ввода сообщения */}
            <div id="input" className="w-2/3 rounded-xl drop-shadow-2xl mb-20">
                <div className="flex">
                    <input
                        placeholder="Type your message..."
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

export default NewChatPage;
