import asyncio
import sqlite3
import os
import requests  # TASK #67: sending POST requests
from datetime import datetime
from pathlib import Path
from bleak import BleakScanner

# TASK #78: Path updated to reach the backend folder correctly
DB_PATH = Path(__file__).resolve().parent.parent / "backend" / "db.sqlite3"

# TASK #70: API Endpoint for Sprint 2
API_URL = "http://127.0.0.1:8000/api/detections/" 

def send_detection_via_post(mac, rssi, name):
    payload = {
        "location": "Raspberry Pi 01",
        "rssi": rssi,
        "mac_address": mac,
        "resident_name": name,
        "timestamp": datetime.now().isoformat()
    }
    try:
        print(f"--- API: Payload prepared for {mac} ---")
        # response = requests.post(API_URL, json=payload) 
    except Exception as e:
        print(f"--- API Error: {e} ---")

def save_to_database(mac, rssi):
    """Saves scan data using the new Sprint 2 Model names (TASK #78)"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # TASK #78: Queries the new table and column names
        cursor.execute("""
            SELECT device_id, service_user_id 
            FROM tracker_wristbanddevice 
            WHERE bluetooth_mac_address = ?
        """, (mac,))
        result = cursor.fetchone()
        
        if result:
            device_id, service_user_id = result
            # TASK #78: Inserts into the correct new LocationLog table
            cursor.execute("""
                INSERT INTO tracker_locationlog 
                (detector_location, signal_strength, timestamp, wristband_device_id, service_user_id, movement_detected)
                VALUES (?, ?, ?, ?, ?, ?)
            """, ("Raspberry Pi 01", rssi, datetime.now(), device_id, service_user_id, False))
            conn.commit()
            print(f"--- Database: Event logged for {mac} ---")
        else:
            print(f"--- Database Alert: MAC {mac} not found in backend records ---")
            
        conn.close()
    except Exception as e:
        print(f"--- Database Error: {e} ---")

async def main():
    print("--- Care Home BLE Monitoring System: ACTIVE ---")
    db_available = DB_PATH.exists()

    def callback(device, adv_data):
        mac = device.address  
        rssi = adv_data.rssi  
        name = adv_data.local_name or device.name

        # Matcher logic removed to stop the 'ModuleNotFoundError'
        print(f"Tracking: {name or 'Unknown Device'} | Signal: {rssi}dBm | ID: {mac}")

        if db_available:
            save_to_database(mac, rssi)
        
        send_detection_via_post(mac, rssi, name or "Unknown")

    scanner = BleakScanner(detection_callback=callback)
    await scanner.start()
    try:
        while True:
            await asyncio.sleep(2) 
    except KeyboardInterrupt:
        print("\nMonitoring System Stopped Safely.")
    finally:
        await scanner.stop()

if __name__ == "__main__":
    asyncio.run(main())