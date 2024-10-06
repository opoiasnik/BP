import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Chat from "../Chat/Chat";
import MainPage from "../MainPage/MainPage";

export default function Router(){
    return(
        <BrowserRouter>
            <Routes>
                <Route path="/" element={<MainPage />} />
                <Route path="Chat" element={<Chat></Chat>}></Route>
            </Routes>
        </BrowserRouter>
    )
}