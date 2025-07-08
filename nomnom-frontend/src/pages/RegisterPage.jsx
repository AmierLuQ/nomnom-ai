import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import "../styles/RegisterPage.css";

export default function RegisterPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");

  const handleRegister = (e) => {
    e.preventDefault();
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }
    // TODO: Connect to backend API
    console.log("Registering:", { email, password });
  };

  return (
    <div className="auth-container">
      {/* Header: Logo + NomNom AI */}
      <header className="auth-header">
        <div className="logo-text">
          <img
            src="/nomnom-ai logo.PNG"
            alt="NomNom AI Logo"
            className="auth-logo"
          />
          <h1 className="auth-brand">NomNom AI</h1>
        </div>
        <hr className="header-line" />
      </header>

      <form className="auth-form" onSubmit={handleRegister}>
        <h2 className="form-title">Register</h2>
        {error && <p className="form-error">{error}</p>}
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="auth-input"
          required
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="auth-input"
          required
        />
        <input
          type="password"
          placeholder="Confirm Password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          className="auth-input"
          required
        />
        <button type="submit" className="auth-button">
          Register
        </button>
        <p className="switch-text">
          Already have an account?{" "}
          <span onClick={() => navigate("/login")} className="link-text">
            Login
          </span>
        </p>
      </form>

      <footer className="auth-footer">
        © {new Date().getFullYear()} NomNom AI. All rights reserved.
      </footer>
    </div>
  );
}
