import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FaArrowLeft, FaUtensils, FaTags, FaStar, FaSignOutAlt, FaEdit, FaTimes } from 'react-icons/fa';
import '../styles/ProfilePage.css';

const ProfileLoadingScreen = () => (
    <div className="profile-container">
        <div className="loading-message">Loading Profile...</div>
    </div>
);

export default function ProfilePage() {
    const [profileData, setProfileData] = useState(null);
    const [isEditing, setIsEditing] = useState(false);
    const [formData, setFormData] = useState({ name: '', phone: '' });
    const navigate = useNavigate();

    useEffect(() => {
        const token = localStorage.getItem("token");
        if (!token) {
            navigate("/login");
            return;
        }

        fetch("https://nomnom-ai.onrender.com/api/profile", {
            headers: { "Authorization": `Bearer ${token}` },
        })
        .then(res => {
            if (!res.ok) {
                localStorage.removeItem("token");
                localStorage.removeItem("username");
                navigate("/login");
                throw new Error("Session expired");
            }
            return res.json();
        })
        .then(data => {
            setProfileData(data);
            setFormData({
                name: data.user_info.name,
                phone: data.user_info.phone || '',
            });
        })
        .catch(err => console.error("Failed to fetch profile data:", err));
    }, [navigate]);

    const handleLogout = () => {
        localStorage.removeItem("token");
        localStorage.removeItem("username");
        navigate("/login");
    };

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleUpdateProfile = (e) => {
        e.preventDefault();
        const token = localStorage.getItem("token");

        fetch("https://nomnom-ai.onrender.com/api/profile/update", {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                "Authorization": `Bearer ${token}`,
            },
            body: JSON.stringify(formData),
        })
        .then(res => res.json())
        .then(data => {
            alert(data.message);
            if (data.user) {
                setProfileData(prev => ({ ...prev, user_info: data.user }));
                setIsEditing(false);
            }
        })
        .catch(err => console.error("Failed to update profile:", err));
    };

    if (!profileData) {
        return <ProfileLoadingScreen />;
    }

    const { user_info, stats, recent_meals } = profileData;

    return (
        <div className="profile-container">
            <header className="profile-header">
                <button className="profile-back-button" onClick={() => navigate('/home')}><FaArrowLeft /></button>
                <h1 className="profile-title">My Profile</h1>
                <button className="profile-edit-button" onClick={() => setIsEditing(true)}><FaEdit /></button>
            </header>

            <main className="profile-content">
                <section className="profile-card">
                    <div className="profile-avatar">{user_info.username.charAt(0).toUpperCase()}</div>
                    <h2 className="profile-username">{user_info.username}</h2>
                    <p className="profile-name">{user_info.name}</p>
                    <p className="profile-email">{user_info.email}</p>
                </section>

                <section className="profile-stats">
                    <div className="stat-card"><FaUtensils className="stat-icon" /><span className="stat-value">{stats.total_meals}</span><span className="stat-label">Meals Eaten</span></div>
                    <div className="stat-card"><FaTags className="stat-icon" /><span className="stat-value">{stats.favorite_cuisine || 'N/A'}</span><span className="stat-label">Favorite Cuisine</span></div>
                    <div className="stat-card"><FaStar className="stat-icon" /><span className="stat-value">{stats.average_rating.toFixed(1)}</span><span className="stat-label">Average Rating</span></div>
                </section>

                <section className="profile-history">
                    <h3 className="history-title">Recent Activity</h3>
                    <ul className="history-list">
                        {recent_meals.length > 0 ? (
                            recent_meals.map((meal) => (
                                <li key={meal.meal_id} className="history-item">
                                    <div className="history-item-info">
                                        <span className="history-item-name">{meal.restaurant_name}</span>
                                        <span className="history-item-date">{new Date(meal.date).toLocaleDateString()}</span>
                                    </div>
                                    <div className="history-item-rating">{meal.rating ? `${meal.rating.toFixed(1)} ★` : 'Not Rated'}</div>
                                </li>
                            ))
                        ) : (
                            <p className="history-empty">No recent meals to show.</p>
                        )}
                    </ul>
                </section>

                <button className="profile-logout-button" onClick={handleLogout}><FaSignOutAlt /> Logout</button>
            </main>

            {isEditing && (
                <div className="modal-overlay">
                    <div className="modal-content">
                        <button className="modal-close-button" onClick={() => setIsEditing(false)}><FaTimes /></button>
                        <h3 className="modal-title">Edit Profile</h3>
                        <form className="modal-form" onSubmit={handleUpdateProfile}>
                            <div className="modal-input-group">
                                <label htmlFor="name">Full Name</label>
                                <input type="text" id="name" name="name" value={formData.name} onChange={handleInputChange} required />
                            </div>
                            <div className="modal-input-group">
                                <label htmlFor="phone">Phone Number</label>
                                <input type="tel" id="phone" name="phone" value={formData.phone} onChange={handleInputChange} />
                            </div>
                            <button type="submit" className="modal-save-button">Save Changes</button>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
