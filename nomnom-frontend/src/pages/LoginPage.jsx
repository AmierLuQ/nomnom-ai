import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import "../styles/AuthPage.css";

export default function LoginPage() {
  const navigate = useNavigate();
  const [showPassword, setShowPassword] = useState(false);

  const togglePassword = () => setShowPassword(!showPassword);

  const handleLogin = (e) => {
    e.preventDefault();
    console.log("Form submitted"); // Later connect to API
  };

  return (
    <div className="login-container">
      {/* Logo Section */}
      <div className="logo-section">
        <img
          src="/nomnom-ai logo.PNG"
          alt="NomNom AI Logo"
          className="logo-img"
        />
        <h1 className="logo-text">NomNom AI</h1>
      </div>

      {/* Form Container */}
      <div className="form-container">
        <h2 className="form-title">Login.</h2>
        <p className="form-subtitle">Sign in to continue.</p>

        <form className="login-form" onSubmit={handleLogin}>
          <label className="form-label">USERNAME</label>
          <input
            type="text"
            placeholder="Enter Username"
            className="form-input"
            required
          />

          <label className="form-label">PASSWORD</label>
          <div className="password-field">
            <input
              type={showPassword ? "text" : "password"}
              placeholder="Enter Password"
              className="form-input"
              required
            />
            <button
              type="button"
              className="toggle-btn"
              onClick={togglePassword}
            >
              {showPassword ? "🙈" : "👁️"}
            </button>
          </div>

          <button type="submit" className="login-btn">
            Log in
          </button>
        </form>

        <a href="#" className="forgot-link">
          Forgot Password?
        </a>
        <p className="register-text">
          Don’t have an account?{" "}
          <span
            className="register-link"
            onClick={() => navigate("/register")}
          >
            Register Here
          </span>
        </p>
      </div>
    </div>
  );
}
