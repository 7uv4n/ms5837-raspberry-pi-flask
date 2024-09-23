const socket = io();
const chartTableBody = document.getElementById('chart-table-body');
const sensorCharts = {};

const createChart = (ctx, label, type) => {
    const placeholderData = new Array(10).fill(null);
    const placeholderLabels = new Array(10).fill('');

    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: placeholderLabels,
            datasets: [{
                label: `${label} ${type}`,
                borderColor: type === 'Temperature (°C)' ? 'rgb(255, 99, 132)' : 'rgb(54, 162, 235)',
                data: placeholderData.slice(), // Copy of placeholder data
            }]
        },
        options: {
            scales: {
                y: {
                    type: 'linear',
                    position: 'left',
                }
            }
        }
    });
};

socket.on('update_data', (data) => {
    const currentTime = new Date().toLocaleTimeString();

    Object.keys(data).forEach((sensor) => {
        if (!sensorCharts[sensor]) {
            // Create a new row for this sensor
            const row = document.createElement('tr');

            // Sensor name cell
            const sensorCell = document.createElement('td');
            sensorCell.textContent = sensor;
            row.appendChild(sensorCell);

            // Latest temperature cell
            const latestTempCell = document.createElement('td');
            latestTempCell.id = `${sensor}_latest_temperature`;
            row.appendChild(latestTempCell);

            // Temperature chart cell
            const tempCell = document.createElement('td');
            const tempCanvas = document.createElement('canvas');
            tempCanvas.id = `${sensor}_temperature_chart`;
            tempCell.appendChild(tempCanvas);
            row.appendChild(tempCell);

            // Latest pressure cell
            const latestPressureCell = document.createElement('td');
            latestPressureCell.id = `${sensor}_latest_pressure`;
            row.appendChild(latestPressureCell);

            // Pressure chart cell
            const pressureCell = document.createElement('td');
            const pressureCanvas = document.createElement('canvas');
            pressureCanvas.id = `${sensor}_pressure_chart`;
            pressureCell.appendChild(pressureCanvas);
            row.appendChild(pressureCell);

            chartTableBody.appendChild(row);

            sensorCharts[sensor] = {
                temperature: createChart(tempCanvas.getContext('2d'), sensor, 'Temperature (°C)'),
                pressure: createChart(pressureCanvas.getContext('2d'), sensor, 'Pressure (mbar)')
            };
        }

        const tempChart = sensorCharts[sensor].temperature;
        const pressureChart = sensorCharts[sensor].pressure;

        tempChart.data.labels.push(currentTime);
        pressureChart.data.labels.push(currentTime);

        if (tempChart.data.labels.length > 10) {
            tempChart.data.labels.shift();
            pressureChart.data.labels.shift();
        }

        tempChart.data.datasets[0].data.push(data[sensor].temperature);
        pressureChart.data.datasets[0].data.push(data[sensor].pressure);

        if (tempChart.data.datasets[0].data.length > 10) {
            tempChart.data.datasets[0].data.shift();
            pressureChart.data.datasets[0].data.shift();
        }

        tempChart.update();
        pressureChart.update();

        // Update latest temperature and pressure values
        document.getElementById(`${sensor}_latest_temperature`).textContent = data[sensor].temperature.toFixed(2);
        document.getElementById(`${sensor}_latest_pressure`).textContent = data[sensor].pressure.toFixed(2);
    });
});