import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { FaEye, FaEyeSlash } from "react-icons/fa";
import "../styles/AuthPage.css";

export default function RegisterPage() {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");

  const handleRegister = (e) => {
    e.preventDefault();
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }
    console.log("Registering with", { username, password });
    // TODO: Connect to backend API
  };

  return (
    <div className="auth-container">
      {/* Logo Section */}
      <div className="logo-section">
        <img
          src="/nomnom-ai logo.PNG"
          alt="NomNom AI Logo"
          className="auth-logo"
        />
        <h1 className="logo-text">NomNom AI</h1>
      </div>

      {/* Form Container */}
      <div className="form-container">
        <h2 className="form-title">Register.</h2>
        <p className="form-subtitle">Create your account.</p>

        {error && <p className="form-error">{error}</p>}

        <form className="auth-form" onSubmit={handleRegister}>
          <label className="field-label">NAME</label>
          <input
            type="text"
            placeholder="John Doe"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="auth-input"
            required
          />

          <label className="field-label">PASSWORD</label>
          <div className="password-field">
            <input
              type={showPassword ? "text" : "password"}
              placeholder="••••••"
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

          <label className="field-label">CONFIRM PASSWORD</label>
          <div className="password-field">
            <input
              type={showPassword ? "text" : "password"}
              placeholder="••••••"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
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
            Register
          </button>
        </form>

        <p className="auth-link">
          Already have an account?{" "}
          <span
            onClick={() => navigate("/login")}
            className="link-text"
          >
            Login Here.
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
