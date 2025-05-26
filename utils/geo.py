# utils/geo.py
from geopy.distance import geodesic

def find_nearest_office(user_lat, user_lon, offices, radius_meters=100):
    for office in offices:
        office_lat = office['lat']
        office_lon = office['lon']
        dist = geodesic((user_lat, user_lon), (office_lat, office_lon)).meters
        if dist <= radius_meters:
            return True, office['name'], dist
    return False, None, None
