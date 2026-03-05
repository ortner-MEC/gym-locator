import os
os.environ['GOOGLE_PLACES_API_KEY'] = 'AIzaSyCT278VniUSxVwE9beIkXo6d3lrxNlA4r0'
import sys
sys.path.insert(0, '/Users/karl/workspace/gym-locator')
from modules.places_api import PlacesAPI
p = PlacesAPI(api_key='AIzaSyCT278VniUSxVwE9beIkXo6d3lrxNlA4r0')
print(p.search_nearby(38.0558, -0.7107, 2000, ['gym']))
