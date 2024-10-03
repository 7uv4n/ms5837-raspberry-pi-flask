import ms5837
import smbus
import time

# I2C multiplexer address
MUX_ADDR = 0x70                   

# Create I2C bus object
bus = smbus.SMBus(1)

# Function to select multiplexer channel
def select_channel(channel):
    bus.write_byte(MUX_ADDR, 1 << channel)

# Function to read from a single MS5837 sensor
def read_sensor(sensor):
    try:
        if sensor.read():
            pressure = sensor.pressure()
            temperature = sensor.temperature()
            depth = sensor.depth()
            return pressure, temperature, depth
    except:
        pass
    return None

# Initialize sensors
def initialize_and_read_sensors():
    sensors = []
    sensor_data = {}
    for i in range(8):
        select_channel(i)
        try:
            sensor = ms5837.MS5837_30BA()
            if sensor.init():
                sensors.append((i, sensor))
            else:
                print(f"Failed to initialize sensor on channel {i}")
        except:
            print(f"Error initializing sensor on channel {i}")

    # Main loop
    while True:
        for channel, sensor in sensors:
            select_channel(channel)
            result = read_sensor(sensor)
            if result:
                pressure, temperature, depth = result
                print(f"Channel {channel}: P: {pressure:.1f} mbar, T: {temperature:.2f} C, D: {depth:.2f} m")
                sensor_data[f"sensor{channel}"] = {"pressure": pressure, "temperature": temperature}

        print("---")
        time.sleep(1)
