import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

interface ChatHistoryItem {
    id: number;
    chat: string;
    created_at: string;
}

const ChatHistory: React.FC = () => {
    const [history, setHistory] = useState<ChatHistoryItem[]>([]);
    const [error, setError] = useState<string | null>(null);
    const navigate = useNavigate();

    useEffect(() => {
        const storedUser = localStorage.getItem('user');
        if (storedUser) {
            const user = JSON.parse(storedUser);
            const email = user.email;
            fetch(`http://localhost:5000/api/chat_history?email=${encodeURIComponent(email)}`)
                .then((res) => res.json())
                .then((data) => {
                    if (data.error) {
                        setError(data.error);
                    } else {
                        setHistory(data.history);
                    }
                })
                .catch(() => setError('Error fetching chat history'));
        } else {
            setError('User not logged in');
        }
    }, []);

    // При клике переходим на HomePage и передаём выбранный чат через state.
    const handleClick = (item: ChatHistoryItem) => {
        navigate('/dashboard', { state: { selectedChat: item } });
    };

    return (
        <div style={{ padding: '20px' }}>
            <h1>Chat History</h1>
            {error && <p style={{ color: 'red' }}>{error}</p>}
            {history.length === 0 && !error ? (
                <p>No chat history found.</p>
            ) : (
                <ul style={{ listStyleType: 'none', padding: 0 }}>
                    {history.map((item) => {
                        // Извлекаем первую строку из сохранённого чата.
                        // Предполагаем, что чат хранится в формате:
                        // "User: <вопрос>\nBot: <ответ>\n..."
                        const lines = item.chat.split("\n");
                        let firstUserMessage = lines[0];
                        if (firstUserMessage.startsWith("User:")) {
                            firstUserMessage = firstUserMessage.replace("User:", "").trim();
                        }
                        return (
                            <li
                                key={item.id}
                                style={{
                                    marginBottom: '15px',
                                    borderBottom: '1px solid #ccc',
                                    paddingBottom: '10px',
                                    cursor: 'pointer'
                                }}
                                onClick={() => handleClick(item)}
                            >
                                <div>
                                    <strong>{firstUserMessage}</strong>
                                </div>
                                <small>{new Date(item.created_at).toLocaleString()}</small>
                            </li>
                        );
                    })}
                </ul>
            )}
        </div>
    );
};

export default ChatHistory;
