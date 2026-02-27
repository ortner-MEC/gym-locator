"""Configuration for Gym Location Analyzer."""
import os

# Google APIs Configuration
GOOGLE_PLACES_API_KEY = os.getenv('GOOGLE_PLACES_API_KEY')
GOOGLE_DISTANCE_API_KEY = os.getenv('GOOGLE_PLACES_API_KEY')  # Same key works for both

# Default Search Parameters
DEFAULT_RADIUS_METERS = 2000  # 2km search radius
MAX_COMPETITORS = 10  # Number of competing gyms to analyze

# Scoring Weights (must sum to 1.0)
WEIGHTS = {
    'competition_density': 0.30,    # Less competition = better
    'target_demographics': 0.25,    # Offices, residences nearby
    'accessibility': 0.25,          # Public transport, parking
    'market_saturation': 0.20,      # Gyms per capita in area
}

# Place Types for Analysis
PLACE_TYPES = {
    'competitors': ['gym', 'fitness_center', 'sports_complex'],
    'target_residential': ['apartment_building', 'residential', 'lodging'],
    'target_office': ['office', 'coworking_space', 'business_center'],
    'target_young': ['university', 'college', 'student_housing'],
    'synergies': ['health_food_store', 'sports_goods_store', 'physiotherapist', 'spa'],
    'accessibility': ['parking', 'subway_station', 'bus_station', 'train_station'],
}

# Output Settings
OUTPUT_DIR = 'reports'
CACHE_ENABLED = True
CACHE_DIR = '.cache'