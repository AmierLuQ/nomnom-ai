import React, { useState, useEffect } from "react";
import "../styles/HomePage.css";
import {
    FaTimes, FaUndoAlt, FaHeart, FaUtensils, FaChevronUp, FaChevronDown,
    FaStar, FaStarHalfAlt, FaRegStar, FaMapMarkerAlt, FaRegStickyNote,
    FaClock, FaMoneyBillWave, FaPhone,
} from "react-icons/fa";
import { useNavigate } from "react-router-dom";

export default function HomePage() {
    const [restaurants, setRestaurants] = useState([]);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [showDetails, setShowDetails] = useState(false);
    const navigate = useNavigate();

    useEffect(() => {
        const token = localStorage.getItem("token");
        if (!token) {
            alert("Please log in to access NomNom AI.");
            navigate("/login");
            return;
        }

        fetch("https://nomnom-ai.onrender.com/api/recommend", {
            headers: {
                "Authorization": `Bearer ${token}`,
            },
        })
        .then((res) => {
            if (res.status === 401 || res.status === 422) {
                localStorage.removeItem("token");
                localStorage.removeItem("username");
                alert("Session expired. Please log in again.");
                navigate("/login");
                throw new Error("Authentication failed");
            }
            if (!res.ok) {
                throw new Error(`Failed to fetch recommendations (status: ${res.status})`);
            }
            return res.json();
        })
        .then((data) => {
            console.log("Fetched recommendations:", data.recommendations);
            if (data.recommendations && data.recommendations.length > 0) {
                setRestaurants(data.recommendations);
            } else {
                // Handle case where no recommendations are returned
                setRestaurants([]); // Set to empty to show a message
            }
        })
        .catch((err) => {
            console.error("API fetch error:", err);
        });
    }, [navigate]);

    // Show a loading message while fetching
    if (restaurants === null) {
        return <p className="loading">Loading restaurants...</p>;
    }
    
    // Show a message if no restaurants are available
    if (restaurants.length === 0) {
        return <p className="loading">No recommendations available at the moment. Please try again later.</p>;
    }

    const restaurant = restaurants[currentIndex];

    // --- Event Handlers ---
    const toggleDetails = (e) => {
        if (e) e.stopPropagation();
        setShowDetails((prev) => !prev);
    };

    const handleSkip = (e) => {
        if (e) e.stopPropagation();
        setCurrentIndex((prevIndex) => (prevIndex + 1) % restaurants.length);
        setShowDetails(false);
    };

    const handleUndo = (e) => {
        if (e) e.stopPropagation();
        setCurrentIndex((prevIndex) => (prevIndex === 0 ? restaurants.length - 1 : prevIndex - 1));
        setShowDetails(false);
    };

    const handleFavorite = (e) => {
        if (e) e.stopPropagation();
        console.log("Favorite clicked!", restaurant.id);
        // Implement favorite logic here
    };

    const handleEat = (e) => {
        if (e) e.stopPropagation();
        console.log("Eat clicked!", restaurant.id);
        handleSkip();
    };

    // --- Helper Functions ---
    const getStars = (rating) => {
        const roundedRating = Math.round(rating * 2) / 2;
        const fullStars = Math.floor(roundedRating);
        const halfStar = roundedRating - fullStars >= 0.5;
        return [...Array(5)].map((_, i) => {
            if (i < fullStars) return <FaStar key={i} color="#FFD700" />;
            if (i === fullStars && halfStar) return <FaStarHalfAlt key={i} color="#FFD700" />;
            return <FaRegStar key={i} color="#CCCCCC" />;
        });
    };

    const getOpenStatus = (openingHours, closingHours) => {
        if (!openingHours || !closingHours) return { status: 'Unknown', isOpen: false };
        const now = new Date();
        const currentTime = now.getHours() * 60 + now.getMinutes();
        const [openHour, openMinute] = openingHours.split(':').map(Number);
        const [closeHour, closeMinute] = closingHours.split(':').map(Number);
        let openTimeInMinutes = openHour * 60 + openMinute;
        let closeTimeInMinutes = closeHour * 60 + closeMinute;

        if (closeTimeInMinutes < openTimeInMinutes) { // Overnight case
            return { status: (currentTime >= openTimeInMinutes || currentTime < closeTimeInMinutes) ? 'Open' : 'Closed', isOpen: (currentTime >= openTimeInMinutes || currentTime < closeTimeInMinutes) };
        } else { // Same day case
            return { status: (currentTime >= openTimeInMinutes && currentTime < closeTimeInMinutes) ? 'Open' : 'Closed', isOpen: (currentTime >= openTimeInMinutes && currentTime < closeTimeInMinutes) };
        }
    };

    const getMapUrl = (locationString) => {
        if (!locationString) return null;
        const [latitude, longitude] = locationString.split(',');
        if (latitude && longitude) {
            return `https://www.google.com/maps/embed/v1/place?key=YOUR_MAPS_API_KEY&q=${latitude},${longitude}`;
        }
        return null;
    };
    
    // --- Data formatting using correct keys ---
    const { status: openStatus, isOpen: isRestaurantOpen } = getOpenStatus(restaurant.opening_time, restaurant.closing_time);
    const mapUrl = getMapUrl(restaurant.location);

    return (
        <div className="home-container">
            <header className="home-header">
                <img src="/nomnom-ai-long-logo.PNG" alt="NomNom AI Logo" className="home-logo" />
            </header>

            <div className={`home-image-box ${showDetails ? "expanded" : ""}`}>
                {/* FIX: Use restaurant.id (lowercase) */}
                <img src={`/images/${restaurant.id.toLowerCase()}.png`} alt={restaurant.name} className="home-restaurant-image" />
                <div className="home-image-gradient"></div>

                <div className="home-image-content">
                    <div className="home-top-info-container">
                        <div className="home-name-rating-container">
                            {/* FIX: Use restaurant.name */}
                            <h2 className="home-restaurant-name">{restaurant.name}</h2>
                            {/* FIX: Use restaurant.google_rating */}
                            <p className="home-restaurant-rating">
                                {Number(restaurant.google_rating || 0).toFixed(1)}{" "}
                                {getStars(Number(restaurant.google_rating || 0))}
                            </p>
                        </div>

                        <div className="home-pill-container">
                            {/* FIX: Use restaurant.tags array */}
                            {restaurant.tags.map((tag, index) => (
                                <span key={index} className="home-pill-box home-tag">{tag}</span>
                            ))}
                            {!showDetails && (
                                // FIX: Use restaurant.price_range
                                <span className="home-pill-box home-price">{restaurant.price_range}</span>
                            )}
                        </div>
                    </div>

                    <div className={`home-details-container ${showDetails ? "show" : ""}`}>
                        {mapUrl ? (
                            <div className="home-map-container">
                                <iframe title="Google Map" src={mapUrl} width="100%" height="150" style={{ border: 0 }} allowFullScreen="" loading="lazy" referrerPolicy="no-referrer-when-downgrade"></iframe>
                            </div>
                        ) : (
                            <div className="home-map-placeholder"><FaMapMarkerAlt size={24} /> <p>Map Not Available</p></div>
                        )}
                        
                        {/* FIX: Use correct lowercase keys for all details */}
                        <div className="home-info-row"><FaMapMarkerAlt size={14} /> <span>{restaurant.address || "No address provided."}</span></div>
                        <div className="home-info-row"><FaRegStickyNote size={14} /> <span>{restaurant.description || "No description provided."}</span></div>
                        <div className="home-info-row">
                            <FaClock size={14} />
                            <span>
                                <span className={isRestaurantOpen ? "home-status-open" : "home-status-closed"}>{openStatus}</span>
                                {" • "}
                                {restaurant.opening_time && restaurant.closing_time ? `${restaurant.opening_time.substring(0, 5)} - ${restaurant.closing_time.substring(0, 5)}` : "Hours unknown."}
                            </span>
                        </div>
                        <div className="home-info-row"><FaMoneyBillWave size={14} /> <span>{restaurant.price_range} per person</span></div>
                        <div className="home-info-row"><FaPhone size={14} /> <span>{restaurant.phone || "No phone number provided."}</span></div>
                    </div>

                    <div className="home-bottom-fixed">
                        <div className="home-button-group">
                            <button type="button" className="home-action-button home-skip" onClick={handleSkip}><FaTimes /></button>
                            <button type="button" className="home-action-button home-undo" onClick={handleUndo}><FaUndoAlt /></button>
                            <button type="button" className="home-action-button home-favorite" onClick={handleFavorite}><FaHeart /></button>
                            <button type="button" className="home-action-button home-eat" onClick={handleEat}><FaUtensils /></button>
                        </div>
                        <div className="home-swipe-indicator-bottom" onClick={toggleDetails}>
                            {showDetails ? <FaChevronDown /> : <FaChevronUp />}
                        </div>
                    </div>
                </div>
            </div>

            <footer className="home-footer">
                © {new Date().getFullYear()} NomNom AI. All rights reserved.
            </footer>
        </div>
    );
}
