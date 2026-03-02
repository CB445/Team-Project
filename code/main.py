import random
import time
import sqlite3
import os
from datetime import datetime

# Path to the database file
DB_PATH = './backend/db.sqlite3'
def get_simulated_ble_data():
    # TASK #19: Simulation of hardware data
    # when we have the rasbery pi we need to change 'mac_addr' to be 'device.rssi' 
    mac_addr = "AA:BB:CC:DD:EE:FF" 
    signal_strength = random.randint(-80, -40)

    # Task #29: Safety Guard for names
    raw_name = random.choice(["Resident_Wristband_01", None])
    clean_name = "Unknown Resident" if raw_name is None else raw_name

    return {"mac": mac_addr, "rssi": signal_strength, "name": clean_name}

def save_to_database(mac, rssi):
    """Saves scan data to the DetectionEvent table"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 1. Find the wristband ID that matches the MAC address
        cursor.execute("SELECT id FROM tracker_wristband WHERE mac_address = ?", (mac,))
        result = cursor.fetchone()
        
        if result:
            wristband_id = result[0]
            # 2. Insert into the DetectionEvent table
            cursor.execute("""
                INSERT INTO tracker_detectionevent (location, rssi, timestamp, wristband_id)
                VALUES (?, ?, ?, ?)
            """, ("Raspberry Pi 01", rssi, datetime.now(), wristband_id))
            conn.commit()
            print(f"--- Database: Event logged for {mac} ---")
        else:
            # Alert for when the Hardware team hasn't registered a wristband yet
            print(f"--- Database Alert: MAC {mac} not found in 'Wristband' table ---")
            
        conn.close()
    except Exception as e:
        print(f"--- Database Error: {e} ---")

if __name__ == "__main__":
    print("--- Care Home BLE Monitoring System: ACTIVE ---")
    
    # Check if the merged database is reachable
    if os.path.exists(DB_PATH):
        try:
            while True:
                data = get_simulated_ble_data()
                
                # Task #21: Print for terminal tracking
                print(f"Tracking: {data['name']} | Signal: {data['rssi']}dBm | ID: {data['mac']}")
                
                # Save to the shared team database
                save_to_database(data['mac'], data['rssi'])
                
                # Task #22: Continuous Loop (2s delay)
                time.sleep(2)
        except KeyboardInterrupt:
            print("\nMonitoring System Stopped Safely.")
    else:
        print(f"ERROR: Database not found at {DB_PATH}. Check your 'backend' folder.")