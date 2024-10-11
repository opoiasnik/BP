import React, { useState } from 'react';
import './ChatItem.css';

interface ChatItemProps {
    index: number;
    onMouseDownEvent: (index: number, e: React.MouseEvent) => void;
    onMouseUpEvent: (index: number, e: React.MouseEvent) => void;
    onMouseMoveEvent: (index: number, e: React.MouseEvent) => void;
}
const ChatItem: React.FC<ChatItemProps> = ({index, onMouseDownEvent, onMouseMoveEvent, onMouseUpEvent}) => {


    return (

        <div className={"chat-list-item"}
            onMouseDown={(event) => onMouseDownEvent(index, event)}
             onMouseMove={(event) => onMouseMoveEvent(index, event)}
             onMouseUp={(event ) => onMouseUpEvent(index, event)}
        >
            Chat {index}
        </div>


    );
};
export default ChatItem;