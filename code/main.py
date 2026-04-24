import asyncio
import sqlite3
import os         
import requests   
import math
import winsound  
import socket  
from datetime import datetime
from pathlib import Path
from bleak import BleakScanner

# Path to database
DB_PATH = Path(__file__).resolve().parent.parent / "db.sqlite3"

# Automatically detect which Pi/Computer this is
NODE_NAME = socket.gethostname()

# Memory for the script
STABLE_DETECTIONS = {}
ALREADY_BEEPED = set() # Remembers who we've already chirped for

# Location Detection Logic (RSSI to Meters)
def calculate_meters(rssi):
    if rssi >= 0: return 0.1
    measured_power = -59 
    environmental_factor = 3.0 
    distance = 10**((measured_power - rssi) / (10 * environmental_factor))
    return round(distance, 2)

# Speaker Function for Alerts
def trigger_speaker_alert(event_type, distance=0):
    if event_type == "RFID_SUCCESS":
        winsound.Beep(2000, 150) # Short chirp
    elif event_type == "BLE_WARNING":
        for _ in range(3):
            winsound.Beep(1200, 250) # Warning beeps
    elif event_type == "UNREGISTERED":
        winsound.Beep(400, 600) 

# Log Validation Logic 
def save_to_database(identifier, rssi, is_rfid=False):
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10) 
        cursor = conn.cursor()
        
        dist_m = 0.0 if is_rfid else calculate_meters(rssi)

        # Extreme Distance Glitch Filter
        if not is_rfid:
            STABLE_DETECTIONS[identifier] = STABLE_DETECTIONS.get(identifier, 0) + 1
            if dist_m > 30.0 and STABLE_DETECTIONS[identifier] < 2:
                print(f"--- IGNORED: Weak single-ping at {dist_m}m ---")
                return

        query_col = "bluetooth_mac_address" if not is_rfid else "rfid_uid"
        sensor_type = "RFID" if is_rfid else "BLE"
        
        cursor.execute(f"SELECT device_id, service_user_id FROM tracker_wristbanddevice WHERE {query_col} = ?", (identifier,))
        result = cursor.fetchone()
        
        if result:
            device_id, service_user_id = result
            location_label = f"Node: {NODE_NAME} (Near)" if dist_m < 4.0 else f"Node: {NODE_NAME} (Away)"
            
            cursor.execute("""
                INSERT INTO tracker_locationlog 
                (detector_location, signal_strength, timestamp, wristband_device_id, service_user_id, movement_detected)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (f"{location_label} - {dist_m}m", rssi, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), device_id, service_user_id, 0))
            conn.commit()
            
            print(f"--- SUCCESS: Resident {service_user_id} Identified | Dist: {dist_m}m | RSSI: {rssi} ---")
            
            # --- PROFESSIONAL AUDIO LOGIC ---
            if is_rfid:
                trigger_speaker_alert("RFID_SUCCESS")
            
            # FIRST CONTACT BEEP: Chirp once when first discovered
            elif identifier not in ALREADY_BEEPED:
                trigger_speaker_alert("RFID_SUCCESS") 
                ALREADY_BEEPED.add(identifier)
                print(f"--- ALERT: First contact with Resident {service_user_id} ---")
            
            # DANGER ZONE BEEP: Warning if very close
            elif dist_m < 1.5:
                trigger_speaker_alert("BLE_WARNING")
            
        else:
            print(f"--- UNKNOWN {sensor_type} | ID: {identifier} | Dist: {dist_m}m ---")
            
        conn.close()
    except Exception as e:
        print(f"--- Database Error: {e} ---")

# RFID Simulation/Mocking logic
async def simulated_rfid_listener():
    try:
        while True:
            await asyncio.sleep(15) 
            print("\n[SIMULATION] Scanning RFID Tag...")
            save_to_database("999888", 100, is_rfid=True)
    except asyncio.CancelledError:
        return

async def main():
    print("--- Smart Wristband Monitoring System: Gateway Node Active ---")
    
    async def hardware_heartbeat():
        try:
            while True:
                await asyncio.sleep(60)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Scanner Status: ONLINE")
        except asyncio.CancelledError:
            return

    def callback(device, adv_data):
        save_to_database(device.address, adv_data.rssi)

    scanner = BleakScanner(detection_callback=callback)
    
    try:
        await scanner.start()
        print("--- BLE Scanner Started (Press CTRL+C once to stop) ---")
        
        await asyncio.gather(
            simulated_rfid_listener(),
            hardware_heartbeat(),
            asyncio.sleep(36000) 
        )
    except (asyncio.CancelledError, KeyboardInterrupt):
        print("\n--- Stopping Scanner... ---")
    finally:
        await scanner.stop()
        print("--- Scanner Stopped Safely ---")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass