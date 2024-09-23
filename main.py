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
