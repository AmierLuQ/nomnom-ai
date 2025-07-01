import React from "react";
import "./HomePage.css";

export default function HomePage() {
  return (
    <div className="home-container">
      <img
        src="/nomnom-ai logo.PNG"
        alt="NomNom AI Logo"
        className="home-logo"
      />

      <h1 className="home-title">Today's Suggestion</h1>

      <div className="recommendation-card">
        <h2>Shawarma Zinger UTP</h2>
        <p>Middle Eastern wrap with crispy chicken and garlic sauce.</p>
        <p><strong>RM9.00</strong></p>
      </div>

      <div className="button-group">
        <button className="home-button">Looks Good 🍽</button>
        <button className="home-button secondary">Skip ❌</button>
      </div>

      <footer className="home-footer">
        © {new Date().getFullYear()} NomNom AI. All rights reserved.
      </footer>
    </div>
  );
}
