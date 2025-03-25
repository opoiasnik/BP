import React, { useState, useEffect } from 'react';
import { CgLogIn } from "react-icons/cg";
import BackImage from '../assets/smallheadicon.png';
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward';
import { Box, Button, Avatar, Modal, Typography } from '@mui/material';
import gsap from 'gsap';
import { useGSAP } from '@gsap/react';
import LogoutIcon from '@mui/icons-material/Logout';
import LoginIcon from '@mui/icons-material/Login';
import { GoogleOAuthProvider, GoogleLogin } from '@react-oauth/google';
import { Link, useNavigate } from 'react-router-dom';
import RegistrationForm from "../Components/RegistrationForm";

const CLIENT_ID = "532143017111-4eqtlp0oejqaovj6rf5l1ergvhrp4vao.apps.googleusercontent.com";

// Компонент для анимации стрелки вниз
const BouncingArrow = () => {
    return (
        <Box
            sx={{
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                mt: 2,
                animation: 'bounce 1s infinite',
                '@keyframes bounce': {
                    '0%, 100%': {
                        transform: 'translateY(0)',
                    },
                    '50%': {
                        transform: 'translateY(-10px)',
                    },
                }
            }}
        >
            <ArrowDownwardIcon fontSize="large" />
        </Box>
    );
};

interface NavbarProps {
    user: any;
    setUser: (user: any) => void;
}

const Navbar: React.FC<NavbarProps> = ({ user, setUser }) => {
    const navigate = useNavigate();

    const handleSignOut = () => {
        setUser(null);
        localStorage.removeItem('user');
    };

    return (
        <nav className="w-full bg-white shadow-md py-4 px-2 sm:px-8 flex justify-between items-center fixed top-0 left-0 right-0 z-50">
            <div className="text-2xl font-semibold text-dark-blue flex items-center">
                Health AI
                <img src={BackImage} width={25} alt="Logo" />
            </div>
            <ul className="flex space-x-6 text-gray-600">
                <li>
                    <Link to="/" className="hover:text-bright-blue transition duration-300">
                        Home
                    </Link>
                </li>
                <li>
                    <Link to="/about" className="hover:text-bright-blue transition duration-300">
                        About
                    </Link>
                </li>
                <li>
                    <Link to="/contact" className="hover:text-bright-blue transition duration-300">
                        Contact
                    </Link>
                </li>
            </ul>
            <div className="flex items-center">
                {user ? (
                    <div className="flex items-center gap-2">
                        <Avatar alt={user.name} src={user.picture} onClick={()=>navigate('/profile')} />
                        <LogoutIcon
                            onClick={handleSignOut}
                            sx={{ cursor: 'pointer', color: '#0d47a1', fontSize: '30px' }}
                        />
                    </div>
                ) : (
                    <LoginIcon
                        onClick={() => navigate('/register')}
                        sx={{ cursor: 'pointer', color: '#0d47a1', fontSize: '30px' }}
                    />
                )}
            </div>
        </nav>
    );
};

const Home: React.FC = () => {
    const navigate = useNavigate();
    const [user, setUser] = useState<any>(null);

    // При загрузке страницы пытаемся загрузить данные пользователя из localStorage
    useEffect(() => {
        const storedUser = localStorage.getItem('user');
        if (storedUser) {
            setUser(JSON.parse(storedUser));
        }
    }, []);

    // Анимация GSAP для элементов страницы
    useGSAP(() => {
        gsap.from('#mainheading', { opacity: 0.3, ease: 'power2.inOut', duration: 0.5 });
        gsap.from('#secondheading', { opacity: 0, y: 5, ease: 'power2.inOut', delay: 0.3, duration: 0.5 });
        gsap.from('#button', { opacity: 0, y: 5, ease: 'power2.inOut', delay: 0.5, duration: 0.5 });
        gsap.from('#features', { opacity: 0, y: 5, ease: 'power2.inOut', delay: 0.7, duration: 0.5 });
        gsap.from('#arrow', { opacity: 0, ease: 'power2.inOut', delay: 2, duration: 0.2 });
        gsap.to('#button', { opacity: 1, ease: 'power2.inOut', delay: 2.5, duration: 0.5 });
    }, []);

    // Обработчик нажатия на кнопку "Get started"
    const handleGetStartedClick = () => {
        if (!user) {
            // Если пользователь не авторизован — переходим на страницу регистрации
            navigate('/register');
        } else {
            // Если авторизован — переходим на страницу dashboard
            navigate('/dashboard');
        }
    };

    return (
        <div style={{ backgroundColor: '#d0e7ff' }} className="min-h-screen">
            <div className="h-screen flex flex-col items-center justify-center bg-gradient-to-b text-gray-800 p-4">
                <Navbar user={user} setUser={setUser} />

                <div className="pt-20 flex flex-col items-center">
                    <h1
                        id="mainheading"
                        className="text-4xl flex items-center sm:text-5xl md:text-6xl font-semibold mb-4 text-center text-dark-blue"
                    >
                        AI Assistant for Your Health
                    </h1>

                    <p
                        id="secondheading"
                        className="text-base sm:text-lg md:text-xl text-center max-w-2xl mb-8 text-gray-700"
                    >
                        A solution for personalized health support, including tailored medication guidance and wellness
                        insights. Take care of yourself with the power of modern technology.
                    </p>

                    <div className="flex flex-col sm:flex-row gap-6 mb-10" id="features">
                        <div className="bg-white p-6 rounded-lg max-w-xs text-center shadow-md">
                            <h3 className="text-xl font-medium mb-3 text-dark-blue">Personalized Prescription</h3>
                            <p className="text-gray-600">
                                Receive tailored medication recommendations specifically designed for your needs.
                            </p>
                        </div>
                        <div className="bg-white p-6 rounded-lg max-w-xs text-center shadow-md">
                            <h3 className="text-xl font-medium mb-3 text-dark-blue">Health Monitoring</h3>
                            <p className="text-gray-600">
                                Stay informed about your health with real-time monitoring and AI-driven insights.
                            </p>
                        </div>
                        <div className="bg-white p-6 rounded-lg max-w-xs text-center shadow-md">
                            <h3 className="text-xl font-medium mb-3 text-dark-blue">Advanced AI Support</h3>
                            <p className="text-gray-600">
                                Utilize AI support to ensure you're following the best routines for a healthier lifestyle.
                            </p>
                        </div>
                    </div>

                    <div id="arrow" className="flex flex-col items-center mt-10 z-0">
                        <p className="text-gray-600">Try it out</p>
                        <BouncingArrow />
                    </div>

                    <div id="button-wrapper" className="flex justify-center mt-6">
                        <button
                            id="button"
                            onClick={handleGetStartedClick}
                            className="bg-bright-blue text-white font-medium py-2 px-5 rounded hover:bg-deep-blue transition duration-300 shadow-md"
                        >
                            Get started
                        </button>
                    </div>
                </div>
            </div>

            <footer className="mt-auto text-center text-gray-500 p-4">
                <p>&copy; {new Date().getFullYear()} Health AI. All rights reserved.</p>
            </footer>
        </div>
    );
};

export { Home, Navbar };

