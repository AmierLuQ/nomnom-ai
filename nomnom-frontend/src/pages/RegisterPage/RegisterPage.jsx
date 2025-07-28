import React, { useState } from "react";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
import { Eye, EyeOff } from "lucide-react";
import { useNavigate } from "react-router-dom";
import "./RegisterPage.css";

import nomnomTextLogo from '../../assets/images/nomnom-ai-text-logo.PNG';

export default function RegisterPage() {
  const navigate = useNavigate();
  const [showPassword, setShowPassword] = useState(false);
  const [dob, setDob] = useState(null);
  const [username, setUsername] = useState("");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const togglePassword = () => setShowPassword(!showPassword);

  const handleRegister = async (e) => {
    e.preventDefault();
    setError(""); // Reset error

    try {
      const response = await fetch("https://nomnom-ai.onrender.com/api/register", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          username: username,
          fullName: fullName,
          email: email,
          phone: phone,
          dob: dob ? dob.toISOString().split("T")[0] : null, // Format YYYY-MM-DD
          password: password,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        // ✅ Registration successful
        alert("🎉 Account created! You can now log in.");
        navigate("/login"); // Redirect to login page
      } else {
        // ❌ Backend responded with error
        setError(data.message || "Registration failed. Try again.");
      }
    } catch (err) {
      console.error("Registration error:", err);
      setError("Something went wrong. Please try again later.");
    }
  };

  return (
    <div className="register-auth-container">
      {/* UPDATED: Use imported logo */}
      <img
        src={nomnomTextLogo}
        alt="NomNom AI Logo"
        className="register-logo-img"
      />

      {/* Form Container */}
      <div className="register-form-container">
        <h2 className="register-form-title">Register.</h2>
        <p className="register-form-subtitle">Create a new account.</p>

        {/* Error Message */}
        {error && <div className="register-error-message">{error}</div>}

        <form className="register-form" onSubmit={handleRegister}>
          {/* Username Field */}
          <div className="register-form-input-group">
            <label className="register-form-label">USERNAME</label>
            <input
              type="text"
              placeholder="Enter Username"
              className="register-form-input"
              required
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
          </div>

          {/* Full Name Field */}
          <div className="register-form-input-group">
            <label className="register-form-label">FULL NAME</label>
            <input
              type="text"
              placeholder="Enter Full Name"
              className="register-form-input"
              required
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
            />
          </div>

          {/* Email Field */}
          <div className="register-form-input-group">
            <label className="register-form-label">EMAIL</label>
            <input
              type="email"
              placeholder="Enter Email"
              className="register-form-input"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>

          {/* Password Field */}
          <div className="register-form-input-group">
            <label className="register-form-label">PASSWORD</label>
            <div className="register-password-field">
              <input
                type={showPassword ? "text" : "password"}
                placeholder="Enter Password"
                className="register-form-input"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
              <button
                type="button"
                className="register-toggle-btn"
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

          {/* Date of Birth Field */}
          <div className="register-form-input-group">
            <label className="register-form-label">DATE OF BIRTH</label>
            <DatePicker
              selected={dob}
              onChange={(date) => setDob(date)}
              placeholderText="dd/mm/yyyy"
              className="register-form-input date"
              required
            />
          </div>

          {/* Phone Field */}
          <div className="register-form-input-group">
            <label className="register-form-label">PHONE NO.</label>
            <input
              type="tel"
              placeholder="Enter Phone No."
              className="register-form-input"
              required
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
            />
          </div>

          <button type="submit" className="register-btn">
            Sign up
          </button>
        </form>

        <p className="register-text">
          Already have an account?{" "}
          <span
            className="register-link"
            onClick={() => navigate("/login")}
          >
            Login here.
          </span>
        </p>
        <footer className="register-form-footer">
          © {new Date().getFullYear()} NomNom AI. All rights reserved.
        </footer>
      </div>
    </div>
  );
}
