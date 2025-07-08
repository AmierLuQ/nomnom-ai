import React, { useState, useEffect } from "react";
import "./HomePage.css";

export default function HomePage() {
  const [restaurant, setRestaurant] = useState(null);
  const [showRating, setShowRating] = useState(false);

  useEffect(() => {
    fetch("https://nomnom-ai.onrender.com/api/restaurants")
      .then((res) => res.json())
      .then((data) => {
        const rst001 = data.find(r => r.ID === "RST_001");
        setRestaurant(rst001);
      })
      .catch((err) => console.error("API fetch error:", err));
  }, []);

  if (!restaurant) return <p className="loading">Loading...</p>;

  const handlePick = () => setShowRating(true);

  return (
    <div className="home-container">
      {/* Header: Logo + NomNom AI Text */}
      <header className="home-header">
        <div className="logo-text">
          <img
            src="/nomnom-ai logo.PNG"
            alt="NomNom AI Logo"
            className="home-logo"
          />
          <h1 className="home-brand">NomNom AI</h1>
        </div>
        <hr className="header-line" />
      </header>

      {!showRating ? (
        <>
          <div className="image-box">
            <img
              src={`/images/${restaurant.ID.toLowerCase()}.png`}
              alt={restaurant.Name}
              className="restaurant-image"
            />
            <div className="overlay">
              <div className="name-rating">
                <h2 className="restaurant-name">{restaurant.Name}</h2>
                <p className="rating">⭐ {restaurant["Google Rating"]}</p>
              </div>
              <p className="description">{restaurant.Description}</p>
              <div className="tags">
                {[restaurant["Tag 1"], restaurant["Tag 2"], restaurant["Tag 3"]]
                  .filter(Boolean)
                  .map((tag, index) => (
                    <span key={index} className="tag-pill">{tag}</span>
                  ))}
              </div>
            </div>
          </div>

          <div className="button-group">
            <button className="home-button" onClick={handlePick}>Looks Good 🍽</button>
            <button className="home-button secondary">Skip ❌</button>
          </div>
        </>
      ) : (
        <RatingPrompt />
      )}

      <footer className="home-footer">
        © {new Date().getFullYear()} NomNom AI. All rights reserved.
      </footer>
    </div>
  );
}

function RatingPrompt() {
  const [hovered, setHovered] = useState(0);

  return (
    <div className="rating-container">
      <h2>Rate your experience</h2>
      <div className="star-input">
        {[1, 2, 3, 4, 5].map((star) => (
          <span
            key={star}
            className={`star ${hovered >= star ? 'hovered' : ''}`}
            onMouseEnter={() => setHovered(star)}
            onMouseLeave={() => setHovered(0)}
          >★</span>
        ))}
      </div>
    </div>
  );
}
