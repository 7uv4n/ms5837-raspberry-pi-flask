# from flask import Flask, render_template, jsonify, request, send_file
# from flask_socketio import SocketIO
# import sqlite3
# from datetime import datetime
# import csv
# import os

# app = Flask(__name__, static_folder='templates/assets')
# socketio = SocketIO(app, async_mode='eventlet')

# # Initialize the SQLite database
# def init_db():
#     conn = sqlite3.connect('sensor_data.db')
#     cursor = conn.cursor()
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS sensor_data (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             timestamp DATETIME,
#             sensor_id TEXT,
#             temperature REAL,
#             pressure REAL
#         )
#     ''')
#     conn.commit()
#     conn.close()

# # Insert data into the database
# def insert_sensor_data(sensor_id, temperature, pressure):
#     conn = sqlite3.connect('sensor_data.db')
#     cursor = conn.cursor()
#     current_time = datetime.now()
#     cursor.execute('''
#         INSERT INTO sensor_data (timestamp, sensor_id, temperature, pressure)
#         VALUES (?, ?, ?, ?)
#     ''', (current_time, sensor_id, temperature, pressure))
#     conn.commit()
#     conn.close()

# @app.route('/')
# def index():
#     return render_template('index.html')

# @app.route('/download_readings')
# def download_page():
#     return render_template('download_readings.html')

# @app.route('/data', methods=['POST'])
# def receive_data():
#     global sensor_data
#     sensor_data = request.json

#     for key, value in sensor_data.items():
#         insert_sensor_data(key, value.get('temperature'), value.get('pressure'))

#     socketio.emit('update_data', sensor_data)
#     return jsonify({"status": "success", "data": sensor_data})

# @app.route('/download', methods=['POST'])
# def download_data():
#     # Retrieve the 'from' and 'to' date and time from the request
#     from_date = request.form['from_date']  # Format: YYYY-MM-DD
#     from_time = request.form['from_time']  # Format: HH:MM
#     to_date = request.form['to_date']      # Format: YYYY-MM-DD
#     to_time = request.form['to_time']      # Format: HH:MM

#     # Combine date and time to form datetime objects
#     from_datetime = f"{from_date} {from_time}:00"
#     to_datetime = f"{to_date} {to_time}:00"

#     # Query the database for the specified date range
#     conn = sqlite3.connect('sensor_data.db')
#     cursor = conn.cursor()
#     cursor.execute('''
#         SELECT * FROM sensor_data WHERE timestamp BETWEEN ? AND ?
#     ''', (from_datetime, to_datetime))
#     rows = cursor.fetchall()
#     conn.close()

#     # Create a CSV file with the queried data
#     csv_filename = 'sensor_readings.csv'
#     with open(csv_filename, 'w', newline='') as csvfile:
#         csv_writer = csv.writer(csvfile)
#         csv_writer.writerow(['ID', 'Timestamp', 'Sensor ID', 'Temperature', 'Pressure'])
#         csv_writer.writerows(rows)

#     # Send the CSV file as a download
#     return send_file(csv_filename, as_attachment=True)

# @app.route('/display')
# def display_data():
#     conn = sqlite3.connect('sensor_data.db')
#     cursor = conn.cursor()
#     cursor.execute('SELECT * FROM sensor_data')
#     rows = cursor.fetchall()
#     conn.close()

#     sensor_data_list = [
#         {"id": row[0], "timestamp": row[1], "sensor_id": row[2], "temperature": row[3], "pressure": row[4]}
#         for row in rows
#     ]
#     return jsonify(sensor_data_list)

# if __name__ == '__main__':
#     init_db()
#     socketio.run(app, port=5000, debug=True)

from flask import Flask, render_template, jsonify, request, send_file
from flask_socketio import SocketIO
import sqlite3
from datetime import datetime
import csv
import os
import ms5837
import smbus
import time

app = Flask(__name__, static_folder='templates/assets')
socketio = SocketIO(app, async_mode='eventlet')

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
            pressure REAL,
            depth REAL
        )
    ''')
    conn.commit()
    conn.close()

# Insert data into the database
def insert_sensor_data(sensor_id, temperature, pressure, depth):
    conn = sqlite3.connect('sensor_data.db')
    cursor = conn.cursor()
    current_time = datetime.now()
    cursor.execute('''
        INSERT INTO sensor_data (timestamp, sensor_id, temperature, pressure, depth)
        VALUES (?, ?, ?, ?, ?)
    ''', (current_time, sensor_id, temperature, pressure, depth))
    conn.commit()
    conn.close()

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
def initialize_sensors():
    sensors = []
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
    return sensors

# Function to gather sensor data and store in the database
def gather_and_store_sensor_data():
    sensors = initialize_sensors()
    while True:
        for channel, sensor in sensors:
            select_channel(channel)
            result = read_sensor(sensor)
            if result:
                pressure, temperature, depth = result
                # Store the sensor data in the database
                insert_sensor_data(f"Channel_{channel}", temperature, pressure, depth)
                # Emit data through socket for real-time updates
                socketio.emit('update_data', {'sensor_id': f"Channel_{channel}", 'temperature': temperature, 'pressure': pressure, 'depth': depth})
        time.sleep(1)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download_readings')
def download_page():
    return render_template('download_readings.html')

@app.route('/download', methods=['POST'])
def download_data():
    # Retrieve the 'from' and 'to' date and time from the request
    from_date = request.form['from_date']  # Format: YYYY-MM-DD
    from_time = request.form['from_time']  # Format: HH:MM
    to_date = request.form['to_date']      # Format: YYYY-MM-DD
    to_time = request.form['to_time']      # Format: HH:MM

    # Combine date and time to form datetime objects
    from_datetime = f"{from_date} {from_time}:00"
    to_datetime = f"{to_date} {to_time}:00"

    # Query the database for the specified date range
    conn = sqlite3.connect('sensor_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM sensor_data WHERE timestamp BETWEEN ? AND ?
    ''', (from_datetime, to_datetime))
    rows = cursor.fetchall()
    conn.close()

    # Create a CSV file with the queried data
    csv_filename = 'sensor_readings.csv'
    with open(csv_filename, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(['ID', 'Timestamp', 'Sensor ID', 'Temperature', 'Pressure', 'Depth'])
        csv_writer.writerows(rows)

    # Send the CSV file as a download
    return send_file(csv_filename, as_attachment=True)

@app.route('/display')
def display_data():
    conn = sqlite3.connect('sensor_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM sensor_data')
    rows = cursor.fetchall()
    conn.close()

    sensor_data_list = [
        {"id": row[0], "timestamp": row[1], "sensor_id": row[2], "temperature": row[3], "pressure": row[4], "depth": row[5]}
        for row in rows
    ]
    return jsonify(sensor_data_list)

if __name__ == '__main__':
    init_db()
    socketio.start_background_task(gather_and_store_sensor_data)
    socketio.run(app, port=5000, debug=True)
