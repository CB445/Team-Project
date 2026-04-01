import asyncio
import sqlite3
import os         
import requests   
from datetime import datetime
from pathlib import Path
from bleak import BleakScanner

# Path to your database
DB_PATH = Path(__file__).resolve().parent.parent / "backend" / "db.sqlite3"

# Task #85: Log Validation Logic
def save_to_database(identifier, rssi, is_rfid=False):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Task #83: Using the new rfid_uid column for database lookups
        query_col = "bluetooth_mac_address" if not is_rfid else "rfid_uid"
        sensor_type = "RFID" if is_rfid else "BLE"
        
        cursor.execute(f"SELECT device_id, service_user_id FROM tracker_wristbanddevice WHERE {query_col} = ?", (identifier,))
        result = cursor.fetchone()
        
        if result:
            device_id, service_user_id = result
            cursor.execute("""
                INSERT INTO tracker_locationlog 
                (detector_location, signal_strength, timestamp, wristband_device_id, service_user_id, movement_detected)
                VALUES (?, ?, ?, ?, ?, ?)
            """, ("Scanner 01", rssi, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), device_id, service_user_id, 0))
            conn.commit()
            print(f"--- SUCCESS: Resident {service_user_id} Identified | Type: {sensor_type} | ID: {identifier} | RSSI: {rssi} ---")
        else:
            # Task #85: Validation alert for unregistered devices
            print(f"--- DATABASE ALERT: Unregistered Device Detected | Type: {sensor_type} | MAC/UID: {identifier} | RSSI: {rssi} ---")
            
        conn.close()
    except Exception as e:
        print(f"--- Database Error: {e} ---")

# Task #82: Create RFID Simulation/Mocking logic
async def simulated_rfid_listener():
    while True:
        await asyncio.sleep(10) 
        print("\n[SIMULATION] Scanning RFID Tag...")
        save_to_database("999888", 100, is_rfid=True)

async def main():
    print("--- BLE + RFID Simulation ---")
    
    def callback(device, adv_data):
        save_to_database(device.address, adv_data.rssi)

    scanner = BleakScanner(detection_callback=callback)
    await scanner.start()
    
    # Task #84: Integrate RFID simulation into the main BLE scanner loop using asyncio.gather
    try:
        await asyncio.gather(
            simulated_rfid_listener(),
            asyncio.sleep(3600) 
        )
    except asyncio.CancelledError:
        await scanner.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n--- Scanner Stopped Safely ---")