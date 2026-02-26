import random
import time
def get_simulated_ble_data():
    # TASK #19
    # #defined the MAC(ID) and RSSI(DISTANCE) to be pulled from scan.
    # when we have the rasbery pi we need to change 'mac_addr' to be 'device.rssi' 
    mac_addr = "AA:BB:CC:DD:EE:FF"

    # when we have the rasbery pi we need to change 'signal_strength' to be 'device.rssi' 
    signal_strength = random.randint(-80, -40)

    # #Task #29
    raw_name = random.choice(["Resident_Wristband_01", None])
    # #Safety Guard: If hardware finds no nmae, use "Unknown Resident"
    if raw_name is None:
        clean_name = "Unknown Resident"
    else:
        clean_name = raw_name

    return {"mac": mac_addr, "rssi": signal_strength, "name": clean_name}

if __name__ == "__main__":
    print("--- Care Home BLE Monitoring System: ACTIVE ---")
    try:
        while True:
            data = get_simulated_ble_data()
            #Task #21: Outputing
            print(f"Tracking: {data['name']} | Signal: {data['rssi']}dBm | ID: {data['mac']}")
            # Task #22: Continuous Loop (2s delay)
            time.sleep(2)
    except KeyboardInterrupt:
        print("\nMonitoring System Stopped Safely.")