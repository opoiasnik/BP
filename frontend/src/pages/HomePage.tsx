import React, { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { MdLocalPharmacy, MdSelfImprovement } from "react-icons/md";
import { GiPill } from "react-icons/gi";
import gsap from "gsap";
import { useGSAP } from "@gsap/react";
import { useLazySendChatQuestionQuery } from "../store/api/chatApi";

interface ChatMessage {
    sender: string;
    text: string;
}

const HomePage = () => {
    const [sendChatQuestion, { isLoading, isFetching }] = useLazySendChatQuestionQuery();

    type Category = 'medication' | 'supplements' | 'lifestyle';
    const [category, setCategory] = useState<Category | null>(null);
    const [message, setMessage] = useState<string>('');
    const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);

    // Получаем объект location для доступа к переданному через navigate состоянию
    const location = useLocation();

    // Если через navigate передан выбранный чат, извлекаем его
    const selectedChat = location.state && (location.state as any).selectedChat
        ? (location.state as any).selectedChat as { id: number; chat: string; created_at: string }
        : null;

    // Если выбранный чат существует, сохраняем его ID для передачи в запрос
    const selectedChatId = selectedChat ? selectedChat.id : null;

    // При монтировании, если выбранный чат передан, разбиваем его содержимое на сообщения
    useEffect(() => {
        if (selectedChat) {
            const lines = selectedChat.chat.split("\n").filter(line => line.trim() !== "");
            const loadedChatHistory = lines.map((line) => {
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
    }, [selectedChat]);

    async function onSubmit() {
        if (!message.trim()) return;

        // Добавляем сообщение пользователя в локальное состояние
        setChatHistory(prev => [...prev, { sender: 'User', text: message }]);
        const userMessage = message;
        setMessage('');

        // Получаем email пользователя из localStorage (если нужно)
        const storedUser = localStorage.getItem('user');
        const email = storedUser ? JSON.parse(storedUser).email : '';

        // Формируем объект запроса; если выбранный чат существует, передаём его ID
        const question = selectedChatId
            ? { query: userMessage, chatId: selectedChatId, email }
            : { query: userMessage, email };

        try {
            const res = await sendChatQuestion(question).unwrap();
            console.log("Response from server:", res);

            // Получаем текстовый ответ из res.response.best_answer
            let bestAnswer = res.response.best_answer;
            if (typeof bestAnswer !== "string") {
                bestAnswer = JSON.stringify(bestAnswer);
            }
            // Если нужно, можно также отформатировать ответ (например, убрать звездочки)
            bestAnswer = bestAnswer.replace(/[*#]/g, "")
                .replace(/(\d\.\s)/g, "\n\n$1")
                .replace(/:\s-/g, ":\n-");

            // Формируем сообщение ассистента без дополнительных данных
            const assistantMessage: ChatMessage = {
                sender: 'Assistant',
                text: bestAnswer,
            };

            // Обновляем локальную историю чата
            setChatHistory(prev => [...prev, assistantMessage]);
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
                            <div
                                key={index}
                                className={`flex ${msg.sender === 'User' ? 'justify-end' : 'justify-start'} mb-2`}
                            >
                                <div
                                    className={`p-2 rounded-lg max-w-md ${
                                        msg.sender === 'User'
                                            ? 'bg-blue-500 text-white'
                                            : 'bg-gray-200 text-gray-800'
                                    }`}
                                >
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
                                        I'm thinking <div className="loader"></div>
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
