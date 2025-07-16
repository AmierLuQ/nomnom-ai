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
    <div className="register-auth-container">
      {/* Logo Section */}
      <img
        src="/nomnom-ai-text-logo.PNG"
        alt="NomNom AI Logo"
        className="register-logo-img"
      />

      {/* Form Container */}
      <div className="register-form-container">
        <h2 className="register-form-title">Register.</h2>
        <p className="register-form-subtitle">Create a new account.</p>

        <form className="register-form" onSubmit={handleRegister}>
          {/* Username Field */}
          <div className="register-form-input-group">
            <label className="register-form-label">USERNAME</label>
            <input
              type="text"
              placeholder="Enter Username"
              className="register-form-input"
              required
            />
          </div>

          {/* Name Field */}
          <div className="register-form-input-group">
            <label className="register-form-label">FULL NAME</label>
            <input
              type="text"
              placeholder="Enter Full Name"
              className="register-form-input"
              required
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
