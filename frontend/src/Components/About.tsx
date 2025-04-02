import React, { useState, useEffect } from 'react';
import { Box, Typography, Grid, Paper } from '@mui/material';
import {Navbar} from '../pages/LandingPage';
import MedicalServicesIcon from '@mui/icons-material/MedicalServices';
import LocalHospitalIcon from '@mui/icons-material/LocalHospital';
import CodeIcon from '@mui/icons-material/Code';

const About: React.FC = () => {
    const [user, setUser] = useState<any>(null);

    useEffect(() => {
        const storedUser = localStorage.getItem('user');
        if (storedUser) {
            setUser(JSON.parse(storedUser));
        }
    }, []);

    return (
        <Box sx={{ background: 'linear-gradient(to right, #d0e7ff, #f0f8ff)', minHeight: '100vh', p: 4 }}>
            {/* Navigation bar */}
            <Navbar user={user} setUser={setUser} />

            {/* Main content with top padding to account for fixed Navbar */}
            <Box sx={{ pt: '80px' }}>
                <Typography
                    variant="h3"
                    align="center"
                    gutterBottom
                    sx={{ fontWeight: 'bold', color: '#0d47a1' }}
                >
                    About Health AI
                </Typography>
                <Typography
                    variant="h6"
                    align="center"
                    gutterBottom
                    sx={{ color: '#0d47a1', mb: 4 }}
                >
                    Your Personal AI Assistant for Tailored Drug Recommendations
                </Typography>
                <Grid container spacing={4} justifyContent="center">
                    {/* Project Information Card */}
                    <Grid item xs={12} md={6}>
                        <Paper elevation={3} sx={{ p: 3, backgroundColor: '#ffffff', borderRadius: '12px' }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                                <MedicalServicesIcon sx={{ fontSize: 40, color: '#0d47a1', mr: 1 }} />
                                <Typography variant="h5" sx={{ fontWeight: 'bold', color: '#0d47a1' }}>
                                    About the Project
                                </Typography>
                            </Box>
                            <Typography variant="body1" sx={{ color: '#424242', mb: 2 }}>
                                Health AI is a cutting-edge application specializing in providing personalized drug recommendations and medication advice.
                                Leveraging advanced AI models like Mistral and powerful search technologies such as Elasticsearch, our platform delivers accurate,
                                context-aware suggestions for both over-the-counter and prescription medications.
                            </Typography>
                            <Typography variant="body1" sx={{ color: '#424242' }}>
                                Our backend utilizes modern technologies including Flask, PostgreSQL, and Google OAuth, ensuring robust security and reliable performance.
                                We also use long-term conversational memory to continuously enhance our responses.
                            </Typography>
                        </Paper>
                    </Grid>
                    {/* How It Works Card */}
                    <Grid item xs={12} md={6}>
                        <Paper elevation={3} sx={{ p: 3, backgroundColor: '#ffffff', borderRadius: '12px' }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                                <LocalHospitalIcon sx={{ fontSize: 40, color: '#0d47a1', mr: 1 }} />
                                <Typography variant="h5" sx={{ fontWeight: 'bold', color: '#0d47a1' }}>
                                    How It Works
                                </Typography>
                            </Box>
                            <Typography variant="body1" sx={{ color: '#424242', mb: 2 }}>
                                Our system uses natural language processing to understand user queries and extract key details such as age, medical history,
                                and medication type. It then employs vector search techniques to fetch the most relevant information from a comprehensive drug database,
                                ensuring precise recommendations.
                            </Typography>
                            <Typography variant="body1" sx={{ color: '#424242' }}>
                                Health AI validates its responses to guarantee consistency and reliability, making it an innovative solution for personalized healthcare guidance.
                            </Typography>
                        </Paper>
                    </Grid>
                    {/* Future Enhancements Card */}
                    <Grid item xs={12}>
                        <Paper elevation={3} sx={{ p: 3, backgroundColor: '#ffffff', borderRadius: '12px' }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                                <CodeIcon sx={{ fontSize: 40, color: '#0d47a1', mr: 1 }} />
                                <Typography variant="h5" sx={{ fontWeight: 'bold', color: '#0d47a1' }}>
                                    What's Next?
                                </Typography>
                            </Box>
                            <Typography variant="body1" sx={{ color: '#424242' }}>
                                We are continuously improving Health AI by integrating additional data sources and refining our AI algorithms.
                                Future enhancements include real-time drug interaction checks, comprehensive patient monitoring,
                                and seamless integration with healthcare providers. Stay tuned for more exciting updates and features as we strive to make healthcare more accessible and efficient.
                            </Typography>
                        </Paper>
                    </Grid>
                </Grid>
                {/* Footer */}
                <Box sx={{ textAlign: 'center', mt: 6 }}>
                    <Typography variant="body2" sx={{ color: '#424242' }}>
                        © {new Date().getFullYear()} Health AI. All rights reserved.
                    </Typography>
                </Box>
            </Box>
        </Box>
    );
};

export default About;
