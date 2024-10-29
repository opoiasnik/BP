import React from 'react';
import { CgLogIn } from "react-icons/cg";
import { Link } from 'react-router-dom';
import BackImage from '../assets/smallheadicon.png'
import MultiStepForm from '../Components/MultistepForm';
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward';
import { Box } from '@mui/material';
import gsap from 'gsap';
import { useGSAP } from '@gsap/react';

const BouncingArrow = () => {
    return (
        <Box
            sx={{
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                mt: 2,
                animation: 'bounce 1s infinite', // Додаємо анімацію
                '@keyframes bounce': { // Описуємо ключові кадри для анімації
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
const Navbar: React.FC = () => {
    return (
        <nav className="w-full bg-white shadow-md py-4 px-2 sm:px-8 flex justify-between items-center fixed top-0 left-0 right-0 z-50">
            <div className="text-2xl font-semibold text-dark-blue flex items-center">
                Health AI
                <img src={BackImage} width={25} alt="" />
            </div>
            <ul className="flex space-x-6 text-gray-600">
                <li><Link to="/dashboard" className="hover:text-bright-blue transition duration-300">Home</Link></li>
                <li><Link to="/solutions" className="hover:text-bright-blue transition duration-300">Solutions</Link></li>
                <li><Link to="/about" className="hover:text-bright-blue transition duration-300">About</Link></li>
                <li><Link to="/contact" className="hover:text-bright-blue transition duration-300">Contact</Link></li>
            </ul>
            <div className='flex gap-2 items-center'>
                Sign in <CgLogIn size={25} />
            </div>
        </nav>
    );
};

const Home: React.FC = () => {

    useGSAP(() => {
        gsap.from('#mainheading', { opacity: 0.3, ease: 'power2.inOut', duration: 0.5 })
        gsap.from('#secondheading', { opacity: 0, y: 5, ease: 'power2.inOut', delay: 0.3, duration: 0.5 })
        gsap.from('#button', { opacity: 0, y: 5, ease: 'power2.inOut', delay: 0.5, duration: 0.5 })
        gsap.from('#features', { opacity: 0, y: 5, ease: 'power2.inOut', delay: 0.7, duration: 0.5 })
        gsap.from('#arrow', { opacity: 0, ease: 'power2.inOut', delay: 2, duration: 0.2 })
    }, [])

    return (<>
        <div className="h-screen flex flex-col items-center justify-center bg-gradient-to-b text-gray-800 p-4">
            {/* Навігація */}
            <Navbar />

            <div className="pt-20 flex flex-col items-center">
                <h1 id='mainheading' className="text-4xl flex items-center sm:text-5xl md:text-6xl font-semibold mb-4 text-center text-dark-blue">
                    AI Assistant for Your Health
                </h1>

                <p id='secondheading' className="text-base sm:text-lg md:text-xl text-center max-w-2xl mb-8 text-gray-700">
                    The product for health improvement, trainings, and other. Care for yourself with modern technologies – be a modern human.
                </p>

                <Link id='button' to='/dashboard'>
                    <button  className="bg-bright-blue text-white font-medium py-2 px-5 rounded hover:bg-deep-blue transition duration-300 mb-10 shadow-md">
                        Get started
                    </button>
                </Link>

                <div className="flex flex-col sm:flex-row gap-6 mb-10" id="features">
                    <div className="bg-white p-6 rounded-lg max-w-xs text-center shadow-md">
                        <h3 className="text-xl font-medium mb-3 text-dark-blue">Personalized Training</h3>
                        <p className="text-gray-600">Get customized training plans designed just for you and track your progress effectively.</p>
                    </div>
                    <div className="bg-white p-6 rounded-lg max-w-xs text-center shadow-md">
                        <h3 className="text-xl font-medium mb-3 text-dark-blue">Health Monitoring</h3>
                        <p className="text-gray-600">Stay informed about your health with real-time monitoring and AI-driven insights.</p>
                    </div>
                    <div className="bg-white p-6 rounded-lg max-w-xs text-center shadow-md">
                        <h3 className="text-xl font-medium mb-3 text-dark-blue">Advanced AI Support</h3>
                        <p className="text-gray-600">Utilize AI support to ensure you're following the best routines for a healthier lifestyle.</p>
                    </div>
                </div>

                <div id='arrow' className='flex flex-col items-center mt-10 z-0'>
                    <p className='text-gray-600'>Try it out</p>
                    <BouncingArrow />
                </div>
            </div>


        </div>
        <div className='w-full h-screen flex flex-col justify-center items-center' >

            <MultiStepForm />

        </div>
        <footer className=" mt-auto text-center text-gray-500 p-4">
            <p>&copy; {new Date().getFullYear()} Health AI. All rights reserved.</p>
        </footer>
    </>
    );
};


export default Home;

