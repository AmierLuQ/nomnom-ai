import React, { useState } from "react";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
import { Eye, EyeOff } from "lucide-react";
import { useNavigate } from "react-router-dom";
import "../styles/RegisterPage.css";

export default function RegisterPage() {
  const navigate = useNavigate();
  const [showPassword, setShowPassword] = useState(false);
  const [dob, setDob] = useState(null);

  const togglePassword = () => setShowPassword(!showPassword);

  const handleRegister = (e) => {
    e.preventDefault();
    console.log("Registering account...");
  };

  return (
    <div className="auth-container">
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
        <h2 className="form-title">Register.</h2>
        <p className="form-subtitle">Create a new account.</p>

        <form className="register-form" onSubmit={handleRegister}>
          {/* Userame Field */}
          <div className="form-input-group">
            <label className="form-label">USERNAME</label>
            <input
              type="text"
              placeholder="Enter Username"
              className="form-input"
              required
            />
          </div>

          {/* Name Field */}
          <div className="form-input-group">
            <label className="form-label">FULL NAME</label>
            <input
              type="text"
              placeholder="Enter Full Name"
              className="form-input"
              required
            />
          </div>

          {/* Email Field */}
          <div className="form-input-group">
            <label className="form-label">EMAIL</label>
            <input
              type="email"
              placeholder="Enter Email"
              className="form-input"
              required
            />
          </div>

          {/* Password Field */}
          <div className="form-input-group">
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
                {showPassword ? (
                  <EyeOff size={18} color="#FDFFFC" />
                ) : (
                  <Eye size={18} color="#FDFFFC" />
                )}
              </button>
            </div>
          </div>

          {/* Date of Birth Field */}
          <label className="form-label-date">DATE OF BIRTH</label>
          <DatePicker
  selected={dob}
  onChange={(date) => setDob(date)}
  placeholderText="dd/mm/yyyy"
  className="form-input"
/>

          {/* Phone Field */}
          <div className="form-input-group">
            <label className="form-label">PHONE NO.</label>
            <input
              type="tel"
              placeholder="Enter Phone No."
              className="form-input"
              required
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
        <footer className="form-footer">
          © {new Date().getFullYear()} NomNom AI. All rights reserved.
        </footer>
      </div>
    </div>
  );
}
