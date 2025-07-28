import React from 'react';

// A reusable component for styled status screens (Loading, Finished, etc.)
const StatusScreen = ({ message, showLogo = true }) => (
    <div className="home-container">
        <div className="status-container">
            {showLogo && <img src="/nomnom-ai logo.PNG" alt="NomNom AI Logo" className="status-logo" />}
            <p className="status-message">{message}</p>
        </div>
    </div>
);

export default StatusScreen;
