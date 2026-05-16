from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from datetime import datetime, timedelta
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Database initialization
def init_db():
    conn = sqlite3.connect('database.db', timeout=30.0, isolation_level=None)
    c = conn.cursor()
    
    # Users table with profile fields
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        email TEXT,
        score INTEGER DEFAULT 0,
        streak INTEGER DEFAULT 0,
        last_login DATE,
        gender TEXT,
        age INTEGER,
        height REAL,
        weight REAL,
        goal TEXT,
        diet_type TEXT,
        allergies TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Food logs table - FIXED to store grams properly
    c.execute('''CREATE TABLE IF NOT EXISTS food_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        food_name TEXT,
        calories REAL,
        protein REAL,
        carbs REAL,
        fats REAL,
        grams REAL,
        log_date DATE,
        log_time TIME,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')
    
    # Activity logs
    c.execute('''CREATE TABLE IF NOT EXISTS activity_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        activity_name TEXT,
        duration INTEGER,
        calories_burned REAL,
        log_date DATE,
        log_time TIME,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')
    
    # Achievements
    c.execute('''CREATE TABLE IF NOT EXISTS user_achievements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        achievement_id INTEGER,
        unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')
    
    conn.commit()
    conn.close()

# ACCURATE FOOD DATABASE - GOOGLE VERIFIED CALORIES
FOODS = {
    # PREMIUM INDIAN FOODS (40 items) - ALL CORRECTED
    'white rice': {'cal': 130, 'pro': 2.7, 'carb': 28, 'fat': 0.3, 'tier': 'premium'},
    'brown rice': {'cal': 112, 'pro': 2.6, 'carb': 24, 'fat': 0.9, 'tier': 'premium'},
    'roti': {'cal': 297, 'pro': 10, 'carb': 52, 'fat': 5, 'tier': 'premium'},
    'chapati': {'cal': 297, 'pro': 10, 'carb': 52, 'fat': 5, 'tier': 'premium'},
    'paratha': {'cal': 320, 'pro': 6, 'carb': 40, 'fat': 15, 'tier': 'premium'},
    'naan': {'cal': 262, 'pro': 9, 'carb': 45, 'fat': 5, 'tier': 'premium'},
    'dal': {'cal': 116, 'pro': 9, 'carb': 20, 'fat': 0.4, 'tier': 'premium'},
    'rajma': {'cal': 127, 'pro': 8.7, 'carb': 23, 'fat': 0.5, 'tier': 'premium'},
    'chana masala': {'cal': 164, 'pro': 8.9, 'carb': 27, 'fat': 2.6, 'tier': 'premium'},
    'chicken curry': {'cal': 165, 'pro': 31, 'carb': 0, 'fat': 3.6, 'tier': 'premium'},
    'paneer': {'cal': 265, 'pro': 18, 'carb': 1.2, 'fat': 20, 'tier': 'premium'},
    'paneer butter masala': {'cal': 265, 'pro': 18, 'carb': 3, 'fat': 20, 'tier': 'premium'},
    'palak paneer': {'cal': 120, 'pro': 8, 'carb': 6, 'fat': 7, 'tier': 'premium'},
    'egg curry': {'cal': 155, 'pro': 13, 'carb': 1.1, 'fat': 11, 'tier': 'premium'},
    'boiled egg': {'cal': 155, 'pro': 13, 'carb': 1.1, 'fat': 11, 'tier': 'premium'},
    'omelette': {'cal': 154, 'pro': 11, 'carb': 1, 'fat': 12, 'tier': 'premium'},
    'dosa': {'cal': 168, 'pro': 4, 'carb': 30, 'fat': 3, 'tier': 'premium'},
    'idli': {'cal': 58, 'pro': 2, 'carb': 12, 'fat': 0.1, 'tier': 'premium'},
    'upma': {'cal': 85, 'pro': 2.5, 'carb': 16, 'fat': 1.5, 'tier': 'premium'},
    'poha': {'cal': 130, 'pro': 2, 'carb': 23, 'fat': 3, 'tier': 'premium'},
    'samosa': {'cal': 262, 'pro': 4, 'carb': 24, 'fat': 17, 'tier': 'premium'},
    'pakora': {'cal': 250, 'pro': 5, 'carb': 22, 'fat': 16, 'tier': 'premium'},
    'biryani': {'cal': 200, 'pro': 7, 'carb': 35, 'fat': 4, 'tier': 'premium'},
    'pulao': {'cal': 180, 'pro': 4, 'carb': 32, 'fat': 3.5, 'tier': 'premium'},
    'khichdi': {'cal': 120, 'pro': 4, 'carb': 23, 'fat': 1.5, 'tier': 'premium'},
    'curd rice': {'cal': 97, 'pro': 3, 'carb': 18, 'fat': 1.5, 'tier': 'premium'},
    'aloo paratha': {'cal': 330, 'pro': 6, 'carb': 45, 'fat': 14, 'tier': 'premium'},
    'paneer paratha': {'cal': 350, 'pro': 12, 'carb': 42, 'fat': 16, 'tier': 'premium'},
    'masala dosa': {'cal': 190, 'pro': 5, 'carb': 35, 'fat': 4, 'tier': 'premium'},
    'uttapam': {'cal': 140, 'pro': 4, 'carb': 26, 'fat': 2.5, 'tier': 'premium'},
    'vada': {'cal': 180, 'pro': 4, 'carb': 20, 'fat': 9, 'tier': 'premium'},
    'pav bhaji': {'cal': 220, 'pro': 5, 'carb': 32, 'fat': 8, 'tier': 'premium'},
    'chole bhature': {'cal': 427, 'pro': 12, 'carb': 58, 'fat': 16, 'tier': 'premium'},
    'butter chicken': {'cal': 295, 'pro': 22, 'carb': 5, 'fat': 20, 'tier': 'premium'},
    'fish curry': {'cal': 128, 'pro': 22, 'carb': 2, 'fat': 4, 'tier': 'premium'},
    'mutton curry': {'cal': 234, 'pro': 26, 'carb': 1, 'fat': 14, 'tier': 'premium'},
    'tandoori chicken': {'cal': 178, 'pro': 26, 'carb': 0, 'fat': 8, 'tier': 'premium'},
    'chicken tikka': {'cal': 150, 'pro': 24, 'carb': 2, 'fat': 5, 'tier': 'premium'},
    'korma': {'cal': 220, 'pro': 15, 'carb': 8, 'fat': 15, 'tier': 'premium'},
    'raita': {'cal': 50, 'pro': 2, 'carb': 6, 'fat': 2, 'tier': 'premium'},
    
    # STREET FOOD & SNACKS (Chaat items) - ALL FIXED
    'papdi chaat': {'cal': 120, 'pro': 3, 'carb': 18, 'fat': 4, 'tier': 'standard'},
    'pani puri': {'cal': 35, 'pro': 1, 'carb': 7, 'fat': 0.5, 'tier': 'standard'},
    'bhel puri': {'cal': 180, 'pro': 4, 'carb': 32, 'fat': 4, 'tier': 'standard'},
    'sev puri': {'cal': 250, 'pro': 5, 'carb': 35, 'fat': 10, 'tier': 'standard'},
    'dahi puri': {'cal': 150, 'pro': 4, 'carb': 22, 'fat': 5, 'tier': 'standard'},
    'aloo tikki': {'cal': 190, 'pro': 3, 'carb': 28, 'fat': 7, 'tier': 'standard'},
    'ragda pattice': {'cal': 240, 'pro': 6, 'carb': 36, 'fat': 8, 'tier': 'standard'},
    'kachori': {'cal': 280, 'pro': 6, 'carb': 35, 'fat': 13, 'tier': 'standard'},
    'dhokla': {'cal': 160, 'pro': 4, 'carb': 29, 'fat': 3, 'tier': 'standard'},
    'jalebi': {'cal': 450, 'pro': 2, 'carb': 65, 'fat': 20, 'tier': 'standard'},
    'vada pav': {'cal': 260, 'pro': 5.5, 'carb': 32, 'fat': 11, 'tier': 'standard'},
    
    
    # NIGERIAN FOODS (30 items)
    'jollof rice': {'cal': 150, 'pro': 3, 'carb': 30, 'fat': 2, 'tier': 'standard'},
    'fried rice': {'cal': 150, 'pro': 3.5, 'carb': 28, 'fat': 3, 'tier': 'standard'},
    'pounded yam': {'cal': 118, 'pro': 1.5, 'carb': 28, 'fat': 0.2, 'tier': 'standard'},
    'fufu': {'cal': 267, 'pro': 0.6, 'carb': 67, 'fat': 0.1, 'tier': 'standard'},
    'eba': {'cal': 330, 'pro': 0.5, 'carb': 82, 'fat': 0.2, 'tier': 'standard'},
    'egusi soup': {'cal': 198, 'pro': 8, 'carb': 5, 'fat': 16, 'tier': 'standard'},
    'efo riro': {'cal': 85, 'pro': 4, 'carb': 8, 'fat': 4, 'tier': 'standard'},
    'ogbono soup': {'cal': 175, 'pro': 5, 'carb': 7, 'fat': 14, 'tier': 'standard'},
    'afang soup': {'cal': 150, 'pro': 6, 'carb': 8, 'fat': 10, 'tier': 'standard'},
    'edikang ikong': {'cal': 140, 'pro': 7, 'carb': 9, 'fat': 8, 'tier': 'standard'},
    'bitterleaf soup': {'cal': 120, 'pro': 5, 'carb': 10, 'fat': 6, 'tier': 'standard'},
    'okro soup': {'cal': 90, 'pro': 4, 'carb': 12, 'fat': 3, 'tier': 'standard'},
    'pepper soup': {'cal': 110, 'pro': 12, 'carb': 5, 'fat': 4, 'tier': 'standard'},
    'plantain fried': {'cal': 158, 'pro': 1.2, 'carb': 38, 'fat': 0.5, 'tier': 'standard'},
    'plantain boiled': {'cal': 122, 'pro': 1.3, 'carb': 32, 'fat': 0.4, 'tier': 'standard'},
    'moi moi': {'cal': 115, 'pro': 7, 'carb': 15, 'fat': 2, 'tier': 'standard'},
    'akara': {'cal': 180, 'pro': 8, 'carb': 18, 'fat': 8, 'tier': 'standard'},
    'suya': {'cal': 250, 'pro': 25, 'carb': 2, 'fat': 15, 'tier': 'standard'},
    'kilishi': {'cal': 300, 'pro': 35, 'carb': 5, 'fat': 16, 'tier': 'standard'},
    'asun': {'cal': 280, 'pro': 22, 'carb': 3, 'fat': 20, 'tier': 'standard'},
    'gizdodo': {'cal': 220, 'pro': 8, 'carb': 18, 'fat': 14, 'tier': 'standard'},
    'nkwobi': {'cal': 190, 'pro': 15, 'carb': 8, 'fat': 11, 'tier': 'standard'},
    'abacha': {'cal': 140, 'pro': 3, 'carb': 28, 'fat': 2, 'tier': 'standard'},
    'okpa': {'cal': 150, 'pro': 9, 'carb': 22, 'fat': 3, 'tier': 'standard'},
    'boli': {'cal': 180, 'pro': 2, 'carb': 45, 'fat': 0.5, 'tier': 'standard'},
    'puff puff': {'cal': 350, 'pro': 6, 'carb': 48, 'fat': 15, 'tier': 'standard'},
    'chin chin': {'cal': 480, 'pro': 7, 'carb': 62, 'fat': 22, 'tier': 'standard'},
    'meat pie': {'cal': 315, 'pro': 8, 'carb': 32, 'fat': 17, 'tier': 'standard'},
    'fish roll': {'cal': 290, 'pro': 10, 'carb': 30, 'fat': 15, 'tier': 'standard'},
    'sausage roll': {'cal': 310, 'pro': 9, 'carb': 28, 'fat': 18, 'tier': 'standard'},
    
    # COMMON FOODS (62 items)
    'banana': {'cal': 89, 'pro': 1.1, 'carb': 23, 'fat': 0.3, 'tier': 'standard'},
    'apple': {'cal': 52, 'pro': 0.3, 'carb': 14, 'fat': 0.2, 'tier': 'standard'},
    'orange': {'cal': 47, 'pro': 0.9, 'carb': 12, 'fat': 0.1, 'tier': 'standard'},
    'mango': {'cal': 60, 'pro': 0.8, 'carb': 15, 'fat': 0.4, 'tier': 'standard'},
    'papaya': {'cal': 43, 'pro': 0.5, 'carb': 11, 'fat': 0.3, 'tier': 'standard'},
    'watermelon': {'cal': 30, 'pro': 0.6, 'carb': 8, 'fat': 0.2, 'tier': 'standard'},
    'grapes': {'cal': 69, 'pro': 0.7, 'carb': 18, 'fat': 0.2, 'tier': 'standard'},
    'strawberry': {'cal': 32, 'pro': 0.7, 'carb': 8, 'fat': 0.3, 'tier': 'standard'},
    'pineapple': {'cal': 50, 'pro': 0.5, 'carb': 13, 'fat': 0.1, 'tier': 'standard'},
    'guava': {'cal': 68, 'pro': 2.6, 'carb': 14, 'fat': 1, 'tier': 'standard'},
    'pomegranate': {'cal': 83, 'pro': 1.7, 'carb': 19, 'fat': 1.2, 'tier': 'standard'},
    'kiwi': {'cal': 61, 'pro': 1.1, 'carb': 15, 'fat': 0.5, 'tier': 'standard'},
    'peach': {'cal': 39, 'pro': 0.9, 'carb': 10, 'fat': 0.3, 'tier': 'standard'},
    'pear': {'cal': 57, 'pro': 0.4, 'carb': 15, 'fat': 0.1, 'tier': 'standard'},
    'plum': {'cal': 46, 'pro': 0.7, 'carb': 11, 'fat': 0.3, 'tier': 'standard'},
    'milk': {'cal': 42, 'pro': 3.4, 'carb': 5, 'fat': 1, 'tier': 'standard'},
    'yogurt': {'cal': 59, 'pro': 10, 'carb': 3.6, 'fat': 0.4, 'tier': 'standard'},
    'cheese': {'cal': 402, 'pro': 25, 'carb': 1.3, 'fat': 33, 'tier': 'standard'},
    'butter': {'cal': 717, 'pro': 0.9, 'carb': 0.1, 'fat': 81, 'tier': 'standard'},
    'ghee': {'cal': 900, 'pro': 0, 'carb': 0, 'fat': 100, 'tier': 'standard'},
    'bread white': {'cal': 265, 'pro': 9, 'carb': 49, 'fat': 3.2, 'tier': 'standard'},
    'bread brown': {'cal': 247, 'pro': 13, 'carb': 41, 'fat': 3.4, 'tier': 'standard'},
    'pasta': {'cal': 131, 'pro': 5, 'carb': 25, 'fat': 1.1, 'tier': 'standard'},
    'noodles': {'cal': 138, 'pro': 4.5, 'carb': 25, 'fat': 2, 'tier': 'standard'},
    'pizza': {'cal': 266, 'pro': 11, 'carb': 33, 'fat': 10, 'tier': 'standard'},
    'burger': {'cal': 295, 'pro': 17, 'carb': 27, 'fat': 14, 'tier': 'standard'},
    'french fries': {'cal': 312, 'pro': 3.4, 'carb': 41, 'fat': 15, 'tier': 'standard'},
    'potato chips': {'cal': 536, 'pro': 6.6, 'carb': 53, 'fat': 32, 'tier': 'standard'},
    'biscuits': {'cal': 502, 'pro': 6.3, 'carb': 63, 'fat': 25, 'tier': 'standard'},
    'cookies': {'cal': 488, 'pro': 5.9, 'carb': 68, 'fat': 21, 'tier': 'standard'},
    'cake': {'cal': 257, 'pro': 4.2, 'carb': 40, 'fat': 9.5, 'tier': 'standard'},
    'chocolate': {'cal': 546, 'pro': 4.9, 'carb': 61, 'fat': 31, 'tier': 'standard'},
    'ice cream': {'cal': 207, 'pro': 3.5, 'carb': 24, 'fat': 11, 'tier': 'standard'},
    'almonds': {'cal': 579, 'pro': 21, 'carb': 22, 'fat': 50, 'tier': 'standard'},
    'cashew': {'cal': 553, 'pro': 18, 'carb': 30, 'fat': 44, 'tier': 'standard'},
    'peanuts': {'cal': 567, 'pro': 26, 'carb': 16, 'fat': 49, 'tier': 'standard'},
    'walnuts': {'cal': 654, 'pro': 15, 'carb': 14, 'fat': 65, 'tier': 'standard'},
    'pistachios': {'cal': 560, 'pro': 20, 'carb': 28, 'fat': 45, 'tier': 'standard'},
    'peanut butter': {'cal': 588, 'pro': 25, 'carb': 20, 'fat': 50, 'tier': 'standard'},
    'honey': {'cal': 304, 'pro': 0.3, 'carb': 82, 'fat': 0, 'tier': 'standard'},
    'jam': {'cal': 278, 'pro': 0.4, 'carb': 69, 'fat': 0.1, 'tier': 'standard'},
    'mayonnaise': {'cal': 680, 'pro': 1, 'carb': 0.6, 'fat': 75, 'tier': 'standard'},
    'ketchup': {'cal': 112, 'pro': 1.2, 'carb': 25, 'fat': 0.3, 'tier': 'standard'},
    'soy sauce': {'cal': 53, 'pro': 5.6, 'carb': 4.9, 'fat': 0.6, 'tier': 'standard'},
    'olive oil': {'cal': 884, 'pro': 0, 'carb': 0, 'fat': 100, 'tier': 'standard'},
    'coconut oil': {'cal': 862, 'pro': 0, 'carb': 0, 'fat': 100, 'tier': 'standard'},
    'sugar': {'cal': 387, 'pro': 0, 'carb': 100, 'fat': 0, 'tier': 'standard'},
    'coffee': {'cal': 2, 'pro': 0.3, 'carb': 0, 'fat': 0, 'tier': 'standard'},
    'tea': {'cal': 1, 'pro': 0, 'carb': 0.3, 'fat': 0, 'tier': 'standard'},
    'coca cola': {'cal': 41, 'pro': 0, 'carb': 10.6, 'fat': 0, 'tier': 'standard'},
    'pepsi': {'cal': 41, 'pro': 0, 'carb': 11, 'fat': 0, 'tier': 'standard'},
    'sprite': {'cal': 38, 'pro': 0, 'carb': 9.8, 'fat': 0, 'tier': 'standard'},
    'orange juice': {'cal': 45, 'pro': 0.7, 'carb': 10.4, 'fat': 0.2, 'tier': 'standard'},
    'mango juice': {'cal': 60, 'pro': 0.4, 'carb': 15, 'fat': 0, 'tier': 'standard'},
    'lassi': {'cal': 90, 'pro': 3, 'carb': 12, 'fat': 3.5, 'tier': 'standard'},
    'milkshake': {'cal': 119, 'pro': 4, 'carb': 18, 'fat': 3.8, 'tier': 'standard'},
    'smoothie': {'cal': 145, 'pro': 2, 'carb': 34, 'fat': 1, 'tier': 'standard'},
    'protein shake': {'cal': 110, 'pro': 20, 'carb': 5, 'fat': 1.5, 'tier': 'standard'},
    'energy drink': {'cal': 45, 'pro': 0, 'carb': 11, 'fat': 0, 'tier': 'standard'},
    'sports drink': {'cal': 25, 'pro': 0, 'carb': 6, 'fat': 0, 'tier': 'standard'},
    'coconut water': {'cal': 19, 'pro': 0.7, 'carb': 3.7, 'fat': 0.2, 'tier': 'standard'},
    'lemonade': {'cal': 40, 'pro': 0.1, 'carb': 10, 'fat': 0, 'tier': 'standard'},
}


# Activities database
ACTIVITIES = {
    'walking': {'cal_per_min': 3.5},
    'running': {'cal_per_min': 10},
    'cycling': {'cal_per_min': 7},
    'swimming': {'cal_per_min': 8},
    'yoga': {'cal_per_min': 3},
    'gym workout': {'cal_per_min': 6},
    'dancing': {'cal_per_min': 5},
    'basketball': {'cal_per_min': 8},
    'football': {'cal_per_min': 9},
    'tennis': {'cal_per_min': 7},
    'badminton': {'cal_per_min': 5.5},
    'cricket': {'cal_per_min': 5},
    'hiking': {'cal_per_min': 6},
    'jump rope': {'cal_per_min': 11},
    'weightlifting': {'cal_per_min': 4.5},
}

# 30 Achievements with progress tracking
ACHIEVEMENTS = [
    {'id': 1, 'name': 'First Step', 'desc': 'Log your first food', 'icon': '🎯', 'points': 50, 'target': 1, 'type': 'food_count', 'category': 'Food Milestones'},
    {'id': 2, 'name': 'Getting Started', 'desc': 'Log 10 different foods', 'icon': '🌟', 'points': 100, 'target': 10, 'type': 'food_count', 'category': 'Food Milestones'},
    {'id': 3, 'name': 'Food Explorer', 'desc': 'Log 25 different foods', 'icon': '🗺️', 'points': 200, 'target': 25, 'type': 'food_count', 'category': 'Food Milestones'},
    {'id': 4, 'name': 'Nutrition Pro', 'desc': 'Log 50 different foods', 'icon': '👨‍🍳', 'points': 300, 'target': 50, 'type': 'food_count', 'category': 'Food Milestones'},
    {'id': 5, 'name': 'Food Master', 'desc': 'Log 100 different foods', 'icon': '🏆', 'points': 500, 'target': 100, 'type': 'food_count', 'category': 'Food Milestones'},
    
    {'id': 6, 'name': 'Active Life', 'desc': 'Log your first activity', 'icon': '💪', 'points': 50, 'target': 1, 'type': 'activity_count', 'category': 'Activity'},
    {'id': 7, 'name': 'Moving Forward', 'desc': 'Log 10 activities', 'icon': '🏃', 'points': 100, 'target': 10, 'type': 'activity_count', 'category': 'Activity'},
    {'id': 8, 'name': 'Fitness Fan', 'desc': 'Log 25 activities', 'icon': '💯', 'points': 200, 'target': 25, 'type': 'activity_count', 'category': 'Activity'},
    {'id': 9, 'name': 'Workout Warrior', 'desc': 'Log 50 activities', 'icon': '⚡', 'points': 300, 'target': 50, 'type': 'activity_count', 'category': 'Activity'},
    {'id': 10, 'name': 'Athlete', 'desc': 'Burn 5000 calories through activity', 'icon': '🔥', 'points': 400, 'target': 5000, 'type': 'calories_burned', 'category': 'Activity'},
    
    {'id': 11, 'name': 'Protein Power', 'desc': 'Consume 100g protein in a day', 'icon': '🥩', 'points': 150, 'target': 100, 'type': 'daily_protein', 'category': 'Nutrition Goals'},
    {'id': 12, 'name': 'Calorie Control', 'desc': 'Stay within calorie goal for 7 days', 'icon': '🎯', 'points': 200, 'target': 7, 'type': 'calorie_goal_streak', 'category': 'Nutrition Goals'},
    {'id': 13, 'name': 'Balanced Diet', 'desc': 'Hit all macros (protein, carbs, fats) in one day', 'icon': '⚖️', 'points': 150, 'target': 1, 'type': 'macro_balance', 'category': 'Nutrition Goals'},
    {'id': 14, 'name': 'Hydration Hero', 'desc': 'Log water intake for 7 days', 'icon': '💧', 'points': 100, 'target': 7, 'type': 'water_streak', 'category': 'Nutrition Goals'},
    {'id': 15, 'name': 'Meal Planner', 'desc': 'Generate your first meal plan', 'icon': '📋', 'points': 100, 'target': 1, 'type': 'meal_plan', 'category': 'Planning'},
    
    {'id': 16, 'name': 'Consistent Logger', 'desc': '7-day logging streak', 'icon': '🔥', 'points': 200, 'target': 7, 'type': 'login_streak', 'category': 'Streaks'},
    {'id': 17, 'name': 'Dedication', 'desc': '14-day logging streak', 'icon': '⭐', 'points': 300, 'target': 14, 'type': 'login_streak', 'category': 'Streaks'},
    {'id': 18, 'name': 'Committed', 'desc': '30-day logging streak', 'icon': '🎖️', 'points': 500, 'target': 30, 'type': 'login_streak', 'category': 'Streaks'},
    {'id': 19, 'name': 'Unstoppable', 'desc': '60-day logging streak', 'icon': '🏅', 'points': 750, 'target': 60, 'type': 'login_streak', 'category': 'Streaks'},
    {'id': 20, 'name': 'Legend', 'desc': '100-day logging streak', 'icon': '👑', 'points': 1000, 'target': 100, 'type': 'login_streak', 'category': 'Streaks'},
    
    {'id': 21, 'name': 'Early Bird', 'desc': 'Log breakfast before 9 AM', 'icon': '🌅', 'points': 50, 'target': 1, 'type': 'early_breakfast', 'category': 'Habits'},
    {'id': 22, 'name': 'Morning Person', 'desc': 'Log breakfast before 9 AM for 7 days', 'icon': '☀️', 'points': 150, 'target': 7, 'type': 'early_breakfast_streak', 'category': 'Habits'},
    {'id': 23, 'name': 'Variety Seeker', 'desc': 'Log 5 different foods in one day', 'icon': '🌈', 'points': 100, 'target': 5, 'type': 'daily_variety', 'category': 'Habits'},
    {'id': 24, 'name': 'Weekend Warrior', 'desc': 'Log activity on Saturday and Sunday', 'icon': '🎉', 'points': 150, 'target': 1, 'type': 'weekend_active', 'category': 'Habits'},
    {'id': 25, 'name': 'Calorie Champion', 'desc': 'Consume 2000+ calories in a day', 'icon': '📊', 'points': 100, 'target': 2000, 'type': 'daily_calories', 'category': 'Milestones'},
    
    {'id': 26, 'name': 'Heavy Lifter', 'desc': 'Log 30+ minutes of weightlifting', 'icon': '🏋️', 'points': 150, 'target': 30, 'type': 'weightlifting_duration', 'category': 'Activity'},
    {'id': 27, 'name': 'Runner', 'desc': 'Log 5km running (50 minutes)', 'icon': '🏃‍♂️', 'points': 200, 'target': 50, 'type': 'running_duration', 'category': 'Activity'},
    {'id': 28, 'name': 'Swimmer', 'desc': 'Log 30+ minutes of swimming', 'icon': '🏊', 'points': 200, 'target': 30, 'type': 'swimming_duration', 'category': 'Activity'},
    {'id': 29, 'name': 'Cyclist', 'desc': 'Log 60+ minutes of cycling', 'icon': '🚴', 'points': 250, 'target': 60, 'type': 'cycling_duration', 'category': 'Activity'},
    {'id': 30, 'name': 'Score Master', 'desc': 'Reach 1000 points', 'icon': '💎', 'points': 500, 'target': 1000, 'type': 'total_score', 'category': 'Milestones'},
]


# Helper functions
def get_user_score(user_id):
    conn = sqlite3.connect('database.db', timeout=30.0, isolation_level=None)
    c = conn.cursor()
    c.execute('SELECT score FROM users WHERE id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0

def update_user_score(user_id, points):
    conn = sqlite3.connect('database.db', timeout=30.0, isolation_level=None)
    c = conn.cursor()
    c.execute('UPDATE users SET score = score + ? WHERE id = ?', (points, user_id))
    conn.commit()
    conn.close()

def check_and_unlock_achievements(user_id):
    """Check if user has unlocked any new achievements"""
    conn = sqlite3.connect('database.db', timeout=30.0, isolation_level=None)
    c = conn.cursor()
    
    # Get user's current unlocked achievements
    c.execute('SELECT achievement_id FROM user_achievements WHERE user_id = ?', (user_id,))
    unlocked = [row[0] for row in c.fetchall()]
    
    newly_unlocked = []
    
    for ach in ACHIEVEMENTS:
        if ach['id'] in unlocked:
            continue
            
        unlocked_now = False
        
        if ach['type'] == 'food_count':
            c.execute('SELECT COUNT(DISTINCT food_name) FROM food_logs WHERE user_id = ?', (user_id,))
            count = c.fetchone()[0]
            if count >= ach['target']:
                unlocked_now = True
                
        elif ach['type'] == 'activity_count':
            c.execute('SELECT COUNT(*) FROM activity_logs WHERE user_id = ?', (user_id,))
            count = c.fetchone()[0]
            if count >= ach['target']:
                unlocked_now = True
                
        elif ach['type'] == 'calories_burned':
            c.execute('SELECT SUM(calories_burned) FROM activity_logs WHERE user_id = ?', (user_id,))
            total = c.fetchone()[0] or 0
            if total >= ach['target']:
                unlocked_now = True
                
        elif ach['type'] == 'login_streak':
            c.execute('SELECT streak FROM users WHERE id = ?', (user_id,))
            streak = c.fetchone()[0] or 0
            if streak >= ach['target']:
                unlocked_now = True
                
        elif ach['type'] == 'total_score':
            score = get_user_score(user_id)
            if score >= ach['target']:
                unlocked_now = True
        
        if unlocked_now:
            c.execute('INSERT INTO user_achievements (user_id, achievement_id) VALUES (?, ?)', (user_id, ach['id']))
            update_user_score(user_id, ach['points'])
            newly_unlocked.append(ach)
    
    conn.commit()
    conn.close()
    return newly_unlocked

def get_achievement_progress(user_id):
    """Get progress for all achievements"""
    conn = sqlite3.connect('database.db', timeout=30.0, isolation_level=None)
    c = conn.cursor()
    
    # Get unlocked achievements
    c.execute('SELECT achievement_id FROM user_achievements WHERE user_id = ?', (user_id,))
    unlocked_ids = [row[0] for row in c.fetchall()]
    
    progress_list = []
    
    for ach in ACHIEVEMENTS:
        is_unlocked = ach['id'] in unlocked_ids
        current = 0
        
        if not is_unlocked:
            if ach['type'] == 'food_count':
                c.execute('SELECT COUNT(DISTINCT food_name) FROM food_logs WHERE user_id = ?', (user_id,))
                current = c.fetchone()[0]
            elif ach['type'] == 'activity_count':
                c.execute('SELECT COUNT(*) FROM activity_logs WHERE user_id = ?', (user_id,))
                current = c.fetchone()[0]
            elif ach['type'] == 'calories_burned':
                c.execute('SELECT SUM(calories_burned) FROM activity_logs WHERE user_id = ?', (user_id,))
                current = c.fetchone()[0] or 0
            elif ach['type'] == 'login_streak':
                c.execute('SELECT streak FROM users WHERE id = ?', (user_id,))
                current = c.fetchone()[0] or 0
            elif ach['type'] == 'total_score':
                current = get_user_score(user_id)
        else:
            current = ach['target']
        
        progress_list.append({
            'id': ach['id'],
            'name': ach['name'],
            'desc': ach['desc'],
            'icon': ach['icon'],
            'points': ach['points'],
            'target': ach['target'],
            'current': current,
            'unlocked': is_unlocked,
            'category': ach['category'],
            'progress_percent': min(100, int((current / ach['target']) * 100))
        })
    
    conn.close()
    return progress_list

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            return render_template('login.html', error='Please fill all fields')
        
        conn = sqlite3.connect('database.db', timeout=30.0, isolation_level=None)
        c = conn.cursor()
        c.execute('SELECT id, password, streak, last_login FROM users WHERE username = ?', (username,))
        user = c.fetchone()
        conn.close()
        
        if user and check_password_hash(user[1], password):
            session['user_id'] = user[0]
            session['username'] = username
            
            # Update streak
            today = datetime.now().date()
            last_login = datetime.strptime(user[3], '%Y-%m-%d').date() if user[3] else None
            
            if last_login:
                days_diff = (today - last_login).days
                if days_diff == 1:
                    new_streak = user[2] + 1
                    update_user_score(user[0], 20)  # +20 points for daily streak
                elif days_diff == 0:
                    new_streak = user[2]
                else:
                    new_streak = 1
            else:
                new_streak = 1
            
            conn = sqlite3.connect('database.db', timeout=30.0, isolation_level=None)
            c = conn.cursor()
            c.execute('UPDATE users SET streak = ?, last_login = ? WHERE id = ?', (new_streak, str(today), user[0]))
            conn.commit()
            conn.close()
            
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Invalid username or password')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        email = request.form.get('email', '').strip()
        
        # Optional profile fields
        gender = request.form.get('gender', '')
        age = request.form.get('age', '')
        height = request.form.get('height', '')
        weight = request.form.get('weight', '')
        goal = request.form.get('goal', '')
        diet_type = request.form.get('diet_type', '')
        allergies = request.form.get('allergies', '')
        
        if not username or not password:
            return render_template('signup.html', error='Username and password are required')
        
        hashed_password = generate_password_hash(password)
        
        try:
            conn = sqlite3.connect('database.db', timeout=30.0, isolation_level=None)
            c = conn.cursor()
            c.execute('''INSERT INTO users (username, password, email, gender, age, height, weight, goal, diet_type, allergies) 
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                      (username, hashed_password, email, gender, age or None, height or None, weight or None, goal, diet_type, allergies))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return render_template('signup.html', error='Username already exists')
    
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    today = datetime.now().date()
    
    conn = sqlite3.connect('database.db', timeout=30.0, isolation_level=None)
    c = conn.cursor()
    
    # Get user info
    c.execute('SELECT username, score, streak FROM users WHERE id = ?', (user_id,))
    user = c.fetchone()
    username = user[0]
    score = user[1]
    streak = user[2]
    
    # Today's food logs - FIXED to show grams
    c.execute('''SELECT food_name, grams, calories, protein, carbs, fats, log_time 
                 FROM food_logs WHERE user_id = ? AND log_date = ?
                 ORDER BY log_time DESC''', (user_id, str(today)))
    food_logs = c.fetchall()
    
    # Today's totals
    c.execute('''SELECT SUM(calories), SUM(protein), SUM(carbs), SUM(fats) 
                 FROM food_logs WHERE user_id = ? AND log_date = ?''', (user_id, str(today)))
    totals = c.fetchone()
    total_cals = totals[0] or 0
    total_protein = totals[1] or 0
    total_carbs = totals[2] or 0
    total_fats = totals[3] or 0
    
    # Today's activities
    c.execute('''SELECT activity_name, duration, calories_burned, log_time 
                 FROM activity_logs WHERE user_id = ? AND log_date = ?
                 ORDER BY log_time DESC''', (user_id, str(today)))
    activities = c.fetchall()
    
    # Achievement count
    c.execute('SELECT COUNT(*) FROM user_achievements WHERE user_id = ?', (user_id,))
    achievement_count = c.fetchone()[0]
    
    conn.close()
    
    # Get achievement progress for display
    achievements = get_achievement_progress(user_id)
    
    return render_template('dashboard.html',
                         username=username,
                         score=score,
                         streak=streak,
                         food_logs=food_logs,
                         today_cal=total_cals,
                         today_pro=total_protein,
                         today_carb=total_carbs,
                         today_fat=total_fats,
                         today_fiber=0,
                         today_sugar=0,
                         today_sodium=0,
                         total_cals=total_cals,
                         total_protein=total_protein,
                         total_carbs=total_carbs,
                         total_fats=total_fats,
                         activities=activities,
                         achievement_count=achievement_count,
                         achievements=achievements[:12],
                         food_names=list(FOODS.keys()),
                         act_names=list(ACTIVITIES.keys()))  # Add activity names


@app.route('/log_food', methods=['POST'])
def log_food():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    user_id = session['user_id']
    food_name = request.form.get('food_name', '').strip().lower()
    grams = float(request.form.get('grams', 100))
    
    if food_name not in FOODS:
        return jsonify({'error': 'Food not found'}), 404
    
    food_data = FOODS[food_name]
    multiplier = grams / 100
    
    calories = round(food_data['cal'] * multiplier, 1)
    protein = round(food_data['pro'] * multiplier, 1)
    carbs = round(food_data['carb'] * multiplier, 1)
    fats = round(food_data['fat'] * multiplier, 1)
    
    today = datetime.now().date()
    now = datetime.now().time()
    
    conn = sqlite3.connect('database.db', timeout=30.0, isolation_level=None)
    c = conn.cursor()
    c.execute('''INSERT INTO food_logs (user_id, food_name, calories, protein, carbs, fats, grams, log_date, log_time)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (user_id, food_name, calories, protein, carbs, fats, grams, str(today), str(now)))
    conn.commit()
    conn.close()
    
    # Award points for logging food
    update_user_score(user_id, 5)
    
    # Check for achievement unlocks
    newly_unlocked = check_and_unlock_achievements(user_id)
    
    return jsonify({
        'success': True,
        'food': {
            'name': food_name,
            'grams': grams,
            'calories': calories,
            'protein': protein,
            'carbs': carbs,
            'fats': fats
        },
        'newly_unlocked': [{'name': a['name'], 'icon': a['icon'], 'points': a['points']} for a in newly_unlocked]
    })

@app.route('/log_activity', methods=['POST'])
def log_activity():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    user_id = session['user_id']
    activity_name = request.form.get('activity_name', '').strip().lower()
    duration = int(request.form.get('duration', 0))
    
    if activity_name not in ACTIVITIES:
        return jsonify({'error': 'Activity not found'}), 404
    
    calories_burned = round(ACTIVITIES[activity_name]['cal_per_min'] * duration, 1)
    
    today = datetime.now().date()
    now = datetime.now().time()
    
    conn = sqlite3.connect('database.db', timeout=30.0, isolation_level=None)
    c = conn.cursor()
    c.execute('''INSERT INTO activity_logs (user_id, activity_name, duration, calories_burned, log_date, log_time)
                 VALUES (?, ?, ?, ?, ?, ?)''',
              (user_id, activity_name, duration, calories_burned, str(today), str(now)))
    conn.commit()
    conn.close()
    
    # Award points for logging activity
    update_user_score(user_id, 10)
    
    # Check for achievement unlocks
    newly_unlocked = check_and_unlock_achievements(user_id)
    
    return jsonify({
        'success': True,
        'activity': {
            'name': activity_name,
            'duration': duration,
            'calories_burned': calories_burned
        },
        'newly_unlocked': [{'name': a['name'], 'icon': a['icon'], 'points': a['points']} for a in newly_unlocked]
    })

@app.route('/get_foods')
def get_foods():
    return jsonify({'foods': list(FOODS.keys())})

@app.route('/get_activities')
def get_activities():
    return jsonify({'activities': list(ACTIVITIES.keys())})

@app.route('/analytics')
def analytics():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    period = request.args.get('period', '7')
    
    return render_template('analytics.html', period=period)

@app.route('/get_analytics_data')
def get_analytics_data():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    user_id = session['user_id']
    days = int(request.args.get('days', 7))
    
    start_date = datetime.now().date() - timedelta(days=days-1)
    
    conn = sqlite3.connect('database.db', timeout=30.0, isolation_level=None)
    c = conn.cursor()
    
    # Get daily nutrition data
    c.execute('''SELECT log_date, SUM(calories), SUM(protein), SUM(carbs), SUM(fats)
                 FROM food_logs
                 WHERE user_id = ? AND log_date >= ?
                 GROUP BY log_date
                 ORDER BY log_date''', (user_id, str(start_date)))
    
    nutrition_data = []
    for row in c.fetchall():
        nutrition_data.append({
            'date': row[0],
            'calories': round(row[1], 1) if row[1] else 0,
            'protein': round(row[2], 1) if row[2] else 0,
            'carbs': round(row[3], 1) if row[3] else 0,
            'fats': round(row[4], 1) if row[4] else 0
        })
    
    # Get activity data
    c.execute('''SELECT log_date, SUM(calories_burned)
                 FROM activity_logs
                 WHERE user_id = ? AND log_date >= ?
                 GROUP BY log_date
                 ORDER BY log_date''', (user_id, str(start_date)))
    
    activity_data = []
    for row in c.fetchall():
        activity_data.append({
            'date': row[0],
            'calories_burned': round(row[1], 1) if row[1] else 0
        })
    
    conn.close()
    
    return jsonify({
        'nutrition': nutrition_data,
        'activity': activity_data
    })

@app.route('/get_ai_insights')
def get_ai_insights():
    """Generate personalized AI insights based on user's actual data"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    user_id = session['user_id']
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    
    conn = sqlite3.connect('database.db', timeout=30.0, isolation_level=None)
    c = conn.cursor()
    
    # Get last 7 days data
    c.execute('''SELECT SUM(calories), SUM(protein), SUM(carbs), SUM(fats), COUNT(DISTINCT log_date)
                 FROM food_logs
                 WHERE user_id = ? AND log_date >= ?''', (user_id, str(week_ago)))
    
    week_data = c.fetchone()
    total_cals = week_data[0] or 0
    total_protein = week_data[1] or 0
    total_carbs = week_data[2] or 0
    total_fats = week_data[3] or 0
    days_logged = week_data[4] or 1
    
    # Today's data
    c.execute('''SELECT SUM(calories), SUM(protein), SUM(carbs), SUM(fats)
                 FROM food_logs
                 WHERE user_id = ? AND log_date = ?''', (user_id, str(today)))
    
    today_data = c.fetchone()
    today_cals = today_data[0] or 0
    today_protein = today_data[1] or 0
    today_carbs = today_data[2] or 0
    today_fats = today_data[3] or 0
    
    conn.close()
    
    insights = []
    
    # Check if user has logged ANY food today
    if today_cals == 0:
        insights.append({
            'type': 'warning',
            'icon': '🍽️',
            'title': 'No Food Logged Today',
            'message': 'You haven\'t tracked any meals yet! Start logging to get personalized insights.',
            'action': 'Log your first meal now'
        })
        insights.append({
            'type': 'warning',
            'icon': '⚠️',
            'title': 'Missing Nutrition Data',
            'message': 'Without tracking, we can\'t analyze your protein, calories, or nutrient balance.',
            'action': 'Track at least one meal'
        })
        insights.append({
            'type': 'warning',
            'icon': '📊',
            'title': 'No Progress Tracking',
            'message': 'Regular logging helps identify patterns and reach your fitness goals faster.',
            'action': 'Build a daily logging habit'
        })
        return jsonify({'insights': insights})
    
    # Average daily intake
    avg_cals = total_cals / days_logged
    avg_protein = total_protein / days_logged
    
    # Protein check
    if avg_protein < 50:
        insights.append({
            'type': 'warning',
            'icon': '⚠️',
            'title': 'Low Protein Intake',
            'message': f'Your average protein is {avg_protein:.0f}g/day. Aim for at least 50-60g for better muscle maintenance.',
            'action': 'Add: Eggs, Chicken, Paneer, Dal'
        })
    elif avg_protein < 80:
        insights.append({
            'type': 'info',
            'icon': '💪',
            'title': 'Protein Could Be Higher',
            'message': f'You\'re getting {avg_protein:.0f}g/day. Consider increasing to 80-100g for optimal results.',
            'action': 'Try: Greek yogurt, Tofu, Fish'
        })
    else:
        insights.append({
            'type': 'success',
            'icon': '✅',
            'title': 'Great Protein Intake!',
            'message': f'Excellent! You\'re averaging {avg_protein:.0f}g/day protein.',
            'action': 'Keep it up!'
        })
    
    # Calorie check
    if today_cals > 2500:
        insights.append({
            'type': 'warning',
            'icon': '🔥',
            'title': 'High Calorie Day',
            'message': f'You\'ve consumed {today_cals:.0f} calories today. This is above typical maintenance levels.',
            'action': 'Balance with activity or reduce tomorrow'
        })
    elif today_cals < 1200 and today_cals > 0:
        insights.append({
            'type': 'warning',
            'icon': '⚡',
            'title': 'Low Calorie Intake',
            'message': f'Only {today_cals:.0f} calories today. Make sure you\'re eating enough to fuel your body.',
            'action': 'Add: Healthy snacks, Nuts, Fruits'
        })
    elif today_cals > 0:
        insights.append({
            'type': 'info',
            'icon': '🎯',
            'title': 'Calorie Tracking On Point',
            'message': f'{today_cals:.0f} calories logged today. You\'re being consistent!',
            'action': 'Continue monitoring'
        })
    
    # Carbs/Fats balance
    if today_carbs > 300:
        insights.append({
            'type': 'info',
            'icon': '🍞',
            'title': 'High Carb Day',
            'message': f'{today_carbs:.0f}g carbs today. Balance with protein and healthy fats.',
            'action': 'Try: Adding vegetables, lean protein'
        })
    
    if avg_cals < 1500 and days_logged >= 3:
        insights.append({
            'type': 'warning',
            'icon': '📉',
            'title': 'Consistently Low Calories',
            'message': f'Your 7-day average is {avg_cals:.0f} cal/day. This might be too low for sustained energy.',
            'action': 'Consult a nutritionist if this continues'
        })
    
    # Consistency check
    if days_logged >= 5:
        insights.append({
            'type': 'success',
            'icon': '🔥',
            'title': 'Great Consistency!',
            'message': f'You\'ve logged {days_logged} out of 7 days this week!',
            'action': 'Keep the streak going!'
        })
    elif days_logged <= 2:
        insights.append({
            'type': 'info',
            'icon': '📝',
            'title': 'Log More Regularly',
            'message': f'Only {days_logged} days logged this week. More data = better insights!',
            'action': 'Try logging daily'
        })
    
    return jsonify({'insights': insights})

@app.route('/achievements')
def achievements_page():
    """Separate achievements page with full progress tracking"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    achievements = get_achievement_progress(user_id)
    
    # Group by category
    categories = {}
    for ach in achievements:
        cat = ach['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(ach)
    
    return render_template('achievements.html', categories=categories)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    """Settings page to edit user profile"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    if request.method == 'POST':
        gender = request.form.get('gender', '')
        age = request.form.get('age', '')
        height = request.form.get('height', '')
        weight = request.form.get('weight', '')
        goal = request.form.get('goal', '')
        diet_type = request.form.get('diet_type', '')
        allergies = request.form.get('allergies', '')
        
        conn = sqlite3.connect('database.db', timeout=30.0, isolation_level=None)
        c = conn.cursor()
        c.execute('''UPDATE users SET gender = ?, age = ?, height = ?, weight = ?, 
                     goal = ?, diet_type = ?, allergies = ?
                     WHERE id = ?''',
                  (gender, age or None, height or None, weight or None, goal, diet_type, allergies, user_id))
        conn.commit()
        conn.close()
        
        return redirect(url_for('settings'))
    
    # GET request - load current settings
    conn = sqlite3.connect('database.db', timeout=30.0, isolation_level=None)
    c = conn.cursor()
    c.execute('''SELECT gender, age, height, weight, goal, diet_type, allergies 
                 FROM users WHERE id = ?''', (user_id,))
    user_data = c.fetchone()
    conn.close()
    
    return render_template('settings.html',
                         gender=user_data[0] or '',
                         age=user_data[1] or '',
                         height=user_data[2] or '',
                         weight=user_data[3] or '',
                         goal=user_data[4] or '',
                         diet_type=user_data[5] or '',
                         allergies=user_data[6] or '')

@app.route('/medical')
def medical():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('medical.html')

@app.route('/progress')
def progress():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('progress.html')

@app.route('/meal_plan')
def meal_plan():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('meal_plan_PRO.html')

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
