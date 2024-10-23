// Message.tsx
import React from 'react';

interface MessageProps {
    content: string;
    role: 'user' | 'assistant';
    rating?: number;
    explanation?: string;
}
const Message: React.FC<MessageProps> = ({ content, role, rating, explanation }) => {
    return (
        <div className={`message ${role}`}>
            <div className="message-content">
                <p dangerouslySetInnerHTML={{ __html: content.replace(/\n/g, '<br/>') }}></p>
            </div>
            {rating !== undefined && rating !== null && (
                <div className="evaluation">
                    <p>
                        <strong>Оценка:</strong> {rating}
                    </p>
                    {explanation && (
                        <p>
                            <strong>Объяснение:</strong> {explanation}
                        </p>
                    )}
                </div>
            )}
        </div>
    );
};


export default Message;
