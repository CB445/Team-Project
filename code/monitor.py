import random

def get_simulated_ble_data():
    # TASK #19
    # #defined the MAC(ID) and RSSI(DISTANCE) to be pulled from scan.
    # #LATER: 'mac_addr' will be 'device.rssi' when I get the rasbery pi
    mac_addr = "AA:BB:CC:DD:EE:FF"

    # #LATER: 'signal_strength' will be 'device.rssi' when I get the rasbery pi.
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
    # Test
    print("Tuesday Testing Output:", get_simulated_ble_data())