import { BrowserRouter as Router, Route, Routes, Outlet } from 'react-router-dom';
import Navigation from './Components/Navigation';
import {Home} from './pages/LandingPage';
import RegistrationForm from "./Components/RegistrationForm";
import LoginForm from "./Components/LoginForm";
import ChatHistory from "./Components/ChatHistory";
import HomePage from './pages/HomePage';
import NewChatPage from "./Components/NewChatPage";
import About from "./Components/About.tsx";
import Contact from "./Components/Contact.tsx";
import Profile from "./Components/Profile.tsx";

const Layout = () => (
    <div className="flex w-full h-screen dark:bg-slate-200">
        <Navigation isExpanded={false} />
        <div className="flex-grow p-3 h-full">
            <main className="h-full w-full border rounded-xl dark:bg-slate-100 shadow-xl">
                <Outlet />
            </main>
        </div>
    </div>
);

function App() {
    return (
        <Router>
            <Routes>
                <Route path="/" element={<Home />} />
                <Route path="/register" element={<RegistrationForm />} />
                <Route path="/login" element={<LoginForm />} />
                <Route path="/contact" element={<Contact />} />
                <Route path="/profile" element={<Profile />} />
                <Route path="/about" element={<About />} />
                <Route path="/dashboard" element={<Layout />}>
                    <Route path="new-chat" element={<NewChatPage />} />
                    <Route path="chat/:id" element={<HomePage />} />
                    <Route path="history" element={<ChatHistory />} />
                    <Route index element={<HomePage />} />
                </Route>
            </Routes>
        </Router>
    );
}

export default App;
