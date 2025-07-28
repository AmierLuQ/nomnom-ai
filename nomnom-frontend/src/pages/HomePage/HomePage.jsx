import React, { useState, useEffect, useCallback, useRef } from "react";
import "./HomePage.css";
import {
    FaTimes, FaUndoAlt, FaHeart, FaUtensils, FaChevronUp, FaChevronDown,
    FaStar, FaStarHalfAlt, FaRegStar, FaMapMarkerAlt, FaRegStickyNote,
    FaClock, FaMoneyBillWave, FaPhone, FaUserCircle
} from "react-icons/fa";
import { useNavigate } from "react-router-dom";

import StatusScreen from "../../components/StatusScreen/StatusScreen"; 
import nomnomTextLogo from '../../assets/images/nomnom-ai-text-logo.PNG';
import nomnomLongLogo from '../../assets/images/nomnom-ai-long-logo.PNG';

export default function HomePage() {
    const [restaurants, setRestaurants] = useState(null);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [showDetails, setShowDetails] = useState(false);
    const [isLoadingMore, setIsLoadingMore] = useState(false);
    const [hasFinished, setHasFinished] = useState(false);
    const navigate = useNavigate();
    const [username, setUsername] = useState('');
    
    // State for rating modal
    const [showRatingModal, setShowRatingModal] = useState(false);
    const [rating, setRating] = useState(0);
    const [hoverRating, setHoverRating] = useState(0);
    const [ratingSuccess, setRatingSuccess] = useState(false);

    const isInitialLoad = useRef(true);

    useEffect(() => {
        const storedUsername = localStorage.getItem("username");
        if (storedUsername) {
            setUsername(storedUsername);
        }
    }, []);

    const loadRecommendations = useCallback((currentRestaurantIds = []) => {
        if (isLoadingMore || hasFinished) return;
        setIsLoadingMore(true);

        const token = localStorage.getItem("token");
        if (!token) {
            navigate("/login");
            return;
        }

        fetch("https://nomnom-ai.onrender.com/api/recommend", {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', "Authorization": `Bearer ${token}` },
            body: JSON.stringify({ exclude_ids: currentRestaurantIds }),
        })
        .then(res => {
            if (!res.ok) throw new Error("API response was not ok.");
            return res.json();
        })
        .then(data => {
            if (data.recommendations && data.recommendations.length > 0) {
                setRestaurants(prev => [...(prev || []), ...data.recommendations]);
            } else {
                if (currentRestaurantIds.length === 0) {
                    setRestaurants([]);
                } else {
                    setHasFinished(true);
                }
            }
        })
        .catch(err => {
            console.error("API fetch error:", err);
            setRestaurants([]);
        })
        .finally(() => {
            setIsLoadingMore(false);
        });
    }, [navigate, hasFinished, isLoadingMore]);

    useEffect(() => {
        if (isInitialLoad.current) {
            isInitialLoad.current = false;
            loadRecommendations();
        }
    }, [loadRecommendations]);

    const handleNextCard = () => {
        const nextIndex = currentIndex + 1;
        if (restaurants && nextIndex >= restaurants.length - 2 && !isLoadingMore && !hasFinished) {
            const currentIds = restaurants.map(r => r.id);
            loadRecommendations(currentIds);
        }
        setCurrentIndex(nextIndex);
        setShowDetails(false);
    };

    const handleSkip = (e) => { e.stopPropagation(); handleNextCard(); };
    
    const handleEat = (e) => {
        e.stopPropagation();
        console.log("Eat!", restaurants[currentIndex]?.id);
        setShowRatingModal(true);
    };

    const handleUndo = (e) => { e.stopPropagation(); if (currentIndex > 0) setCurrentIndex(c => c - 1); setShowDetails(false); };
    const handleFavorite = (e) => { e.stopPropagation(); console.log("Favorite!", restaurants[currentIndex]?.id); };

    const formatPriceRange = (priceRangeString) => {
        if (!priceRangeString) return '';
        return priceRangeString.replace(/\.00/g, '');
    };

    const submitRating = async (selectedRating) => {
        const token = localStorage.getItem("token");
        const restaurantId = restaurants[currentIndex]?.id;

        try {
            const response = await fetch("https://nomnom-ai.onrender.com/api/rate", {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({
                    restaurant_id: restaurantId,
                    rating: selectedRating
                }),
            });
            if (!response.ok) {
                throw new Error('Failed to submit rating');
            }
            setRatingSuccess(true);
            setTimeout(() => {
                setShowRatingModal(false);
                setRatingSuccess(false);
                setRating(0);
                handleNextCard();
            }, 2000);

        } catch (error) {
            console.error("Rating submission error:", error);
            setShowRatingModal(false);
            handleNextCard();
        }
    };

    if (restaurants === null) {
        return <StatusScreen message="Finding recommendations for you..." />;
    }

    if (restaurants.length === 0) {
        return <StatusScreen message="No recommendations available at the moment. Please try again later." />;
    }

    if (currentIndex >= restaurants.length) {
        if (hasFinished) {
            return (
                 <div className="home-container">
                    <div className="status-container finished-container">
                        <img src={nomnomTextLogo} alt="NomNom AI Logo" className="status-logo" />
                        <h2 className="finished-header">You've seen it all!</h2>
                        <p className="status-message">There are no more recommendations for you right now. Check back later!</p>
                        <button className="finished-button" onClick={() => window.location.reload()}>Start Over</button>
                    </div>
                </div>
            );
        }
        return <StatusScreen message="Finding more recommendations..." />;
    }

    const restaurant = restaurants[currentIndex];
    const toggleDetails = (e) => { if (e) e.stopPropagation(); setShowDetails((prev) => !prev); };
    const getStars = (rating) => { const r = Math.round(rating * 2) / 2; const f = Math.floor(r); const h = r - f >= 0.5; return [...Array(5)].map((_, i) => { if (i < f) return <FaStar key={i} color="#FFD700" />; if (i === f && h) return <FaStarHalfAlt key={i} color="#FFD700" />; return <FaRegStar key={i} color="#CCCCCC" />; }); };
    
    const getOpenStatus = (openingHours, closingHours) => {
        if (!openingHours || !closingHours) return { status: 'Open 24/7', isOpen: true };
        if (openingHours === closingHours) return { status: 'Open 24/7', isOpen: true };
        const now = new Date();
        const currentTime = now.getHours() * 60 + now.getMinutes();
        const [openHour, openMinute] = openingHours.split(':').map(Number);
        const [closeHour, closeMinute] = closingHours.split(':').map(Number);
        let openTimeInMinutes = openHour * 60 + openMinute;
        let closeTimeInMinutes = closeHour * 60 + closeMinute;
        if (closeTimeInMinutes < openTimeInMinutes) {
            return { status: (currentTime >= openTimeInMinutes || currentTime < closeTimeInMinutes) ? 'Open' : 'Closed', isOpen: (currentTime >= openTimeInMinutes || currentTime < closeTimeInMinutes) };
        } else {
            return { status: (currentTime >= openTimeInMinutes && currentTime < closeTimeInMinutes) ? 'Open' : 'Closed', isOpen: (currentTime >= openTimeInMinutes && currentTime < closeTimeInMinutes) };
        }
    };

    const getMapUrl = (l) => {
    if (!l) return null;
    const [lat, lon] = l.split(',');
    
    // Get the API key securely from the environment variable
    const apiKey = process.env.REACT_APP_Maps_API_KEY;

    if (lat && lon && apiKey) {
        return `https://www.google.com/maps/embed/v1/place?key=${apiKey}&q=${lat},${lon}`;
    }
    // If the key is missing, return null to avoid showing a broken map
    return null; 
};
    const { status: openStatus, isOpen: isRestaurantOpen } = getOpenStatus(restaurant.opening_time, restaurant.closing_time);
    const mapUrl = getMapUrl(restaurant.location);

    return (
        <div className="home-container">
            {showRatingModal && (
                <div className="rating-modal-overlay">
                    <div className="rating-modal-content">
                        {!ratingSuccess ? (
                            <>
                                <h2>Rate your meal at</h2>
                                <h3>{restaurant.name}</h3>
                                <div className="rating-stars">
                                    {[1, 2, 3, 4, 5].map((star) => (
                                        <FaStar
                                            key={star}
                                            className="rating-star"
                                            color={(hoverRating || rating) >= star ? "#FFD700" : "#CCCCCC"}
                                            onMouseEnter={() => setHoverRating(star)}
                                            onMouseLeave={() => setHoverRating(0)}
                                            onClick={() => {
                                                setRating(star);
                                                submitRating(star);
                                            }}
                                        />
                                    ))}
                                </div>
                                <button className="rating-skip-button" onClick={() => { setShowRatingModal(false); handleNextCard(); }}>
                                    Skip Rating
                                </button>
                            </>
                        ) : (
                            <div className="rating-success-message">
                                <p>Thank you for your feedback!</p>
                            </div>
                        )}
                    </div>
                </div>
            )}
            
            <header className="home-header">
                <img src={nomnomLongLogo} alt="NomNom AI Logo" className="home-logo" />
                <div className="home-user-info">
                    <span className="home-welcome-text">Hi, {username}!</span>
                    <button className="home-profile-button" onClick={() => navigate('/profile')}>
                        <FaUserCircle />
                    </button>
                </div>
            </header>
            <div className={`home-image-box ${showDetails ? "expanded" : ""}`}>
                <img src={`/images/${restaurant.id.toLowerCase()}.png`} alt={restaurant.name} className="home-restaurant-image" />
                <div className="home-image-gradient"></div>
                <div className="home-image-content">
                    <div className="home-top-info-container"><div className="home-name-rating-container"><h2 className="home-restaurant-name">{restaurant.name}</h2><p className="home-restaurant-rating">{Number(restaurant.google_rating || 0).toFixed(1)}{" "}{getStars(Number(restaurant.google_rating || 0))}</p></div><div className="home-pill-container">{restaurant.tags.map((tag, index) => (<span key={index} className="home-pill-box home-tag">{tag}</span>))}{!showDetails && (<span className="home-pill-box home-price">{formatPriceRange(restaurant.price_range)}</span>)}</div></div>
                    <div className={`home-details-container ${showDetails ? "show" : ""}`}>
                        {mapUrl ? (<div className="home-map-container"><iframe title="Google Map" src={mapUrl} width="100%" height="150" style={{ border: 0 }} allowFullScreen="" loading="lazy" referrerPolicy="no-referrer-when-downgrade"></iframe></div>) : (<div className="home-map-placeholder"><FaMapMarkerAlt size={24} /> <p>Map Not Available</p></div>)}
                        <div className="home-info-row"><FaMapMarkerAlt size={14} /> <span>{restaurant.address || "No address provided."}</span></div>
                        <div className="home-info-row"><FaRegStickyNote size={14} /> <span>{restaurant.description || "No description provided."}</span></div>
                        <div className="home-info-row">
                            <FaClock size={14} />
                            <span>
                                <span className={isRestaurantOpen ? "home-status-open" : "home-status-closed"}>{openStatus}</span>
                                {openStatus !== 'Open 24/7' && restaurant.opening_time && restaurant.closing_time ? ` • ${restaurant.opening_time.substring(0, 5)} - ${restaurant.closing_time.substring(0, 5)}` : ""}
                            </span>
                        </div>
                        <div className="home-info-row"><FaMoneyBillWave size={14} /> <span>{formatPriceRange(restaurant.price_range)} per person</span></div>
                        <div className="home-info-row"><FaPhone size={14} /> <span>{restaurant.phone || "No phone number provided."}</span></div>
                    </div>
                    <div className="home-bottom-fixed">
                        <div className="home-button-group"><button type="button" className="home-action-button home-skip" onClick={handleSkip}><FaTimes /></button><button type="button" className="home-action-button home-undo" onClick={handleUndo}><FaUndoAlt /></button><button type="button" className="home-action-button home-favorite" onClick={handleFavorite}><FaHeart /></button><button type="button" className="home-action-button home-eat" onClick={handleEat}><FaUtensils /></button></div>
                        <div className="home-swipe-indicator-bottom" onClick={toggleDetails}>{showDetails ? <FaChevronDown /> : <FaChevronUp />}</div>
                    </div>
                </div>
            </div>
            <footer className="home-footer">© {new Date().getFullYear()} NomNom AI. All rights reserved.</footer>
        </div>
    );
}
