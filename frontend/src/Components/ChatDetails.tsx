import React, { useEffect, useState } from 'react';
import { useParams, useLocation } from 'react-router-dom';

interface ChatHistoryItem {
    id: number;
    chat: string;
    created_at: string;
}

const ChatDetails: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const location = useLocation();
    const [chat, setChat] = useState<ChatHistoryItem | null>(location.state?.chat || null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!chat && id) {
            // Если данные не переданы через state, можно попробовать получить их с сервера
            fetch(`http://localhost:5000/api/chat_history_detail?id=${encodeURIComponent(id)}`)
                .then((res) => {
                    if (!res.ok) {
                        throw new Error('Chat not found');
                    }
                    return res.json();
                })
                .then((data) => {
                    if (data.error) {
                        setError(data.error);
                    } else {
                        setChat(data.chat);
                    }
                })
                .catch((err) => setError(err.message));
        }
    }, [id, chat]);

    if (error) {
        return <div>Error: {error}</div>;
    }

    if (!chat) {
        return <div>Loading chat details...</div>;
    }

    return (
        <div style={{ padding: '20px' }}>
            <h1>Chat Details</h1>
            <div style={{ border: '1px solid #ccc', padding: '10px' }}>
                {chat.chat.split('\n').map((line, index) => (
                    <p key={index}>{line}</p>
                ))}
            </div>
            <small>{new Date(chat.created_at).toLocaleString()}</small>
        </div>
    );
};

export default ChatDetails;
