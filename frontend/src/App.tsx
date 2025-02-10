import { BrowserRouter as Router, Route, Routes, Outlet } from 'react-router-dom';
import Navigation from './Components/Navigation';
import HomePage from './pages/HomePage';
import LandingPage from './pages/LandingPage';
import RegistrationForm from "./Components/RegistrationForm.tsx";
import LoginForm from "./Components/LoginForm.tsx";
import ChatHistory from "./Components/ChatHistory.tsx";
import ChatDetails from "./Components/ChatDetails.tsx";

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
                <Route path='/' element={<LandingPage />} />
                <Route path="/register" element={<RegistrationForm />} />
                <Route path="/login" element={<LoginForm />} />
                <Route path="solutions" element={<>Sorry not implemented yet</>} />
                <Route path="contact" element={<>Sorry not implemented yet</>} />
                <Route path="about" element={<>Sorry not implemented yet</>} />
                <Route path="/dashboard" element={<Layout />}>
                    <Route index element={<HomePage />} />
                    <Route path="history" element={<ChatHistory />} />
                    <Route path="chat/:id" element={<ChatDetails />} />
                </Route>
            </Routes>
        </Router>
    );
}

export default App;
