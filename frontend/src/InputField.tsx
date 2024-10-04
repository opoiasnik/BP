import React, { useState } from 'react';

interface InputFieldProps {
    onSend: (message: string) => void;
}

const InputField: React.FC<InputFieldProps> = ({ onSend }) => {
    const [inputValue, setInputValue] = useState('');

    const handleSend = () => {
        if (inputValue.trim() !== '') {
            onSend(inputValue);
            setInputValue('');
        }
    };

    return (
        <div className="input-field">
            <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder="Введите сообщение..."
                onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            />
            <button onClick={handleSend}>Отправить</button>
        </div>
    );
};

export default InputField;
