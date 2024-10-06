import React, { useEffect, useRef } from "react";
import { Link } from "react-router-dom";
import { gsap } from "gsap";
import './Header.css';

export default function Header() {
    const headerRef = useRef<HTMLElement | null>(null);

    useEffect(() => {
        if (headerRef.current) {
            gsap.fromTo(headerRef.current, { opacity: 0, y: -50 }, { opacity: 1, y: 0, duration: 1, ease: "power4.out" });
        }
    }, []);

    return (
        <header ref={headerRef} className="header">
            <div className="logo">
                <h2>Medical AI Assistant</h2>
            </div>
            <nav className="nav-header">
                <ul>
                    <li><Link to="/login">Log In</Link></li>
                    <li><Link to="/signup">Sign Up</Link></li>
                    <li><Link to="/about">About Us</Link></li>
                    <li><Link to="/services">Services</Link></li>
                    <li><Link to="/contact">Contact</Link></li>
                </ul>
            </nav>
        </header>
    );
}
