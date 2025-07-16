import React, { useState, useEffect } from "react"; // Removed useRef
import "../styles/HomePage.css";
import {
  FaTimes,
  FaUndoAlt,
  FaHeart,
  FaUtensils,
  FaChevronUp,
  FaChevronDown,
  FaStar,
  FaStarHalfAlt,
  FaRegStar,
  FaMapMarkerAlt,
  FaRegStickyNote,
  FaClock,
  FaMoneyBillWave,
  FaPhone,
} from "react-icons/fa";

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

  // Function to toggle details view
  const toggleDetails = (e) => {
    if (e) e.stopPropagation(); // Prevent any parent click issues
    setShowDetails(prev => !prev);
  };

  const handleSkip = (e) => {
    if (e) e.stopPropagation();
    setCurrentIndex((prevIndex) => (prevIndex + 1) % restaurants.length);
    setShowDetails(false); // Reset details view
  };

  const handleUndo = (e) => {
    if (e) e.stopPropagation();
    setCurrentIndex((prevIndex) =>
      prevIndex === 0 ? restaurants.length - 1 : prevIndex - 1
    );
    setShowDetails(false); // Reset details view
  };

  const handleFavorite = (e) => {
    if (e) e.stopPropagation();
    console.log("Favorite clicked!");
    // Implement favorite logic
  };

  const handleEat = (e) => {
    if (e) e.stopPropagation();
    console.log("Eat clicked!");
    handleSkip(); // Move to next restaurant after 'eating'
  };


  const getStars = (rating) => {
    const roundedRating = Math.round(rating * 2) / 2; // Round to nearest 0.5
    const fullStars = Math.floor(roundedRating);
    const halfStar = roundedRating - fullStars >= 0.5;

    return [...Array(5)].map((_, i) => {
      if (i < fullStars) return <FaStar key={i} color="#FFD700" />;
      if (i === fullStars && halfStar)
        return <FaStarHalfAlt key={i} color="#FFD700" />;
      return <FaRegStar key={i} color="#CCCCCC" />;
    });
  };

  function formatPrice(min, max) {
    const cleanMin = min.replace("RM", "").replace(".00", "");
    const cleanMax = max.replace("RM", "").replace(".00", "");
    return `RM ${cleanMin}-${cleanMax}`;
  }

  // Determine current opening status
  const getOpenStatus = (openingHours) => {
    if (!openingHours) return { status: 'Unknown', isOpen: false };

    // Simple heuristic: if "Closed" is in the string
    if (openingHours.toLowerCase().includes("closed")) {
      return { status: 'Closed', isOpen: false };
    }

    // For more robust checking, you'd parse current time against opening hours.
    // For now, assume "Open" if not explicitly "Closed"
    return { status: 'Open', isOpen: true };
  };

  const { status: openStatus, isOpen: isRestaurantOpen } = getOpenStatus(restaurant["Opening Hours"]);


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
        className={`home-image-box ${showDetails ? "expanded" : ""}`}
      >
        <img
          src={`/images/${restaurant.ID.toLowerCase()}.png`}
          alt={restaurant.Name}
          className="home-restaurant-image"
        />
        <div className="home-image-gradient"></div>

        {/* Content Overlay */}
        <div className="home-image-content">
          {/* Top Info (Name, Rating, Tags) */}
          <div className="home-top-info-container">
            {/* Name & Rating */}
            <div className="home-name-rating-container">
              <h2 className="home-restaurant-name">{restaurant.Name}</h2>
              <p className="home-restaurant-rating">
                {Number(restaurant["Google Rating"] || 0).toFixed(1)}{" "}
                {getStars(Number(restaurant["Google Rating"] || 0))}
              </p>
            </div>

            {/* Tags */}
            <div className="home-pill-container">
              {[restaurant["Tag 1"], restaurant["Tag 2"], restaurant["Tag 3"]]
                .filter(Boolean)
                .map((tag, index) => (
                  <span key={index} className="home-pill-box home-tag">
                    {tag}
                  </span>
                ))}
              {/* Price pill only shown when not expanded */}
              {!showDetails && (
                <span className="home-pill-box home-price">
                  {formatPrice(
                    restaurant["Est Price Min per Person"],
                    restaurant["Est Price Max per Person"]
                  )}
                </span>
              )}
            </div>
          </div>

          {/* Description Box (shown when expanded) */}
          <div className={`home-details-container ${showDetails ? "show" : ""}`}>
            {/* Map Placeholder */}
            <div className="home-map-placeholder">
              <FaMapMarkerAlt size={24} /> <p>Map Placeholder</p>
            </div>
            <div className="home-info-row">
              <FaMapMarkerAlt size={14} />{" "}
              <span>{restaurant.Location || "No address provided."}</span>
            </div>
            <div className="home-info-row">
              <FaRegStickyNote size={14} />{" "}
              <span>{restaurant.Description || "No description provided."}</span>
            </div>
            <div className="home-info-row">
              <FaClock size={14} />{" "}
              <span>
                <span
                  className={
                    isRestaurantOpen ? "home-status-open" : "home-status-closed"
                  }
                >
                  {openStatus}
                </span>{" "}
                • {restaurant["Opening Hours"] || "10:00 AM - 10:00 PM"}
              </span>
            </div>
            <div className="home-info-row">
              <FaMoneyBillWave size={14} />{" "}
              <span>
                {formatPrice(
                  restaurant["Est Price Min per Person"],
                  restaurant["Est Price Max per Person"]
                )}{" "}
                per person
              </span>
            </div>
            <div className="home-info-row">
              <FaPhone size={14} />{" "}
              <span>{restaurant.Phone || "No phone number provided."}</span>
            </div>
          </div>


          {/* Bottom Fixed Buttons */}
          <div className="home-bottom-fixed">
            <div className="home-button-group">
              <button
                type="button"
                className="home-action-button home-skip"
                onClick={handleSkip}
              >
                <FaTimes />
              </button>
              <button
                type="button"
                className="home-action-button home-undo"
                onClick={handleUndo}
              >
                <FaUndoAlt />
              </button>
              <button
                type="button"
                className="home-action-button home-favorite"
                onClick={handleFavorite}
              >
                <FaHeart />
              </button>
              <button
                type="button"
                className="home-action-button home-eat"
                onClick={handleEat}
              >
                <FaUtensils />
              </button>
            </div>

            {/* Swipe Indicator (bottom) - always present */}
            <div
              className="home-swipe-indicator-bottom"
              onClick={toggleDetails}
            >
              {showDetails ? <FaChevronDown /> : <FaChevronUp />}
            </div>
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