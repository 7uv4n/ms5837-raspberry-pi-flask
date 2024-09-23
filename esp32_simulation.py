import requests
import json
import random
import time

# Server URL
server_url = "http://127.0.0.1:5000/data"

def generate_sensor_data():
    data = {}
    for i in range(5):  # Simulate 5 sensors
        data[f"sensor{i}"] = {
            "pressure": round(random.uniform(950, 1050), 2),  # Simulated pressure in mbar
            "temperature": round(random.uniform(15, 25), 2)  # Simulated temperature in Celsius
        }
    return data

def send_data_to_server(data):
    headers = {'Content-Type': 'application/json'}
    response = requests.post(server_url, headers=headers, data=json.dumps(data))
    return response

def main():
    while True:
        sensor_data = generate_sensor_data()
        print("Sending data:", sensor_data)
        response = send_data_to_server(sensor_data)
        print("Server response:", response.status_code, response.text)
        time.sleep(1)  # Send data every 3 seconds

if __name__ == "__main__":
    main()
