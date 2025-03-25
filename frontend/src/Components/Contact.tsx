import React, { useState, useEffect } from 'react';
import { Box, Typography, Paper, Grid } from '@mui/material';
import {Navbar} from '../pages/LandingPage';
import { useNavigate } from 'react-router-dom';
import SchoolIcon from '@mui/icons-material/School';
import DeveloperModeIcon from '@mui/icons-material/DeveloperMode';
import EmailIcon from '@mui/icons-material/Email';

const Contact: React.FC = () => {
    const navigate = useNavigate();
    const [user, setUser] = useState<any>(null);

    // Load user information from localStorage to pass to Navbar
    useEffect(() => {
        const storedUser = localStorage.getItem('user');
        if (storedUser) {
            setUser(JSON.parse(storedUser));
        }
    }, []);

    return (
        <Box
            sx={{
                background: 'linear-gradient(to right, #d0e7ff, #f0f8ff)',
                minHeight: '100vh',
                p: 4,
            }}
        >
            {/* Navbar with navigation links */}
            <Navbar user={user} setUser={setUser} />

            {/* Main content with spacing for fixed Navbar */}
            <Box sx={{ pt: '80px', maxWidth: '800px', mx: 'auto' }}>
                <Paper
                    elevation={4}
                    sx={{
                        p: 4,
                        borderRadius: '16px',
                        backgroundColor: '#ffffff',
                        boxShadow: '0 4px 20px rgba(0,0,0,0.1)',
                    }}
                >
                    <Typography
                        variant="h4"
                        align="center"
                        sx={{ fontWeight: 'bold', color: '#0d47a1', mb: 4 }}
                    >
                        Contact
                    </Typography>
                    <Grid container spacing={4}>
                        {/* University Info */}
                        <Grid item xs={12} sm={6}>
                            <Paper
                                elevation={2}
                                sx={{
                                    p: 2,
                                    display: 'flex',
                                    alignItems: 'center',
                                    borderRadius: '12px',
                                    backgroundColor: '#e3f2fd',
                                }}
                            >
                                <SchoolIcon sx={{ fontSize: 40, color: '#0d47a1', mr: 2 }} />
                                <Box>
                                    <Typography variant="h6" sx={{ fontWeight: 'bold', color: '#0d47a1' }}>
                                        Technical University of Košice
                                    </Typography>
                                    <Typography variant="body2" sx={{ color: '#424242' }}>
                                        KEMT Department
                                    </Typography>
                                </Box>
                            </Paper>
                        </Grid>
                        {/* Developer Info */}
                        <Grid item xs={12} sm={6}>
                            <Paper
                                elevation={2}
                                sx={{
                                    p: 2,
                                    display: 'flex',
                                    alignItems: 'center',
                                    borderRadius: '12px',
                                    backgroundColor: '#e8f5e9',
                                }}
                            >
                                <DeveloperModeIcon sx={{ fontSize: 40, color: '#0d47a1', mr: 2 }} />
                                <Box>
                                    <Typography variant="h6" sx={{ fontWeight: 'bold', color: '#0d47a1' }}>
                                        Developer
                                    </Typography>
                                    <Typography variant="body2" sx={{ color: '#424242' }}>
                                        oleh.poiasnik@student.tuke.sk
                                    </Typography>
                                </Box>
                            </Paper>
                        </Grid>
                        {/* Additional Contact Option */}
                        <Grid item xs={12}>
                            <Paper
                                elevation={2}
                                sx={{
                                    p: 2,
                                    display: 'flex',
                                    alignItems: 'center',
                                    borderRadius: '12px',
                                    backgroundColor: '#fff3e0',
                                }}
                            >
                                <EmailIcon sx={{ fontSize: 40, color: '#0d47a1', mr: 2 }} />
                                <Box>
                                    <Typography variant="h6" sx={{ fontWeight: 'bold', color: '#0d47a1' }}>
                                        Email Us
                                    </Typography>
                                    <Typography variant="body2" sx={{ color: '#424242' }}>
                                        For any inquiries or further information about Health AI, please get in touch!
                                    </Typography>
                                </Box>
                            </Paper>
                        </Grid>
                    </Grid>
                    <Box sx={{ textAlign: 'center', mt: 4 }}>
                        <Typography variant="body2" sx={{ color: '#424242' }}>
                            © {new Date().getFullYear()} Health AI. All rights reserved.
                        </Typography>
                    </Box>
                </Paper>
            </Box>
        </Box>
    );
};

export default Contact;
