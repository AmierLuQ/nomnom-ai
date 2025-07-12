import React from "react";
import { useNavigate } from "react-router-dom";
import "../styles/LandingPage.css";

export default function LandingPage() {
  const navigate = useNavigate();

  const handleStart = () => {
    navigate("/login");
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

      <button className="landing-button" onClick={handleStart}>
        Get Started
      </button>

      <div className="features-section">
        <div className="feature-card">
          <img
            src="/onside_coral_nomnom-ai logo.PNG"
            alt="AI Recommendations"
            className="feature-icon"
          />
          <h3 className="feature-title">AI-Powered Recommendations</h3>
          <p className="feature-desc">
            Smart suggestions tailored to your taste, lifestyle, and cravings—getting more accurate the more you use it.
          </p>
        </div>

        <div className="feature-card">
          <img
            src="/onside_orange_nomnom-ai logo.PNG"
            alt="Quick Decisions"
            className="feature-icon"
          />
          <h3 className="feature-title">Quick & Effortless Decisions</h3>
          <p className="feature-desc">
            Swipe and pick in seconds. No more endless debates about “What should we eat?”—we’ve got you covered.
          </p>
        </div>

        <div className="feature-card">
          <img
            src="/onside_orange_nomnom-ai logo.PNG"
            alt="Budget-Friendly"
            className="feature-icon"
          />
          <h3 className="feature-title">Budget-Friendly Choices</h3>
          <p className="feature-desc">
            Find meals that satisfy your cravings without breaking your budget—delicious options for every price range.
          </p>
        </div>

        <div className="feature-card">
          <img
            src="/onside_coral_nomnom-ai logo.PNG"
            alt="Minimal Effort"
            className="feature-icon"
          />
          <h3 className="feature-title">Minimal Effort, Maximum Flavor</h3>
          <p className="feature-desc">
            Enjoy a seamless, mobile-first experience designed to help you decide fast and start enjoying your meal sooner.
          </p>
        </div>
      </div>

      <footer className="landing-footer">
        © {new Date().getFullYear()} NomNom AI. All rights reserved.
      </footer>
    </div>
  );
}
