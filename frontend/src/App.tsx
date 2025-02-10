import { BrowserRouter as Router, Route, Routes, Outlet } from 'react-router-dom';
import Navigation from './Components/Navigation';
import LandingPage from './pages/LandingPage';
import RegistrationForm from "./Components/RegistrationForm";
import LoginForm from "./Components/LoginForm";
import ChatHistory from "./Components/ChatHistory";
import HomePage from './pages/HomePage';
import NewChatPage from "./Components/NewChatPage";

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
                <Route path="/" element={<LandingPage />} />
                <Route path="/register" element={<RegistrationForm />} />
                <Route path="/login" element={<LoginForm />} />
                <Route path="/dashboard" element={<Layout />}>
                    {/* Новый чат */}
                    <Route path="new-chat" element={<NewChatPage />} />
                    {/* Существующий чат (после создания нового, URL обновится) */}
                    <Route path="chat/:id" element={<HomePage />} />
                    <Route path="history" element={<ChatHistory />} />
                    <Route index element={<HomePage />} />
                </Route>
            </Routes>
        </Router>
    );
}

export default App;
