import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, Typography, Paper } from '@mui/material';

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

    const handleClick = (item: ChatHistoryItem) => {
        navigate(`/dashboard/chat/${item.id}`, { state: { selectedChat: item } });
    };

    return (
        <Box
            sx={{
                width: '100%',
                height: '100vh',
                overflowY: 'auto',
                background: '#f5f5f5',
                boxSizing: 'border-box',
                p: 3,

                /* Hide scrollbar for Chrome, Safari and Opera */
                '&::-webkit-scrollbar': {
                    display: 'none',
                },
                /* Hide scrollbar for IE, Edge and Firefox */
                '-ms-overflow-style': 'none',  // IE and Edge
                'scrollbarWidth': 'none',      // Firefox
            }}
        >
            <Typography
                variant="h4"
                sx={{
                    mb: 3,
                    fontWeight: 'bold',
                    textAlign: 'center',
                    color: '#0d47a1',
                }}
            >
                Chat History
            </Typography>
            {error ? (
                <Typography
                    variant="body1"
                    sx={{ color: 'error.main', textAlign: 'center' }}
                >
                    {error}
                </Typography>
            ) : (
                <Box sx={{ maxWidth: '800px', mx: 'auto' }}>
                    {history.length === 0 ? (
                        <Typography
                            variant="body1"
                            sx={{ textAlign: 'center', color: '#424242' }}
                        >
                            No chat history found.
                        </Typography>
                    ) : (
                        history.map((item) => {
                            const lines = item.chat.split("\n");
                            let firstUserMessage = lines[0];
                            if (firstUserMessage.startsWith("User:")) {
                                firstUserMessage = firstUserMessage.replace("User:", "").trim();
                            }
                            return (
                                <Paper
                                    key={item.id}
                                    sx={{
                                        p: 2,
                                        mb: 2,
                                        cursor: 'pointer',
                                        transition: 'box-shadow 0.3s ease',
                                        '&:hover': { boxShadow: 6 },
                                    }}
                                    onClick={() => handleClick(item)}
                                >
                                    <Box
                                        sx={{
                                            display: 'flex',
                                            justifyContent: 'space-between',
                                            alignItems: 'center',
                                        }}
                                    >
                                        <Typography
                                            variant="subtitle1"
                                            sx={{ fontWeight: 'bold', color: '#0d47a1' }}
                                        >
                                            {firstUserMessage}
                                        </Typography>
                                        <Typography
                                            variant="caption"
                                            sx={{ color: '#757575' }}
                                        >
                                            {new Date(item.created_at).toLocaleString()}
                                        </Typography>
                                    </Box>
                                </Paper>
                            );
                        })
                    )}
                </Box>
            )}
        </Box>
    );
};

export default ChatHistory;
