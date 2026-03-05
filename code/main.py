import asyncio
import sqlite3
import os
import requests  # Task #67: For sending POST requests
from datetime import datetime
from pathlib import Path

# TASK #19: Real Hardware Extraction
from bleak import BleakScanner
# Import the matcher tool (Task #30 is a teammate's task)
from matcher import match_device   

# Path to the database file - Professional Path (Task #78)
DB_PATH = Path(__file__).resolve().parent.parent / "backend" / "db.sqlite3"

# TASK #70: API Endpoint for Sprint 2
API_URL = "http://127.0.0.1:8000/api/detections/" 

# TASK #67: Create send_detection() Function
def send_detection_via_post(mac, rssi, name):
    """
    TASK #66: Build detection payload 
    Packages data into the JSON format required by the backend.
    """
    payload = {
        "location": "Raspberry Pi 01",
        "rssi": rssi,
        "mac_address": mac,
        "resident_name": name,
        "timestamp": datetime.now().isoformat()
    }
    
    # TASK #71: Framework for Manual API Call
    try:
        # This will be uncommented once the backend API is live
        print(f"--- API: Payload prepared for {mac} ---")
        # response = requests.post(API_URL, json=payload) 
    except Exception as e:
        print(f"--- API Error: {e} ---")

def save_to_database(mac, rssi):
    """Saves scan data to the DetectionEvent table (Sprint 1)"""
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
            
            # TASK #21: Fixed 'prinl' typo to 'print'
            print(f"--- Database: Event logged for {mac} ---")
        else:
            # TASK #21: Print status to console (Unknown Case)
            print(f"--- Database Alert: MAC {mac} not found ---")
            
        conn.close()
    except Exception as e:
        print(f"--- Database Error: {e} ---")

async def main():
    # TASK #78: Review/Change tasks (Logging system startup)
    print("--- Care Home BLE Monitoring System: Sprint 1 & 2 ACTIVE ---")

    db_available = DB_PATH.exists()

    def callback(device, adv_data):
        # TASK #19: Extract MAC + RSSI from scan results (Real Hardware)
        mac = device.address  
        rssi = adv_data.rssi  
        name = adv_data.local_name or device.name

        # Filtering logic
        match = match_device(mac, name)
        if not match:
            return

        # TASK #29: Handle missing device names (Safety Guard)
        resident_id = match.get("id", name or "Unknown Resident")
        print(f"Tracking: {resident_id} | Signal: {rssi}dBm | ID: {mac}")

        if db_available:
            save_to_database(mac, rssi)
        
        # TASK #69: Integrate POST into Scan Loop
        send_detection_via_post(mac, rssi, resident_id)

    scanner = BleakScanner(detection_callback=callback)

    await scanner.start()
    try:
        # TASK #22: Continuous scan loop (2s delay)
        while True:
            await asyncio.sleep(2) 
    except KeyboardInterrupt:
        print("\nMonitoring System Stopped Safely.")
    finally:
        await scanner.stop()

if __name__ == "__main__":
    asyncio.run(main())