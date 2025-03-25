import React, { useEffect, useState } from 'react';
import {
    Box,
    Typography,
    Avatar,
    Paper,
    Button,
    TextField,
    IconButton,
    Divider
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { Navbar } from '../pages/LandingPage';
import CheckIcon from '@mui/icons-material/Check';
import CloseIcon from '@mui/icons-material/Close';

const Profile: React.FC = () => {
    const [user, setUser] = useState<any>(null);
    const [editing, setEditing] = useState<boolean>(false);
    const [formData, setFormData] = useState({
        name: '',
        email: '',
        phone: '',
        role: '',
        bio: '',
        picture: '',
    });
    const navigate = useNavigate();

    useEffect(() => {
        const storedUser = localStorage.getItem('user');
        if (storedUser) {
            const parsedUser = JSON.parse(storedUser);
            setUser(parsedUser);
            setFormData({
                name: parsedUser.name || '',
                email: parsedUser.email || '',
                phone: parsedUser.phone || '',
                role: parsedUser.role || '',
                bio: parsedUser.bio || '',
                picture: parsedUser.picture || '',
            });
        } else {
            navigate('/login');
        }
    }, [navigate]);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setFormData(prev => ({
            ...prev,
            [e.target.name]: e.target.value,
        }));
    };

    const handleCancelEdit = () => {
        // Reset formData to original user values
        setFormData({
            name: user.name || '',
            email: user.email || '',
            phone: user.phone || '',
            role: user.role || '',
            bio: user.bio || '',
            picture: user.picture || '',
        });
        setEditing(false);
    };

    const handleSaveEdit = async () => {
        try {
            const response = await fetch('http://localhost:5000/api/update_profile', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData),
            });
            const data = await response.json();
            if (response.ok) {
                const updatedUser = { ...user, ...formData };
                setUser(updatedUser);
                localStorage.setItem('user', JSON.stringify(updatedUser));
                setEditing(false);
            } else {
                alert(data.error || 'Error updating profile');
            }
        } catch (err) {
            console.error(err);
            alert('Error updating profile');
        }
    };

    if (!user) {
        return null;
    }

    return (
        <Box
            sx={{
                minHeight: '100vh',
                background: 'linear-gradient(to right, #d0e7ff, #f0f8ff)',
                display: 'flex',
                flexDirection: 'column',
            }}
        >
            <Navbar user={user} setUser={setUser} />
            <Box
                sx={{
                    flexGrow: 1,
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                    p: 4,
                }}
            >
                <Paper
                    elevation={3}
                    sx={{
                        p: 4,
                        borderRadius: '12px',
                        maxWidth: '500px',
                        width: '100%',
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                    }}
                >
                    <Avatar
                        src={user.picture}
                        alt={user.name}
                        sx={{ width: 100, height: 100, mb: 2 }}
                    />
                    {editing ? (
                        <>
                            <TextField
                                label="Name"
                                name="name"
                                value={formData.name}
                                onChange={handleChange}
                                fullWidth
                                sx={{ mb: 2 }}
                            />
                            <TextField
                                label="Email"
                                name="email"
                                value={formData.email}
                                fullWidth
                                sx={{ mb: 2 }}
                                disabled
                            />
                            <TextField
                                label="Phone"
                                name="phone"
                                value={formData.phone}
                                onChange={handleChange}
                                fullWidth
                                sx={{ mb: 2 }}
                            />
                            <TextField
                                label="Role"
                                name="role"
                                value={formData.role}
                                onChange={handleChange}
                                fullWidth
                                sx={{ mb: 2 }}
                            />
                            <TextField
                                label="Bio"
                                name="bio"
                                value={formData.bio}
                                onChange={handleChange}
                                fullWidth
                                multiline
                                rows={3}
                                sx={{ mb: 2 }}
                            />
                            <TextField
                                label="Picture URL"
                                name="picture"
                                value={formData.picture}
                                onChange={handleChange}
                                fullWidth
                                sx={{ mb: 2 }}
                            />
                            <Box
                                sx={{
                                    display: 'flex',
                                    justifyContent: 'space-around',
                                    width: '100%',
                                    mt: 2,
                                }}
                            >
                                <IconButton onClick={handleSaveEdit} color="primary">
                                    <CheckIcon />
                                </IconButton>
                                <IconButton onClick={handleCancelEdit} color="error">
                                    <CloseIcon />
                                </IconButton>
                            </Box>
                        </>
                    ) : (
                        <>
                            <Typography
                                variant="h5"
                                sx={{ fontWeight: 'bold', color: '#0d47a1', mb: 1 }}
                            >
                                {user.name}
                            </Typography>
                            <Typography variant="body1" sx={{ color: '#424242', mb: 2 }}>
                                {user.email}
                            </Typography>
                            <Divider sx={{ width: '100%', mb: 2 }} />
                            <Typography variant="body1" sx={{ color: '#424242', mb: 1 }}>
                                <strong>Phone:</strong> {user.phone || 'Not provided'}
                            </Typography>
                            <Typography variant="body1" sx={{ color: '#424242', mb: 1 }}>
                                <strong>Role:</strong> {user.role || 'User'}
                            </Typography>
                            <Typography variant="body1" sx={{ color: '#424242', mb: 1 }}>
                                <strong>Bio:</strong> {user.bio || 'No bio available'}
                            </Typography>
                            <Button
                                variant="contained"
                                sx={{ mt: 3, backgroundColor: '#0d47a1' }}
                                onClick={() => setEditing(true)}
                            >
                                Edit Profile
                            </Button>
                        </>
                    )}
                </Paper>
            </Box>
        </Box>
    );
};

export default Profile;
