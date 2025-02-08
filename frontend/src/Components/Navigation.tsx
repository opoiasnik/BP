import React, { useEffect, useState } from 'react'
import { IoMdHome } from "react-icons/io";
import { GoHistory } from "react-icons/go";
import { Link } from 'react-router-dom';
import { MdOutlineDarkMode } from "react-icons/md";
import { CiLight } from "react-icons/ci";
import IconButton from '@mui/material/IconButton';
import Avatar from '@mui/material/Avatar';
import { CgLogIn } from "react-icons/cg";
import BackImage from '../assets/smallheadicon.png'

export interface NavigationItem {
    icon: React.ReactNode,
    title: string,
    link: string
}

const NavigationItems: NavigationItem[] = [
    {
        title: 'Dashboard',
        link: '/dashboard',
        icon: <IoMdHome size={30} />
    },
    {
        title: 'History',
        link: '/dashboard/history',
        icon: <GoHistory size={25} />
    }
]

interface NavigationProps {
    isExpanded: boolean,
}

const Navigation = ({ isExpanded = false }: NavigationProps) => {
    const [theme, setTheme] = useState<'dark' | 'light'>('light')

    useEffect(() => {
        if (window.matchMedia('(prefers-color-scheme:dark)').matches) {
            setTheme('dark');
        } else {
            setTheme('light')
        }
    }, [])

    useEffect(() => {
        if (theme === "dark") {
            document.documentElement.classList.add("dark");
        } else {
            document.documentElement.classList.remove("dark");
        }
    }, [theme])

    const handleThemeSwitch = () => {
        setTheme(theme === "dark" ? "light" : "dark")
    }

    // Загружаем данные пользователя из localStorage (если имеются)
    const [user, setUser] = useState<any>(null);
    useEffect(() => {
        const storedUser = localStorage.getItem('user');
        if (storedUser) {
            setUser(JSON.parse(storedUser));
        }
    }, []);

    return (
        <div className='h-full p-3 w-fit'>
            <div className='h-full rounded-xl border flex flex-col px-1 justify-between py-2 items-center dark:bg-slate-300 shadow-xl'>
                <div className='flex flex-col items-start gap-12'>
                    <Link to='/' className='w-full flex items-center justify-center'>
                        <IconButton sx={{ width: 40, height: 40 }}>
                            <img src={BackImage} width={25} alt="" />
                        </IconButton>
                        {isExpanded && (
                            <p className='text-2xl font-semibold text-dark-blue flex items-center'>
                                Health AI
                            </p>
                        )}
                    </Link>
                    <div className='flex flex-col p-1 gap-5 items-center'>
                        {NavigationItems.map((item) => (
                            <Link key={item.link} to={item.link} className='flex gap-2 items-center w-full'>
                                <IconButton
                                    sx={{
                                        width: 40,
                                        height: 40,
                                        borderRadius: 2,
                                        backgroundColor: '#FFFFFF',
                                        ...(theme === 'dark' && {
                                            '&:hover': {
                                                backgroundColor: '#eef3f4',
                                                borderColor: '#0062cc',
                                                boxShadow: 'none',
                                            },
                                        }),
                                    }}
                                >
                                    {item.icon}
                                </IconButton>
                                {isExpanded && item.title}
                            </Link>
                        ))}
                    </div>
                </div>
                {/* Блок с иконкой пользователя и переключателем темы */}
                <div className="flex flex-col items-center gap-2">
                    <Link to={user ? '/profile' : '/login'} className="flex items-center">
                        <IconButton
                            sx={{
                                width: 40,
                                height: 40,
                                borderRadius: 2,
                                backgroundColor: '#FFFFFF',
                            }}
                        >
                            {user ? (
                                <Avatar alt={user.name} src={user.picture} />
                            ) : (
                                <CgLogIn size={24} />
                            )}
                        </IconButton>
                    </Link>
                    <button onClick={handleThemeSwitch} className='flex items-center gap-2'>
                        <IconButton
                            sx={{
                                width: 40,
                                height: 40,
                                borderRadius: 2,
                                background: theme === 'dark' ? 'white' : 'initial',
                                '&:focus-visible': {
                                    outline: '2px solid blue', // Кастомный стиль фокуса
                                    outlineOffset: '0px',
                                    borderRadius: '4px',
                                },
                            }}
                        >
                            {theme === 'light' ? <CiLight size={30} /> : <MdOutlineDarkMode size={30} />}
                        </IconButton>
                        {isExpanded && (theme === 'light' ? 'Light mode' : 'Dark mode')}
                    </button>
                </div>
            </div>
        </div>
    )
}

export default Navigation;
