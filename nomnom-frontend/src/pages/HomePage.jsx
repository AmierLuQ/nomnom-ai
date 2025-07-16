import React, { useState, useEffect, useRef } from "react"; // Added useRef back as it's needed for nameRef
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
  const nameRef = useRef(null); // useRef is needed for the name length check
  const [longName, setLongName] = useState(false); // State for long name

  useEffect(() => {
    fetch("https://nomnom-ai.onrender.com/api/restaurants")
      .then((res) => res.json())
      .then((data) => {
        setRestaurants(data); // Save all restaurants
      })
      .catch((err) => console.error("API fetch error:", err));
  }, []);

  // Derive the current restaurant based on restaurants array and currentIndex
  const restaurant = restaurants[currentIndex];

  // Effect to check if the restaurant name is too long
  useEffect(() => {
    if (nameRef.current && restaurant) {
      const computedStyle = getComputedStyle(nameRef.current);
      const lineHeight = parseFloat(computedStyle.lineHeight);
      const height = nameRef.current.offsetHeight;
      const lines = Math.round(height / lineHeight);
      setLongName(lines > 1);
    }
  }, [restaurant]); // Re-run when the current restaurant changes

  // Conditional render for loading state - must be after all hooks
  if (!restaurant) {
    return <p className="loading">Loading...</p>;
  }

  // Function to toggle details view
  const toggleDetails = (e) => {
    if (e) e.stopPropagation(); // Prevent any parent click issues
    setShowDetails((prev) => !prev);
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

  // Determine current opening status based on actual opening/closing times
  const getOpenStatus = (openingHours, closingHours) => {
    const now = new Date();
    const currentDay = now.getDay(); // 0 for Sunday, 1 for Monday, etc.
    const currentTime = now.getHours() * 60 + now.getMinutes(); // Current time in minutes

    if (!openingHours || !closingHours) return { status: 'Unknown', isOpen: false };

    // Assuming openingHours and closingHours are in 'HH:MM:SS' format
    const [openHour, openMinute] = openingHours.split(':').map(Number);
    const [closeHour, closeMinute] = closingHours.split(':').map(Number);

    let openTimeInMinutes = openHour * 60 + openMinute;
    let closeTimeInMinutes = closeHour * 60 + closeMinute;

    // Handle cases where closing time is on the next day (e.g., 10 PM - 2 AM)
    if (closeTimeInMinutes < openTimeInMinutes) {
      // If current time is past midnight but before closing time (e.g., 00:00 to 02:00 for a 10 PM - 2 AM place)
      if (currentTime >= 0 && currentTime < closeTimeInMinutes) {
        return { status: 'Open', isOpen: true };
      }
      // If current time is after opening time until midnight (e.g., 22:00 to 23:59 for a 10 PM - 2 AM place)
      if (currentTime >= openTimeInMinutes && currentTime <= 24 * 60) {
        return { status: 'Open', isOpen: true };
      }
      return { status: 'Closed', isOpen: false };
    } else {
      // Normal opening hours within the same day
      if (currentTime >= openTimeInMinutes && currentTime < closeTimeInMinutes) {
        return { status: 'Open', isOpen: true };
      }
      return { status: 'Closed', isOpen: false };
    }
  };


  const { status: openStatus, isOpen: isRestaurantOpen } = getOpenStatus(
    restaurant["Opening Time"],
    restaurant["Closing Time"]
  );

  const getMapUrl = (latitude, longitude) => {
    if (latitude && longitude) {
      // Google Maps embed URL
      return `https://www.google.com/maps/embed/v1/place?key=YOUR_Maps_API_KEY&q=${latitude},${longitude}`;
      // Note: Replace 'YOUR_Maps_API_KEY' with your actual API key
    }
    return null;
  };

  const mapUrl = getMapUrl(restaurant.Latitude, restaurant.Longitude);

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
      <div className={`home-image-box ${showDetails ? "expanded" : ""}`}>
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
              <h2
                ref={nameRef}
                className={`home-restaurant-name ${longName ? "long-name" : ""}`}
              >
                {restaurant.Name}
              </h2>
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
            {/* Map Section */}
            {mapUrl ? (
              <div className="home-map-container">
                <iframe
                  title="Google Map"
                  src={mapUrl}
                  width="100%"
                  height="150"
                  style={{ border: 0 }}
                  allowFullScreen=""
                  loading="lazy"
                  referrerPolicy="no-referrer-when-downgrade"
                ></iframe>
              </div>
            ) : (
              <div className="home-map-placeholder">
                <FaMapMarkerAlt size={24} /> <p>Map Not Available</p>
              </div>
            )}

            <div className="home-info-row">
              <FaMapMarkerAlt size={14} />{" "}
              {/* Use restaurant.Address for more detailed address if available */}
              <span>{restaurant.Address || "No address provided."}</span>
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
                • {restaurant["Opening Time"] && restaurant["Closing Time"]
                    ? `${restaurant["Opening Time"].substring(0, 5)} - ${restaurant["Closing Time"].substring(0, 5)}`
                    : "Hours unknown."}
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
              <span>{restaurant["Phone No."] || "No phone number provided."}</span>
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