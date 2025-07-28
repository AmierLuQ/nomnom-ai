import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Eye, EyeOff } from "lucide-react";
import "./LoginPage.css";

import nomnomTextLogo from '../../assets/images/nomnom-ai-text-logo.PNG';

export default function LoginPage() {
  const navigate = useNavigate();
  const [showPassword, setShowPassword] = useState(false);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const togglePassword = () => setShowPassword(!showPassword);

  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");

    try {
      const response = await fetch("https://nomnom-ai.onrender.com/api/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          username: username,
          password: password,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        localStorage.setItem("token", data.access_token);
        localStorage.setItem("username", data.username);
        navigate("/home");
      } else {
        setError(data.message || "Login failed. Please try again.");
      }
    } catch (err) {
      console.error("Login error:", err);
      setError("Something went wrong. Please try again later.");
    }
  };

  const handlePotatoLogin = async () => {
    try {
      const response = await fetch("https://nomnom-ai.onrender.com/api/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          username: "potato",
          password: "potato123",
        }),
      });

      const data = await response.json();

      if (response.ok) {
        localStorage.setItem("token", data.access_token);
        localStorage.setItem("username", data.username);
        navigate("/home");
      } else {
        console.error("Potato login failed:", data.message);
        alert("Failed to login as Potato.");
      }
    } catch (err) {
      console.error("Potato login error:", err);
      alert("Something went wrong. Please try again later.");
    }
  };

  return (
    <div className="login-auth-container">
      <button className="login-potato-button" onClick={handlePotatoLogin}>
        Potato
      </button>
      
      <img
        src={nomnomTextLogo}
        alt="NomNom AI Logo"
        className="login-logo-img"
      />

      <div className="login-form-container">
        <h2 className="login-form-title">Login.</h2>
        <p className="login-form-subtitle">Sign in to continue.</p>

        {error && <div className="login-error-message">{error}</div>}

        <form className="login-form" onSubmit={handleLogin}>
          <div className="login-form-input-group">
            <label className="login-form-label">USERNAME</label>
            <input
              type="text"
              placeholder="Enter Username"
              className="login-form-input"
              required
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
          </div>

          <div className="login-form-input-group">
            <label className="login-form-label">PASSWORD</label>
            <div className="login-password-field">
              <input
                type={showPassword ? "text" : "password"}
                placeholder="Enter Password"
                className="login-form-input"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
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
