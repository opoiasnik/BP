// @ts-ignore
import React, { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { gsap } from "gsap";
import Header from "../Header/Header";
// @ts-ignore
import smiley from '../Images/clipart1366776.png';
import { Snackbar, Button } from '@mui/material';
import './MainPage.css';

export default function MainPage() {
    const titleRef = useRef<HTMLHeadingElement | null>(null);
    const textRef = useRef<HTMLParagraphElement | null>(null);
    const buttonRef = useRef<HTMLDivElement | null>(null);
    const leftEyeRef = useRef<HTMLDivElement | null>(null);
    const rightEyeRef = useRef<HTMLDivElement | null>(null);
    const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
    const [openSnackbar, setOpenSnackbar] = useState(false);
    const [chatEnabled, setChatEnabled] = useState(false);
    const navigate = useNavigate();

    useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await fetch("/featureFlags.json");
                const data = await response.json();
                setChatEnabled(data.isChatEnabled);
            } catch (error) {
                console.error("Error featureFlags.json:", error);
            }
        };

        fetchData();
        if (titleRef.current) {
            gsap.fromTo(titleRef.current, { opacity: 0, y: -50 }, { opacity: 1, y: 0, duration: 1.5, ease: "power4.out" });
        }

        if (textRef.current) {
            gsap.fromTo(textRef.current, { opacity: 0, y: 50 }, { opacity: 1, y: 0, duration: 2, delay: 0.5, ease: "power4.out" });
        }

        if (buttonRef.current) {
            gsap.fromTo(buttonRef.current, { opacity: 0, y: 50 }, { opacity: 1, y: 0, duration: 2, delay: 0.8, ease: "power4.out" });
        }

        const handleMouseMove = (event: MouseEvent) => {
            setMousePos({ x: event.clientX, y: event.clientY });
        };

        window.addEventListener("mousemove", handleMouseMove);

        return () => {
            window.removeEventListener("mousemove", handleMouseMove);
        };
    }, []);

    const calculateEyeMovement = (eyeRef: React.RefObject<HTMLDivElement>, offsetX: number, offsetY: number) => {
        if (eyeRef.current) {
            const eye = eyeRef.current;
            const eyeX = eye.getBoundingClientRect().left + eye.offsetWidth / 2;
            const eyeY = eye.getBoundingClientRect().top + eye.offsetHeight / 2;

            const angle = Math.atan2(mousePos.y - eyeY, mousePos.x - eyeX);
            const distance = 10;

            const moveX = Math.cos(angle) * distance;
            const moveY = Math.sin(angle) * distance;

            eye.style.transform = `translate(${moveX + offsetX}px, ${moveY + offsetY}px)`;
        }
    };

    useEffect(() => {
        calculateEyeMovement(leftEyeRef, -10, 0);
        calculateEyeMovement(rightEyeRef, 10, 0);
    }, [mousePos]);

    const handleTryChatClick = () => {
        chatEnabled ? navigate('/Chat'): setOpenSnackbar(true);
    };

    const handleCloseSnackbar = (event?: React.SyntheticEvent | Event, reason?: string) => {
        if (reason === 'clickaway') {
            return;
        }
        setOpenSnackbar(false);
    };

    const waveText = "Welcome to the Medical AI Assistant!".split("").map((char, index) => (
        <span key={index} className="wave-text" style={{ animationDelay: `${index * 0.1}s` }}>
            {char === " " ? "\u00A0" : char}
        </span>
    ));

    useEffect(() => {
        const startWaveAnimation = () => {
            const letters = document.querySelectorAll('.wave-text');
            letters.forEach((letter, index) => {
                (letter as HTMLElement).style.animation = 'none';

                // Перезапускаем анимацию
                setTimeout(() => {
                    (letter as HTMLElement).style.animation = `wave 1s ease-in-out ${index * 0.1}s`;
                }, 10);
            });
        };

        const intervalId = setInterval(() => {
            startWaveAnimation();
        }, 10000);

        startWaveAnimation();
        return () => clearInterval(intervalId);
    }, []);

    return (
        <>
            <Header />
            <div className="main-content">
                <h1 ref={titleRef} className="wave-text-container">{waveText}</h1>
                <p ref={textRef} className="intro-text">
                    Your personal assistant in the world of healthcare and pharmaceuticals. We are here to help you find reliable information about medicines, healthcare, and more.
                </p>
                <div className="try-chat-container" ref={buttonRef}>
                    <Button variant="contained" color="primary" onClick={handleTryChatClick}>
                        TRY CHAT
                    </Button>
                </div>
            </div>
            <div className="smiley-container">
                <img src={smiley} alt="Smiley" className="smiley" />
                <div className="eye left-eye" ref={leftEyeRef}></div>
                <div className="eye right-eye" ref={rightEyeRef}></div>
            </div>

            <Snackbar
                open={openSnackbar}
                autoHideDuration={3000}
                onClose={handleCloseSnackbar}
                message="Chat is not available right now"
            />
        </>
    );
}
