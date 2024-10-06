import React from 'react';

interface MessageProps {
    content: string;
    role: 'user' | 'assistant';
}

const Message: React.FC<MessageProps> = ({ content, role }) => {
    return (
        <div className={`message ${role}`}>
            <p>{content}</p>
        </div>
    );
};

export default Message;
