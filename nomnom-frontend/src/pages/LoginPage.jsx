import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { FaEye, FaEyeSlash } from "react-icons/fa";
import "../styles/AuthPage.css";

export default function LoginPage() {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  const handleLogin = (e) => {
    e.preventDefault();
    console.log("Logging in with", { username, password });
    // TODO: Connect to backend API
  };

  return (
    <div className="auth-container">
      {/* Top Logo Section */}
      <div className="logo-section">
        <img
          src="/nomnom-ai logo.PNG"
          alt="NomNom AI Logo"
          className="auth-logo"
        />
        <h1 className="auth-brand">NomNom AI</h1>
      </div>

      {/* Rounded Form Container */}
      <div className="form-container">
        <h2 className="form-header">Login.</h2>
        <p className="form-subtitle">Sign in to continue.</p>

        <form className="auth-form" onSubmit={handleLogin}>
          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="auth-input"
            required
          />
          <div className="password-field">
            <input
              type={showPassword ? "text" : "password"}
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="auth-input"
              required
            />
            <span
              className="toggle-password"
              onClick={() => setShowPassword(!showPassword)}
            >
              {showPassword ? <FaEyeSlash /> : <FaEye />}
            </span>
          </div>
          <button type="submit" className="auth-button">
            Log In
          </button>
        </form>

        <p className="auth-link">Forgot Password?</p>
        <p className="auth-link">
          Don’t have an account?{" "}
          <span onClick={() => navigate("/register")} className="link-text">
            Register Here.
          </span>
        </p>
      </div>

      {/* Footer */}
      <footer className="auth-footer">
        © {new Date().getFullYear()} NomNom AI. All rights reserved.
      </footer>
    </div>
  );
}
