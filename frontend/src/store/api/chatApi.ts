import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react"


// type chatQuestion = {

// }

const chatApi = createApi({
    reducerPath: 'chat',
    baseQuery: fetchBaseQuery({ baseUrl: 'http://localhost:5000' }),
    endpoints: (builder) => ({
        sendTestVersion: builder.query<string, any>({
            query: (body) => ({
                url: '/create-answer',
                method: 'POST',
                body: body
            }),
            transformResponse: ({ response }) => response
        }),
        sendChatQuestion: builder.query<any, any>({
            query: (body) => ({
                url: '/api/chat',
                method: 'POST',
                body: body
            })
        })
    })
})



export default chatApi
export const { useLazySendTestVersionQuery,useLazySendChatQuestionQuery } = chatApi
