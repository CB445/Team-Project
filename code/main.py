import asyncio
import sqlite3
import os
from datetime import datetime
from pathlib import Path

from bleak import BleakScanner
from matcher import match_device   # or: from .matcher import match_device (see note below)

# Path to the database file
DB_PATH = Path(__file__).resolve().parent.parent / "backend" / "db.sqlite3"



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


async def main():
    print("--- Care Home BLE Monitoring System: ACTIVE ---")

    db_available = DB_PATH.exists()
    if not db_available:
        print(f"NOTE: Database not found at {DB_PATH}. Running without DB logging for now.")

    def callback(device, adv_data):                          #def callback(device, adv_data):
        mac = device.address                                 #print(f"Seen device: {device.address} | {adv_data.rssi} dBm")
        rssi = adv_data.rssi                                    #run this to test call back for all bluetooth devices not jsut ones found in whitelist
        name = adv_data.local_name or device.name

        match = match_device(mac, name)
        if not match:
            return

        resident_id = match.get("id", name or "Unknown Resident")
        print(f"Tracking: {resident_id} | Signal: {rssi}dBm | ID: {mac}")

        if db_available:
            save_to_database(mac, rssi)

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