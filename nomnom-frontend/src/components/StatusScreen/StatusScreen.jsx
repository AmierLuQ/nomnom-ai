import React from 'react';
import './StatusScreen.css'; // <-- FIX: Added the CSS import
import nomnomLogo from '../../assets/images/nomnom-ai logo.PNG';

// A reusable component for styled status screens (Loading, Finished, etc.)
const StatusScreen = ({ message, showLogo = true }) => (
    <div className="home-container">
        <div className="status-container">
            {showLogo && <img src={nomnomLogo} alt="NomNom AI Logo" className="status-logo" />}
            <p className="status-message">{message}</p>
        </div>
    </div>
);

export default StatusScreen;
