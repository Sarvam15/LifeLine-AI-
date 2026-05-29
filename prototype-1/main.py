import time
import math
import random

# 1. HAVERSINE FORMULA: Calculates distance between two GPS coordinates
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * \
        math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# 2. MOCK DATA: Nearby Ambulances (Private & Public)
ambulances = [
    {"id": "AMB-01", "name": "City Private Med", "lat": 19.2850, "lon": 72.8750, "status": "Available"},
    {"id": "AMB-02", "name": "LifeCare Pvt", "lat": 19.2910, "lon": 72.8620, "status": "Available"},
    {"id": "GOVT-HUB", "name": "Mira Road Govt Hospital Hub", "lat": 19.2810, "lon": 72.8550, "status": "Available"}
]

def trigger_emergency(patient_lat, patient_lon, symptoms):
    print(f"\n[SYSTEM] EMERGENCY TRIGGERED: {symptoms}")
    print(f"[SYSTEM] Locating ambulances near ({patient_lat}, {patient_lon})...")
    
    # 3. BROADCAST PHASE
    nearby = [a for a in ambulances if calculate_distance(patient_lat, patient_lon, a['lat'], a['lon']) < 5]
    print(f"[BROADCAST] Loud Ping sent to {len(nearby)} units in 5km radius.")
    
    # 4. THE 30-SECOND FAIL-SAFE TIMER
    start_time = time.time()
    accepted = False
    
    print("[TIMER] 30s Claim Window Started...")
    
    # Simulating a "claim" (In reality, this would be a button press from the driver app)
    while time.time() - start_time < 30:
        elapsed = int(time.time() - start_time)
        # For simulation, let's say there's a 10% chance a driver accepts every second
        if random.random() < 0.05: 
            accepted = True
            winner = random.choice(nearby)
            print(f"\n[SUCCESS] {winner['name']} ({winner['id']}) has ACCEPTED the trip at {elapsed}s!")
            break
        
        if elapsed % 5 == 0:
            print(f"Time remaining: {30 - elapsed}s...")
        time.sleep(1)

    # 5. ESCALATION PHASE
    if not accepted:
        print("\n[ALERT] NO CLAIM WITHIN 30 SECONDS.")
        print(f"[ESCALATION] Force Dispatching: {ambulances[2]['name']} (Primary Govt Hub)")
        print("[API] Preparing ER Unit for symptoms: " + symptoms)
    
    print("[FINISH] Hospital API Handshake Complete. Route Cleared.")

# RUN SIMULATION
if __name__ == "__main__":
    # Example: SOS from a user in Mira Road
    trigger_emergency(19.2833, 72.8711, "Patient reporting severe chest pain and breathlessness.")
