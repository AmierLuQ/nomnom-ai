import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Eye, EyeOff } from "lucide-react";
import "../styles/LoginPage.css";

export default function LoginPage() {
  const navigate = useNavigate();
  const [showPassword, setShowPassword] = useState(false);

  const togglePassword = () => setShowPassword(!showPassword);

  const handleLogin = (e) => {
    e.preventDefault();
    console.log("Logging in...");
  };

  return (
    <div className="login-auth-container">
      {/* Potato Button */}
      <button
        className="login-potato-button"
        onClick={() => navigate("/home")}
      >
        Potato
      </button>

      {/* Logo Section */}
      <img
        src="/nomnom-ai-text-logo.PNG"
        alt="NomNom AI Logo"
        className="login-logo-img"
      />

      {/* Form Container */}
      <div className="login-form-container">
        <h2 className="login-form-title">Login.</h2>
        <p className="login-form-subtitle">Sign in to continue.</p>

        <form className="login-form" onSubmit={handleLogin}>
          {/* Username Field */}
          <div className="login-form-input-group">
            <label className="login-form-label">USERNAME</label>
            <input
              type="text"
              placeholder="Enter Username"
              className="login-form-input"
              required
            />
          </div>

          {/* Password Field */}
          <div className="login-form-input-group">
            <label className="login-form-label">PASSWORD</label>
            <div className="login-password-field">
              <input
                type={showPassword ? "text" : "password"}
                placeholder="Enter Password"
                className="login-form-input"
                required
              />
              <button
                type="button"
                className="login-toggle-btn"
                onClick={togglePassword}
              >
                {showPassword ? (
                  <EyeOff size={18} color="#FDFFFC" />
                ) : (
                  <Eye size={18} color="#FDFFFC" />
                )}
              </button>
            </div>
          </div>

          <button type="submit" className="login-btn">
            Log in
          </button>
        </form>

        <button
          className="login-forgot-link"
          onClick={() => alert("Forgot Password placeholder")}
        >
          Forgot Password?
        </button>
        <p className="login-register-text">
          Don’t have an account?{" "}
          <span
            className="login-register-link"
            onClick={() => navigate("/register")}
          >
            Register Here
          </span>
        </p>
        <footer className="login-form-footer">
          © {new Date().getFullYear()} NomNom AI. All rights reserved.
        </footer>
      </div>
    </div>
  );
}
