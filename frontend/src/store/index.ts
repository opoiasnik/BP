import { configureStore } from "@reduxjs/toolkit";
import chatApi from "./api/chatApi";
import { setupListeners } from '@reduxjs/toolkit/query';


const store = configureStore({
    reducer: {
        [chatApi.reducerPath]: chatApi.reducer
    },
    middleware: (getDefaultMiddleware) =>
        getDefaultMiddleware().concat(chatApi.middleware),
})

setupListeners(store.dispatch);

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

export default store;