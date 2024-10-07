from flask import Flask, render_template, jsonify, request, send_file
from flask_socketio import SocketIO
import sqlite3
from datetime import datetime
import csv
import os
import subprocess
import threading
import ms5837
import smbus
import time
import requests
import json

app = Flask(__name__, static_folder='templates/assets')
socketio = SocketIO(app, async_mode='eventlet')

# I2C multiplexer address
MUX_ADDR = 0x70
# Create I2C bus object
bus = smbus.SMBus(1)
# Server URL for data sending
server_url = "http://127.0.0.1:5000/data"

# Initialize the SQLite database
def init_db():
    conn = sqlite3.connect('sensor_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sensor_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME,
            sensor_id TEXT,
            temperature REAL,
            pressure REAL
        )
    ''')
    conn.commit()
    conn.close()
    
    
# Insert data into the database
def insert_sensor_data(sensor_id, temperature, pressure):
    conn = sqlite3.connect('sensor_data.db')
    cursor = conn.cursor()
    current_time = datetime.now()
    cursor.execute('''
        INSERT INTO sensor_data (timestamp, sensor_id, temperature, pressure)
        VALUES (?, ?, ?, ?)
    ''', (current_time, sensor_id, temperature, pressure))
    conn.commit()
    conn.close()

# Function to select multiplexer channel
def select_channel(channel):
    bus.write_byte(MUX_ADDR, 1 << channel)

# Function to read from a single MS5837 sensor
def read_sensor(sensor):
    try:
        if sensor.read():
            pressure = sensor.pressure()
            temperature = sensor.temperature()
            return pressure, temperature
    except Exception as e:
        print(f"Error reading sensor: {e}")
    return None

# Function to send data to the server
def send_data_to_server(data):
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.post(server_url, headers=headers, data=json.dumps(data))
        return response
    except requests.exceptions.RequestException as e:
        print(f"Error sending data to server: {e}")
        return None


# Initialize sensors
sensors = []
for i in range(8):
    select_channel(i)
    try:
        sensor = ms5837.MS5837_30BA()
        if sensor.init():
            sensors.append((i, sensor))
    except Exception as e:
        print(f"Error initializing sensor on channel {i}: {e}")

# Function to get data from the ESP32 (modify the URL according to your ESP32 endpoint)
def get_data_from_esp32():
    esp32_url = "http://192.168.178.31:5000/get_sensor_data"  # ESP32 URL for GET request
    try:
        response = requests.get(esp32_url)
        if response.status_code == 200:
            esp32_data = response.json()
            return esp32_data  # Return the JSON response from ESP32
        else:
            print(f"Error: Received {response.status_code} from ESP32")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to ESP32: {e}")
        return None

# need to modify the main4.py especially this function. so far it is working to get the values from esp32, but  not far till to read the values and display the stuffs

# Function to run the sensor reading loop
def run_sensor_reading():
    while True:
        sensor_data = {}

        # Read from local sensors connected via the multiplexer
        for channel, sensor in sensors:
            select_channel(channel)
            result = read_sensor(sensor)
            if result:
                pressure, temperature = result
                sensor_data[f"sensor{channel+1}"] = {
                    "pressure": round(pressure, 2),
                    "temperature": round(temperature, 2)
                }

                # Insert data into the database
                insert_sensor_data(f"sensor{channel+1}", temperature, pressure)

        # Fetch data from ESP32
        esp32_data = get_data_from_esp32()
        print(esp32_data)
        
        sensor_data['sensor0'] = esp32_data
        # if esp32_data:
        #     for sensor_id, values in esp32_data.items():
        #         print(esp32_data.items())
        #         sensor_data[sensor_id] = {
        #             "temperature": values['temperature'],
        #             "pressure": values['pressure']
        #         }
        #         # Insert ESP32 data into the database
        #         insert_sensor_data(sensor_id, values['temperature'], values['pressure'])

        # Send collected data to the server (if there is any data)
        if sensor_data:
            print(sensor_data)
            send_data_to_server(sensor_data)

        time.sleep(1)  # Adjust delay if necessary


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download_readings')
def download_page():
    return render_template('download_readings.html')

@app.route('/data', methods=['POST'])
def receive_data():
    global sensor_data
    sensor_data = request.json

    for key, value in sensor_data.items():
        insert_sensor_data(key, value.get('temperature'), value.get('pressure'))
    socketio.emit('update_data', sensor_data)
    return jsonify({"status": "success", "data": sensor_data})

@app.route('/download', methods=['POST'])
def download_data():
    from_date = request.form['from_date']
    from_time = request.form['from_time']
    to_date = request.form['to_date']
    to_time = request.form['to_time']

    from_datetime = f"{from_date} {from_time}:00"
    to_datetime = f"{to_date} {to_time}:00"

    conn = sqlite3.connect('sensor_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM sensor_data WHERE timestamp BETWEEN ? AND ?
    ''', (from_datetime, to_datetime))
    rows = cursor.fetchall()
    conn.close()

    csv_filename = 'sensor_readings.csv'
    with open(csv_filename, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(['ID', 'Timestamp', 'Sensor ID', 'Temperature', 'Pressure'])
        csv_writer.writerows(rows)

    return send_file(csv_filename, as_attachment=True)

@app.route('/display')
def display_data():
    if 'sensor_data' not in globals():
        return jsonify({"error": "No sensor data available"}), 404

    sensor_data_list = [
        {"sensor_id": sensor_id, "temperature": data.get('temperature'), "pressure": data.get('pressure')}
        for sensor_id, data in sensor_data.items()
    ]
    print(sensor_data_list)
    return jsonify(sensor_data_list)

if __name__ == '__main__':
    init_db()
    threading.Thread(target=run_sensor_reading).start()
    socketio.run(app, port=5000, debug=True)
        
