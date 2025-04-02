import React from 'react';
import { GoogleLogin, GoogleOAuthProvider } from '@react-oauth/google';
import { Link, useNavigate } from 'react-router-dom';

const CLIENT_ID = "532143017111-4eqtlp0oejqaovj6rf5l1ergvhrp4vao.apps.googleusercontent.com";

const RegistrationFormContent: React.FC = () => {
    const navigate = useNavigate();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        const nameElement = document.getElementById('name') as HTMLInputElement | null;
        const emailElement = document.getElementById('email') as HTMLInputElement | null;
        const passwordElement = document.getElementById('password') as HTMLInputElement | null;
        const confirmPasswordElement = document.getElementById('confirm-password') as HTMLInputElement | null;

        if (!nameElement || !emailElement || !passwordElement || !confirmPasswordElement) {
            console.error('One or more input fields are missing');
            return;
        }

        const name = nameElement.value;
        const email = emailElement.value;
        const password = passwordElement.value;
        const confirmPassword = confirmPasswordElement.value;

        if (password !== confirmPassword) {
            console.error('Passwords do not match');
            alert('Passwords do not match');
            return;
        }

        try {
            const response = await fetch('http://localhost:5000/api/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, email, password }),
            });

            const data = await response.json();

            if (response.ok) {
                console.log('User registered successfully:', data.message);
                const loggedInUser = {
                    name,
                    email,
                    picture: 'https://via.placeholder.com/150',
                };
                localStorage.setItem('user', JSON.stringify(loggedInUser));
                navigate('/dashboard');
            } else {
                console.error('Error:', data.error);
                alert(data.error);
            }
        } catch (error) {
            console.error('Error registering user:', error);
            alert('Error registering user');
        }
    };

    const handleGoogleLoginSuccess = async (response: any) => {
        try {
            const res = await fetch('http://localhost:5000/api/verify', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ token: response.credential }),
            });
            const data = await res.json();
            const loggedInUser = {
                name: data.user.name,
                email: data.user.email,
                picture: data.user.picture || 'https://via.placeholder.com/150',
            };
            localStorage.setItem('user', JSON.stringify(loggedInUser));
            navigate('/dashboard');
        } catch (error) {
            console.error('Error tiken verification:', error);
        }
    };

    const handleGoogleLoginError = () => {
        console.error('Error auth: Google login failed');
    };


    return (
        <div
            style={{
                background: 'rgba(0, 0, 0, 0.5)',
                minHeight: '100vh',
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                padding: '16px',
            }}
        >
            <div
                className="registration-card"
                style={{
                    maxWidth: '400px',
                    width: '100%',
                    borderRadius: '8px',
                    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
                    backgroundColor: '#fff',
                    padding: '24px',
                }}
            >
                <h2 style={{ textAlign: 'center', fontWeight: 'bold', color: '#333', marginBottom: '16px' }}>
                    Create Your Account
                </h2>
                <p style={{ textAlign: 'center', color: '#555', marginBottom: '24px' }}>
                    Join us to explore personalized health solutions.
                </p>
                <form noValidate autoComplete="off" onSubmit={handleSubmit}>
                    <div style={{ marginBottom: '16px' }}>
                        <label htmlFor="name" style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>
                            Name
                        </label>
                        <input
                            type="text"
                            id="name"
                            required
                            style={{
                                width: '100%',
                                padding: '8px',
                                borderRadius: '4px',
                                border: '1px solid #ccc',
                            }}
                        />
                    </div>
                    <div style={{ marginBottom: '16px' }}>
                        <label htmlFor="email" style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>
                            Email
                        </label>
                        <input
                            type="email"
                            id="email"
                            required
                            style={{
                                width: '100%',
                                padding: '8px',
                                borderRadius: '4px',
                                border: '1px solid #ccc',
                            }}
                        />
                    </div>
                    <div style={{ marginBottom: '16px' }}>
                        <label htmlFor="password" style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>
                            Password
                        </label>
                        <input
                            type="password"
                            id="password"
                            required
                            style={{
                                width: '100%',
                                padding: '8px',
                                borderRadius: '4px',
                                border: '1px solid #ccc',
                            }}
                        />
                    </div>
                    <div style={{ marginBottom: '24px' }}>
                        <label
                            htmlFor="confirm-password"
                            style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}
                        >
                            Confirm Password
                        </label>
                        <input
                            type="password"
                            id="confirm-password"
                            required
                            style={{
                                width: '100%',
                                padding: '8px',
                                borderRadius: '4px',
                                border: '1px solid #ccc',
                            }}
                        />
                    </div>
                    <button
                        type="submit"
                        style={{
                            width: '100%',
                            padding: '12px',
                            backgroundColor: '#007bff',
                            color: '#fff',
                            fontWeight: 'bold',
                            borderRadius: '4px',
                            border: 'none',
                            cursor: 'pointer',
                            marginBottom: '16px',
                        }}
                    >
                        Register
                    </button>
                </form>
                <div
                    style={{
                        textAlign: 'center',
                        marginBottom: '16px',
                        color: '#555',
                        fontSize: '14px',
                        borderBottom: '1px solid #ccc',
                        lineHeight: '0.1em',
                        margin: '10px 0 20px',
                    }}
                >
                    <span style={{ background: '#fff', padding: '0 10px' }}>OR</span>
                </div>
                <div style={{ textAlign: 'center', marginBottom: '16px' }}>
                    <GoogleLogin
                        onSuccess={handleGoogleLoginSuccess}
                        onError={handleGoogleLoginError}
                        size="large"
                        width="100%"
                    />
                </div>
                <p style={{ textAlign: 'center', color: '#555', marginTop: '16px' }}>
                    Already have an account?{' '}
                    <Link to="/login" style={{ color: '#007bff', textDecoration: 'none' }}>
                        Sign In
                    </Link>
                </p>
            </div>
        </div>
    );
};

const RegistrationForm: React.FC = () => {
    return (
        <GoogleOAuthProvider clientId={CLIENT_ID}>
            <RegistrationFormContent />
        </GoogleOAuthProvider>
    );
};

export default RegistrationForm;
