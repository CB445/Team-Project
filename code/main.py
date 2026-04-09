import asyncio
import sqlite3
import os         
import requests   
import math
import winsound  # Task #99: physical speaker alerts
from datetime import datetime
from pathlib import Path
from bleak import BleakScanner

# Path to  database
DB_PATH = Path(__file__).resolve().parent.parent / "db.sqlite3"
# Task #92: Location Detection Logic (RSSI to Meters)
def calculate_meters(rssi):
    if rssi >= 0: return 0.1
    measured_power = -59 
    environmental_factor = 3.0 
    distance = 10**((measured_power - rssi) / (10 * environmental_factor))
    return round(distance, 2)

# Task #99: Speaker Function for Alerts
def trigger_speaker_alert(event_type, distance=0):
    if event_type == "RFID_SUCCESS":
        winsound.Beep(2000, 150) # Short chirp for swipe
    elif event_type == "BLE_WARNING":
        # Task #99: Alert if patient is too far
        for _ in range(3):
            winsound.Beep(1200, 250)
    elif event_type == "UNREGISTERED":
        # Commented out in save_to_database to avoid annoyance
        winsound.Beep(400, 600) 

# Task #85: Log Validation Logic (Updated for Sprint 4)
def save_to_database(identifier, rssi, is_rfid=False):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # SPRINT 4 UPDATE: Calculate distance for EVERY device found
        dist_m = 0.0 if is_rfid else calculate_meters(rssi)
        
        # Task #83: Using the new rfid_uid column for database lookups
        query_col = "bluetooth_mac_address" if not is_rfid else "rfid_uid"
        sensor_type = "RFID" if is_rfid else "BLE"
        
        cursor.execute(f"SELECT device_id, service_user_id FROM tracker_wristbanddevice WHERE {query_col} = ?", (identifier,))
        result = cursor.fetchone()
        
        if result:
            device_id, service_user_id = result
            
            # Task #99: Estimate location based on meters
            location_label = "Scanner 01 (Near)" if dist_m < 4.0 else "Scanner 01 (Away)"
            
            cursor.execute("""
                INSERT INTO tracker_locationlog 
                (detector_location, signal_strength, timestamp, wristband_device_id, service_user_id, movement_detected)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (f"{location_label} - {dist_m}m", rssi, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), device_id, service_user_id, 0))
            conn.commit()
            
            print(f"--- SUCCESS: Resident {service_user_id} Identified | Dist: {dist_m}m | RSSI: {rssi} ---")
            
            # Triggering the new sound features
            if is_rfid:
                trigger_speaker_alert("RFID_SUCCESS")
            elif dist_m > 4.0:
                trigger_speaker_alert("BLE_WARNING", dist_m)
        else:
            # Task #85: Validation alert for unregistered devices
            # UPDATED: Now shows distance even for unknown devices, but sound is disabled
            print(f"--- UNKNOWN {sensor_type} | ID: {identifier} | Dist: {dist_m}m ---")
            
            # trigger_speaker_alert("UNREGISTERED") # Disabled to stop annoying noise
            
        conn.close()
    except Exception as e:
        print(f"--- Database Error: {e} ---")

# Task #82: Create RFID Simulation/Mocking logic
async def simulated_rfid_listener():
    while True:
        await asyncio.sleep(15) 
        print("\n[SIMULATION] Scanning RFID Tag...")
        save_to_database("999888", 100, is_rfid=True)

async def main():
    print("--- Sprint 4: Location Logic + Speaker Alerts ---")
    
    def callback(device, adv_data):
        save_to_database(device.address, adv_data.rssi)

    scanner = BleakScanner(detection_callback=callback)
    
    # Starting BLE but adding a safety check for adapter errors
    try:
        await scanner.start()
        ble_active = True
    except:
        print("--- Hardware Alert: BLE Adapter Not Found (Simulation Only) ---")
        ble_active = False
    
    # Task #84: Integrate simulation into the main scanner loop
    try:
        await asyncio.gather(
            simulated_rfid_listener(),
            asyncio.sleep(3600) 
        )
    except asyncio.CancelledError:
        if ble_active: await scanner.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n--- Scanner Stopped Safely ---")