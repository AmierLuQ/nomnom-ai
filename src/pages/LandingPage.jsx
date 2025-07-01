import React from "react";
import "./LandingPage.css";

export default function LandingPage() {
  return (
    <div className="landing-container">
      {/* Logo */}
      <img
        src="/nomnom-ai logo.PNG"
        alt="NomNom AI Logo"
        className="landing-logo"
      />

      {/* Headline */}
      <h1 className="landing-title">Welcome to NomNom AI</h1>

      {/* Subtitle */}
      <p className="landing-subtitle">
        Let us help you decide what to eat — fast, smart, and within your budget.
        Powered by AI. Personalized for you.
      </p>

      {/* Button */}
      <button className="landing-button">Get Started</button>

      {/* Footer */}
      <footer className="landing-footer">
        © {new Date().getFullYear()} NomNom AI. All rights reserved.
      </footer>
    </div>
  );
}
