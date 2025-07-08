import React from "react";
import { useNavigate } from "react-router-dom";
import "../styles/LandingPage.css";

export default function LandingPage() {
  const navigate = useNavigate();

  const handleStart = () => {
    navigate("/home");
  };

  return (
    <div className="landing-container">
      <img
        src="/nomnom-ai logo.PNG"
        alt="NomNom AI Logo"
        className="landing-logo"
      />

      <h1 className="landing-title">Welcome to NomNom AI</h1>

      <p className="landing-subtitle">
        Let us help you decide what to eat — fast, smart, and within your budget.
        Powered by AI. Personalized for you.
      </p>

      <button className="landing-button" onClick={handleStart}>Get Started</button>

      <footer className="landing-footer">
        © {new Date().getFullYear()} NomNom AI. All rights reserved.
      </footer>
    </div>
  );
}