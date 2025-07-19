import React, { useState, useEffect, useCallback } from "react";
import "../styles/HomePage.css";
import {
    FaTimes, FaUndoAlt, FaHeart, FaUtensils, FaChevronUp, FaChevronDown,
    FaStar, FaStarHalfAlt, FaRegStar, FaMapMarkerAlt, FaRegStickyNote,
    FaClock, FaMoneyBillWave, FaPhone,
} from "react-icons/fa";
import { useNavigate } from "react-router-dom";

export default function HomePage() {
    // No changes to initial state, except starting with null for a clearer loading state
    const [restaurants, setRestaurants] = useState(null); 
    const [currentIndex, setCurrentIndex] = useState(0);
    const [showDetails, setShowDetails] = useState(false);
    const navigate = useNavigate();

    // --- NEW: State for infinite scroll ---
    const [isLoadingMore, setIsLoadingMore] = useState(false);
    const [hasFinished, setHasFinished] = useState(false);

    // --- REVISED: Data fetching logic ---
    const fetchRecommendations = useCallback((exclude_ids = []) => {
        // Don't fetch if we're already fetching or if we know there are no more results
        if (isLoadingMore || hasFinished) return;

        setIsLoadingMore(true);
        const token = localStorage.getItem("token");
        if (!token) {
            navigate("/login");
            return;
        }

        fetch("https://nomnom-ai.onrender.com/api/recommend", {
            method: 'POST', // Use POST to send a body
            headers: {
                'Content-Type': 'application/json',
                "Authorization": `Bearer ${token}`,
            },
            body: JSON.stringify({ exclude_ids }), // Send IDs of restaurants already seen
        })
        .then(res => {
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
        .then(data => {
            if (data.recommendations && data.recommendations.length > 0) {
                // Append new restaurants to the existing list
                setRestaurants(prev => [...(prev || []), ...data.recommendations]);
            } else {
                // If the API returns an empty list, it means we've reached the end
                setHasFinished(true);
            }
        })
        .catch(err => {
            console.error("API fetch error:", err);
        })
        .finally(() => {
            setIsLoadingMore(false);
        });
    }, [navigate, isLoadingMore, hasFinished]);

    // Initial fetch when the component mounts
    useEffect(() => {
        fetchRecommendations([]);
    }, [fetchRecommendations]); // Note: fetchRecommendations is not a dependency to prevent re-fetching

    // --- REVISED: Event Handlers ---
    const handleNextCard = useCallback(() => {
        const nextIndex = currentIndex + 1;
        // Check if we need to fetch more data (e.g., when 3 cards away from the end)
        if (restaurants && nextIndex >= restaurants.length - 3) {
            const currentIds = restaurants.map(r => r.id);
            fetchRecommendations(currentIds);
        }
        setCurrentIndex(nextIndex);
        setShowDetails(false);
    }, [currentIndex, restaurants, fetchRecommendations]);

    const handleSkip = (e) => {
        if (e) e.stopPropagation();
        handleNextCard();
    };

    const handleEat = (e) => {
        if (e) e.stopPropagation();
        console.log("Eat clicked!", restaurants[currentIndex].id);
        handleNextCard();
    };
    
    // Undo logic is now simpler, no looping
    const handleUndo = (e) => {
        if (e) e.stopPropagation();
        if (currentIndex > 0) {
            setCurrentIndex((prevIndex) => prevIndex - 1);
        }
        setShowDetails(false);
    };

    // --- NEW: Revised Loading and Finished States ---
    if (restaurants === null) {
        return <p className="loading">Finding recommendations for you...</p>;
    }
    
    // This state shows when you've swiped past all loaded cards, but more are coming
    if (currentIndex >= restaurants.length && isLoadingMore) {
        return <p className="loading">Finding more recommendations...</p>;
    }

    // This state shows when you've swiped past all cards AND the server has no more to give
    if (currentIndex >= restaurants.length && hasFinished) {
        return (
            <div className="home-container">
                <header className="home-header"><img src="/nomnom-ai-long-logo.PNG" alt="NomNom AI Logo" className="home-logo" /></header>
                <div className="finished-container">
                    <h2>You've seen it all!</h2>
                    <p>There are no more recommendations for you right now. Check back later!</p>
                    <button className="finished-button" onClick={() => window.location.reload()}>Start Over</button>
                </div>
                <footer className="home-footer">© {new Date().getFullYear()} NomNom AI. All rights reserved.</footer>
            </div>
        );
    }
    
    // This handles the case where the initial fetch returns nothing
    if (restaurants.length === 0) {
        return <p className="loading">No recommendations available at the moment. Please try again later.</p>;
    }

    // --- No changes below this line, except for the event handlers on the buttons ---
    const restaurant = restaurants[currentIndex];
    const toggleDetails = (e) => { if (e) e.stopPropagation(); setShowDetails((prev) => !prev); };
    const handleFavorite = (e) => { if (e) e.stopPropagation(); console.log("Favorite clicked!", restaurant.id); };
    const getStars = (rating) => { const r = Math.round(rating * 2) / 2; const f = Math.floor(r); const h = r - f >= 0.5; return [...Array(5)].map((_, i) => { if (i < f) return <FaStar key={i} color="#FFD700" />; if (i === f && h) return <FaStarHalfAlt key={i} color="#FFD700" />; return <FaRegStar key={i} color="#CCCCCC" />; }); };
    const getOpenStatus = (o, c) => { if (!o || !c) return { status: 'Unknown', isOpen: false }; const n = new Date(); const t = n.getHours() * 60 + n.getMinutes(); const [oh, om] = o.split(':').map(Number); const [ch, cm] = c.split(':').map(Number); let ot = oh * 60 + om; let ct = ch * 60 + cm; if (ct < ot) { return { status: (t >= ot || t < ct) ? 'Open' : 'Closed', isOpen: (t >= ot || t < ct) }; } else { return { status: (t >= ot && t < ct) ? 'Open' : 'Closed', isOpen: (t >= ot && t < ct) }; } };
    const getMapUrl = (l) => { if (!l) return null; const [lat, lon] = l.split(','); if (lat && lon) { return `https://www.google.com/maps/embed/v1/place?key=YOUR_MAPS_API_KEY&q=${lat},${lon}`; } return null; };
    const { status: openStatus, isOpen: isRestaurantOpen } = getOpenStatus(restaurant.opening_time, restaurant.closing_time);
    const mapUrl = getMapUrl(restaurant.location);

    return (
        <div className="home-container">
            <header className="home-header"><img src="/nomnom-ai-long-logo.PNG" alt="NomNom AI Logo" className="home-logo" /></header>
            <div className={`home-image-box ${showDetails ? "expanded" : ""}`}>
                <img src={`/images/${restaurant.id.toLowerCase()}.png`} alt={restaurant.name} className="home-restaurant-image" />
                <div className="home-image-gradient"></div>
                <div className="home-image-content">
                    <div className="home-top-info-container">
                        <div className="home-name-rating-container"><h2 className="home-restaurant-name">{restaurant.name}</h2><p className="home-restaurant-rating">{Number(restaurant.google_rating || 0).toFixed(1)}{" "}{getStars(Number(restaurant.google_rating || 0))}</p></div>
                        <div className="home-pill-container">{restaurant.tags.map((tag, index) => (<span key={index} className="home-pill-box home-tag">{tag}</span>))}{!showDetails && (<span className="home-pill-box home-price">{restaurant.price_range}</span>)}</div>
                    </div>
                    <div className={`home-details-container ${showDetails ? "show" : ""}`}>
                        {mapUrl ? (<div className="home-map-container"><iframe title="Google Map" src={mapUrl} width="100%" height="150" style={{ border: 0 }} allowFullScreen="" loading="lazy" referrerPolicy="no-referrer-when-downgrade"></iframe></div>) : (<div className="home-map-placeholder"><FaMapMarkerAlt size={24} /> <p>Map Not Available</p></div>)}
                        <div className="home-info-row"><FaMapMarkerAlt size={14} /> <span>{restaurant.address || "No address provided."}</span></div>
                        <div className="home-info-row"><FaRegStickyNote size={14} /> <span>{restaurant.description || "No description provided."}</span></div>
                        <div className="home-info-row"><FaClock size={14} /><span><span className={isRestaurantOpen ? "home-status-open" : "home-status-closed"}>{openStatus}</span>{" • "}{restaurant.opening_time && restaurant.closing_time ? `${restaurant.opening_time.substring(0, 5)} - ${restaurant.closing_time.substring(0, 5)}` : "Hours unknown."}</span></div>
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
                        <div className="home-swipe-indicator-bottom" onClick={toggleDetails}>{showDetails ? <FaChevronDown /> : <FaChevronUp />}</div>
                    </div>
                </div>
            </div>
            <footer className="home-footer">© {new Date().getFullYear()} NomNom AI. All rights reserved.</footer>
        </div>
    );
}
