import React, { useEffect } from 'react';
import {
    Box,
    Button,
    Card,
    CardContent,
    TextField,
    Typography,
    Divider,
    Link as MuiLink,
} from '@mui/material';
import { GoogleLogin } from '@react-oauth/google';
import { Link } from 'react-router-dom';
import gsap from 'gsap';

const RegistrationForm: React.FC = () => {
    useEffect(() => {
        gsap.from('.registration-card', {
            opacity: 0,
            y: -20,
            duration: 0.6,
            ease: 'power2.out',
        });
    }, []);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        console.log('Registration form submitted');
    };

    const handleGoogleLoginSuccess = (response: any) => {
        console.log('Google login success:', response);
    };

    const handleGoogleLoginError = (error: any) => {
        console.error('Google login error:', error);
    };

    return (
        <Box
            sx={{
                background: 'rgba(0, 0, 0, 0.5)', // Более светлый фон модального окна
                minHeight: '100vh',
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                p: 2,
            }}
        >
            <Card
                className="registration-card"
                sx={{
                    maxWidth: 400,
                    width: '100%',
                    borderRadius: 4,
                    boxShadow: 6,
                    backgroundColor: '#ffffff', // Белый фон для формы
                }}
            >
                <CardContent>
                    <Typography
                        variant="h5"
                        align="center"
                        sx={{ fontWeight: 'bold', color: '#333', mb: 2 }}
                    >
                        Create Your Account
                    </Typography>
                    <Typography
                        variant="body2"
                        align="center"
                        sx={{ color: '#555', mb: 4 }}
                    >
                        Join us to explore personalized health solutions.
                    </Typography>
                    <Box
                        component="form"
                        noValidate
                        autoComplete="off"
                        onSubmit={handleSubmit}
                    >
                        <TextField
                            fullWidth
                            label="Name"
                            variant="outlined"
                            margin="dense"
                            required
                            sx={{ mb: 2 }}
                        />
                        <TextField
                            fullWidth
                            label="Email"
                            variant="outlined"
                            margin="dense"
                            type="email"
                            required
                            sx={{ mb: 2 }}
                        />
                        <TextField
                            fullWidth
                            label="Password"
                            variant="outlined"
                            margin="dense"
                            type="password"
                            required
                            sx={{ mb: 2 }}
                        />
                        <TextField
                            fullWidth
                            label="Confirm Password"
                            variant="outlined"
                            margin="dense"
                            type="password"
                            required
                            sx={{ mb: 3 }}
                        />
                        <Button
                            fullWidth
                            variant="contained"
                            color="primary"
                            size="large"
                            type="submit"
                            sx={{
                                fontWeight: 'bold',
                                mb: 2,
                                py: 1.5,
                            }}
                        >
                            Register
                        </Button>
                    </Box>
                    <Divider sx={{ my: 2 }}>OR</Divider>
                    <Box sx={{ textAlign: 'center', mb: 2 }}>
                        <GoogleLogin
                            onSuccess={handleGoogleLoginSuccess}
                            onError={handleGoogleLoginError}
                            size="large"
                            width="100%"
                        />
                    </Box>
                    <Typography
                        align="center"
                        variant="body2"
                        sx={{ mt: 2, color: '#555' }}
                    >
                        Already have an account?{' '}
                        <MuiLink component={Link} to="/login" underline="hover">
                            Sign In
                        </MuiLink>
                    </Typography>
                </CardContent>
            </Card>
        </Box>
    );
};

export default RegistrationForm;
