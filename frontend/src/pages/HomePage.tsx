import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import gsap from "gsap";
import { useGSAP } from "@gsap/react";
import { useLazySendChatQuestionQuery } from "../store/api/chatApi";

interface ChatMessage {
    sender: string;
    text: string;
}

const HomePage = () => {
    const [sendChatQuestion, { isLoading, isFetching }] = useLazySendChatQuestionQuery();
    const [message, setMessage] = useState<string>('');
    const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);

    const location = useLocation();
    const navigate = useNavigate();
    const state = location.state as any || {};

    // Если state.newChat === true, начинаем новый чат (очищаем историю)
    const isNewChat = state.newChat === true;
    // Если передан выбранный чат, извлекаем его данные
    const selectedChat = state.selectedChat ? state.selectedChat as { id: number; chat: string; created_at: string } : null;
    const selectedChatId = selectedChat ? selectedChat.id : null;

    // При монтировании: если новый чат — очищаем историю, иначе, если выбранный чат передан, загружаем его историю
    useEffect(() => {
        if (isNewChat) {
            setChatHistory([]);
        } else if (selectedChat) {
            const lines = selectedChat.chat.split("\n").filter(line => line.trim() !== "");
            const loadedChatHistory = lines.map(line => {
                if (line.startsWith("User:")) {
                    return { sender: 'User', text: line.replace("User:", "").trim() };
                } else if (line.startsWith("Bot:")) {
                    return { sender: 'Assistant', text: line.replace("Bot:", "").trim() };
                } else {
                    return { sender: 'Info', text: line.trim() };
                }
            });
            setChatHistory(loadedChatHistory);
        }
    }, [isNewChat, selectedChat]);

    async function onSubmit() {
        if (!message.trim()) return;
        // Создаем локальную копию истории с добавленным сообщением пользователя
        const newUserMessage: ChatMessage = { sender: 'User', text: message };
        const updatedHistory = [...chatHistory, newUserMessage];
        // Обновляем локальное состояние
        setChatHistory(updatedHistory);
        const userMessage = message;
        setMessage('');

        // Получаем email пользователя (если нужно)
        const storedUser = localStorage.getItem('user');
        const email = storedUser ? JSON.parse(storedUser).email : '';

        // Формируем объект запроса: если чат уже существует, передаем chatId, иначе нет.
        const question = selectedChatId
            ? { query: userMessage, chatId: selectedChatId, email }
            : { query: userMessage, email };

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

            const assistantMessage: ChatMessage = {
                sender: 'Assistant',
                text: bestAnswer,
            };

            const newUpdatedHistory = [...updatedHistory, assistantMessage];

            // Если это новый чат (selectedChatId отсутствует) и сервер вернул chatId, обновляем URL и state
            if (!selectedChatId && res.response.chatId) {
                // Создаем строковое представление истории для сохранения (например, для будущей загрузки)
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
            } else {
                // Если обновляем существующий чат, просто обновляем локальное состояние
                setChatHistory(newUpdatedHistory);
            }
        } catch (error) {
            console.error("Error:", error);
            setChatHistory(prev => [...prev, { sender: 'Assistant', text: "Что-то пошло не так" }]);
        }
    }

    useGSAP(() => {
        gsap.from('#firstheading', { opacity: 0.3, ease: 'power2.inOut', duration: 0.5 });
        gsap.from('#secondheading', { opacity: 0, y: 5, ease: 'power2.inOut', delay: 0.3, duration: 0.5 });
        gsap.from('#buttons', { opacity: 0, y: 5, ease: 'power2.inOut', delay: 0.3, duration: 0.5 });
        gsap.from('#input', { opacity: 0, y: 5, ease: 'power2.inOut', duration: 0.5 });
    }, []);

    return (
        <div className='w-full h-full flex flex-col justify-end items-center p-4 gap-8'>
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
                            Ask any question or advice about your health or trainings and let's see what happens
                        </h1>
                        <h2 className="text-gray-600" id="secondheading">
                            Choose a category for a better experience and make your life better with Health AI
                        </h2>
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
