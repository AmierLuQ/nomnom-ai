import React, { useState, useEffect, useCallback } from "react";
import "../styles/HomePage.css";
import {
    FaTimes, FaUndoAlt, FaHeart, FaUtensils, FaChevronUp, FaChevronDown,
    FaStar, FaStarHalfAlt, FaRegStar, FaMapMarkerAlt, FaRegStickyNote,
    FaClock, FaMoneyBillWave, FaPhone,
} from "react-icons/fa";
import { useNavigate } from "react-router-dom";

// A new component for styled status screens (Loading, Finished, etc.)
const StatusScreen = ({ message, showLogo = true }) => (
    <div className="home-container">
        <div className="status-container">
            {showLogo && <img src="/nomnom-ai logo.PNG" alt="NomNom AI Logo" className="status-logo" />}
            <p className="status-message">{message}</p>
        </div>
    </div>
);


export default function HomePage() {
    const [restaurants, setRestaurants] = useState(null);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [showDetails, setShowDetails] = useState(false);
    const [isLoadingMore, setIsLoadingMore] = useState(false);
    const [hasFinished, setHasFinished] = useState(false);
    const navigate = useNavigate();

    // This function now handles fetching and appending data
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
                // If it was the first fetch and it's empty, set an empty array.
                if (currentRestaurantIds.length === 0) {
                    setRestaurants([]);
                } else {
                // If it was a subsequent fetch that's empty, we've reached the end.
                    setHasFinished(true);
                }
            }
        })
        .catch(err => {
            console.error("API fetch error:", err);
            if (restaurants === null) setRestaurants([]); // Handle error on initial load
        })
        .finally(() => {
            setIsLoadingMore(false);
        });
    }, [navigate, isLoadingMore, hasFinished, restaurants]);

    // This useEffect hook runs ONLY ONCE to get the initial data.
    useEffect(() => {
        // We need to use a non-hook function inside because of ESLint rules
        const initialLoad = () => {
             loadRecommendations();
        }
        initialLoad();
    }, []); // Empty dependency array ensures it runs once on mount.

    // --- Event Handlers ---
    const handleNextCard = () => {
        const nextIndex = currentIndex + 1;
        // Check if we need to fetch more data
        if (restaurants && nextIndex >= restaurants.length - 2 && !isLoadingMore && !hasFinished) {
            const currentIds = restaurants.map(r => r.id);
            loadRecommendations(currentIds);
        }
        setCurrentIndex(nextIndex);
        setShowDetails(false);
    };

    const handleSkip = (e) => { e.stopPropagation(); handleNextCard(); };
    const handleEat = (e) => { e.stopPropagation(); console.log("Eat!", restaurants[currentIndex]?.id); handleNextCard(); };
    const handleUndo = (e) => { e.stopPropagation(); if (currentIndex > 0) setCurrentIndex(c => c - 1); setShowDetails(false); };
    const handleFavorite = (e) => { e.stopPropagation(); console.log("Favorite!", restaurants[currentIndex]?.id); };

    // --- RENDER LOGIC ---
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
                        <img src="/nomnom-ai-text-logo.PNG" alt="NomNom AI Logo" className="status-logo" />
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
                    <div className="home-top-info-container"><div className="home-name-rating-container"><h2 className="home-restaurant-name">{restaurant.name}</h2><p className="home-restaurant-rating">{Number(restaurant.google_rating || 0).toFixed(1)}{" "}{getStars(Number(restaurant.google_rating || 0))}</p></div><div className="home-pill-container">{restaurant.tags.map((tag, index) => (<span key={index} className="home-pill-box home-tag">{tag}</span>))}{!showDetails && (<span className="home-pill-box home-price">{restaurant.price_range}</span>)}</div></div>
                    <div className={`home-details-container ${showDetails ? "show" : ""}`}>
                        {mapUrl ? (<div className="home-map-container"><iframe title="Google Map" src={mapUrl} width="100%" height="150" style={{ border: 0 }} allowFullScreen="" loading="lazy" referrerPolicy="no-referrer-when-downgrade"></iframe></div>) : (<div className="home-map-placeholder"><FaMapMarkerAlt size={24} /> <p>Map Not Available</p></div>)}
                        <div className="home-info-row"><FaMapMarkerAlt size={14} /> <span>{restaurant.address || "No address provided."}</span></div>
                        <div className="home-info-row"><FaRegStickyNote size={14} /> <span>{restaurant.description || "No description provided."}</span></div>
                        <div className="home-info-row"><FaClock size={14} /><span><span className={isRestaurantOpen ? "home-status-open" : "home-status-closed"}>{openStatus}</span>{" • "}{restaurant.opening_time && restaurant.closing_time ? `${restaurant.opening_time.substring(0, 5)} - ${restaurant.closing_time.substring(0, 5)}` : "Hours unknown."}</span></div>
                        <div className="home-info-row"><FaMoneyBillWave size={14} /> <span>{restaurant.price_range} per person</span></div>
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
