import { BrowserRouter as Router, Route, Routes, Outlet } from 'react-router-dom';
import Navigation from './Components/Navigation';
import HomePage from './pages/HomePage';
import LandingPage from './pages/LandingPage';


const Layout = () => (
  <div className="flex w-full h-screen dark:bg-slate-200">
    <Navigation isExpanded={false} />
    <div className="flex-grow p-3 h-full">
      <main className="h-full w-full border rounded-xl dark:bg-slate-100 shadow-xl" >
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
        <Route path="solutions" element={<>Sorry not implemented yet</>} />
        <Route path="contact" element={<>Sorry not implemented yet</>} />
        <Route path="about" element={<>Sorry not implemented yet</>} />
        <Route path="/dashboard" element={<Layout />}>
          <Route index element={<HomePage />} />
          <Route path="history" element={<>Sorry not implemented yet</>} />
        </Route>
      </Routes>
    </Router>
  )
}

export default App

