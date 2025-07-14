import React, { useState, useEffect } from "react";
import "../styles/HomePage.css";
import { FaTimes, FaUndoAlt, FaHeart, FaUtensils, FaChevronUp, FaChevronDown } from "react-icons/fa";
import { FaStar, FaStarHalfAlt, FaRegStar } from "react-icons/fa";

export default function HomePage() {
  const [restaurants, setRestaurants] = useState([]); // Store all restaurants
  const [currentIndex, setCurrentIndex] = useState(0); // Track current index
  const [showDetails, setShowDetails] = useState(false);

  useEffect(() => {
    fetch("https://nomnom-ai.onrender.com/api/restaurants")
      .then((res) => res.json())
      .then((data) => {
        setRestaurants(data); // Save all restaurants
      })
      .catch((err) => console.error("API fetch error:", err));
  }, []);

  if (!restaurants.length) return <p className="loading">Loading...</p>;

  const restaurant = restaurants[currentIndex];

  const handleSwipe = (direction) => {
    console.log(`Swiped ${direction}`);
    if (direction === "up") setShowDetails(true);
    if (direction === "down") setShowDetails(false);
  };

  const handleSkip = () => {
    setCurrentIndex((prevIndex) => (prevIndex + 1) % restaurants.length);
    setShowDetails(false); // Reset details view
  };

  const handleUndo = () => {
  setCurrentIndex((prevIndex) =>
    prevIndex === 0 ? restaurants.length - 1 : prevIndex - 1
  );
  setShowDetails(false); // Reset details view
};

  const getStars = (rating) => {
    const fullStars = Math.floor(rating);
    const halfStar = rating - fullStars >= 0.5;

    return [...Array(5)].map((_, i) => {
      if (i < fullStars) return <FaStar key={i} color="#FFD700" />;
      if (i === fullStars && halfStar) return <FaStarHalfAlt key={i} color="#FFD700" />;
      return <FaRegStar key={i} color="#CCCCCC" />;
    });
  };

  function formatPrice(min, max) {
    const cleanMin = min.replace("RM", "").replace(".00", "");
    const cleanMax = max.replace("RM", "").replace(".00", "");
    return `RM ${cleanMin}-${cleanMax}`;
  }

  return (
    <div className="home-container">
      {/* Header */}
      <header className="home-header">
        <img
          src="/nomnom-ai-long-logo.PNG"
          alt="NomNom AI Logo"
          className="home-logo"
        />
      </header>

      {/* Image Box */}
      <div
        className={`image-box ${showDetails ? "expanded" : ""}`}
        onTouchStart={(e) => handleSwipe(e.touches[0].clientY < 100 ? "up" : "down")}
      >
        <img
          src={`/images/${restaurant.ID.toLowerCase()}.png`}
          alt={restaurant.Name}
          className="restaurant-image"
        />
        <div className="image-gradient"></div>

        {/* Content Overlay */}
        <div className="image-content">
          {/* Name & Rating */}
          <div className="name-rating-container">
            <h2 className="restaurant-name">{restaurant.Name}</h2>
            <p className="restaurant-rating">
              {Number(restaurant["Google Rating"] || 0).toFixed(1)} {getStars(Number(restaurant["Google Rating"] || 0))}
            </p>
          </div>

          {/* Tags */}
          <div className="pill-container">
            {[restaurant["Tag 1"], restaurant["Tag 2"], restaurant["Tag 3"]]
              .filter(Boolean)
              .map((tag, index) => (
                <span key={index} className="pill-box tag">{tag}</span>
              ))}
            <span className="pill-box price">
              {formatPrice(restaurant["Est Price Min per Person"], restaurant["Est Price Max per Person"])}
            </span>
          </div>

          {/* Description Box */}
          {showDetails && (
            <div className="details-container">
              {/* Map Placeholder */}
              <div className="map-placeholder">
                📍 Map Placeholder
              </div>
              <div className="info-row">
                📍 <span>{restaurant.Location || "3.139, 101.686"}</span>
              </div>
              <div className="info-row">
                📝 <span>{restaurant.Description || "No description provided."}</span>
              </div>
              <div className="info-row">
                ⏰{" "}
                <span>
                  <span className={restaurant.Open ? "status-open" : "status-closed"}>
                    {restaurant.Open ? "Open" : "Closed"}
                  </span>{" "}
                  • {restaurant["Opening Hours"] || "10:00 AM - 10:00 PM"}
                </span>
              </div>
              <div className="info-row">
                💸 <span>{formatPrice(restaurant["Est Price Min per Person"], restaurant["Est Price Max per Person"])} per person</span>
              </div>
              <div className="info-row">
                📞 <span>{restaurant.Phone || "0133997134"}</span>
              </div>
            </div>
          )}

          {/* Interaction Buttons */}
          <div className="button-group">
            <button
              type="button"
              className="action-button skip"
              onClick={(e) => {
                handleSkip();
                e.target.blur(); // Removes focus immediately
              }}
            >
              <FaTimes />
            </button>
            <button
              type="button"
              className="action-button undo"
              onClick={handleUndo}
            >
              <FaUndoAlt />
            </button>
            <button className="action-button favorite"><FaHeart /></button>
            <button className="action-button eat"><FaUtensils /></button>
          </div>

          {/* Swipe Indicator */}
          <div
            className="swipe-indicator"
            onClick={() => setShowDetails(!showDetails)}
          >
            {showDetails ? <FaChevronDown /> : <FaChevronUp />}
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="home-footer">
        © {new Date().getFullYear()} NomNom AI. All rights reserved.
      </footer>
    </div>
  );
}
