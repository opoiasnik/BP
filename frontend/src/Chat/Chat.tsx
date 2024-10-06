// @ts-ignore
import React, { useState } from 'react';
import axios from 'axios';
import { Box, Button, Container, Grid, Paper, TextField, Typography, List, ListItem, Divider } from '@mui/material';
import { motion } from 'framer-motion';
import Message from '../Message/Message';
import InputField from '../InputField/InputField';
import '../styles.css';

interface Message {
    content: string;
    role: 'user' | 'assistant';
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

    return (
        <Container maxWidth="xl" sx={{ height: '100vh', display: 'flex', padding: '0' }}>
            {/* Левая панель для информации о чатах */}
            <Grid container spacing={2} sx={{ height: '100%' }}>
                <Grid item xs={3}>
                    <Paper sx={{ height: '100%', padding: '20px', backgroundColor: '#0077b6' }}>
                        <Typography variant="h5" color="white">
                            Your Chats
                        </Typography>
                        <Divider sx={{ backgroundColor: 'white', margin: '20px 0' }} />
                        <List>
                            <ListItem>
                                <Typography color="white">Chat 1</Typography>
                            </ListItem>
                            <ListItem>
                                <Typography color="white">Chat 2</Typography>
                            </ListItem>
                            {/* Можно добавить еще чаты */}
                        </List>
                        <Button variant="contained" color="primary" fullWidth>
                            New Chat
                        </Button>
                    </Paper>
                </Grid>

                <Grid item xs={9}>
                    <Paper sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                        <Box
                            sx={{
                                flexGrow: 1,
                                padding: '20px',
                                backgroundColor: '#e0f7fa',
                                overflowY: 'auto',
                            }}
                        >

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
                        </Box>


                        <Box
                            component="form"
                            sx={{
                                padding: '20px',
                                display: 'flex',
                                borderTop: '1px solid #0077b6',
                                backgroundColor: '#fff',
                            }}
                            onSubmit={(e) => {
                                e.preventDefault();
                                handleSend(inputValue);
                                setInputValue('');
                            }}
                        >
                            <TextField
                                value={inputValue}
                                onChange={(e) => setInputValue(e.target.value)}
                                variant="outlined"
                                fullWidth
                                placeholder="Type your message..."
                            />
                            <Button
                                type="submit"
                                variant="contained"
                                color="primary"
                                sx={{ marginLeft: '10px' }}
                            >
                                Send
                            </Button>
                        </Box>
                    </Paper>
                </Grid>
            </Grid>
        </Container>
    );
};

export default Chat;
