import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import Router from '../src/Router/Router';
import reportWebVitals from './reportWebVitals';

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);
root.render(
  <React.StrictMode>
    <Router />
  </React.StrictMode>
);

reportWebVitals();
