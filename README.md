# SCADA AI Monitoring System
🚀 **Real-time SCADA monitoring system with synthetic data generation, anomaly detection, and a web dashboard.**

---

## Features
✅ **SCADA Sensor Data Simulation** – Generates realistic sensor data (temperature, pressure, flow rate, etc.).  
✅ **Real-Time Monitoring** – Uses MQTT to stream sensor data.  
✅ **Anomaly Detection** – Detects spikes, threshold violations, and sensor drift.  
✅ **Automated Alerts** – Logs alerts into a database and sends email notifications.  
✅ **Web Dashboard** – Displays live sensor data and alerts via a Flask-Dash web interface.  
✅ **Docker Support** – Easy deployment with Docker and docker-compose.
✅ **Comprehensive Testing** – Unit tests with coverage reporting.

---

## 1️⃣ Installation

### Option A: Standard Installation

#### Step 1: Clone the Repository
```sh
git clone https://github.com/CCCSAdams/SDGenMon.git
cd SDGenMon
```

#### Step 2: Install Dependencies
```sh
pip install -r requirements.txt
```

#### Step 3: Configure the System
```sh
# Copy example environment file
cp .env.example .env

# Edit .env with your settings
nano .env
```

### Option B: Docker Installation

#### Step 1: Clone the Repository
```sh
git clone https://github.com/CCCSAdams/SDGenMon.git
cd SDGenMon
```

#### Step 2: Configure the System
```sh
# Copy example environment file
cp .env.example .env

# Edit .env with your settings
nano .env

# Create directories for MQTT broker
mkdir -p mosquitto/config mosquitto/data mosquitto/log
```

#### Step 3: Set up MQTT Configuration
```sh
# Copy example MQTT configuration
cp mosquitto/config/mosquitto.conf.example mosquitto/config/mosquitto.conf

# Edit if needed
nano mosquitto/config/mosquitto.conf
```

---

## 2️⃣ Usage

### Option A: Standard Usage

#### Run the Complete System
```sh
python run.py --all
```

#### Run Individual Components
```sh
# Generate synthetic data
python run.py --generate-data

# Simulate sensor publishing
python run.py --simulate-sensors

# Run SCADA monitor
python run.py --monitor

# Run dashboard
python run.py --dashboard
```

### Option B: Docker Usage

#### Start the System
```sh
docker-compose up -d
```

#### View Logs
```sh
docker-compose logs -f
```

#### Stop the System
```sh
docker-compose down
```

### Access the Dashboard
📌 *Visit:* **[`http://localhost:8050`](http://localhost:8050)**  
- **View real-time sensor readings**  
- **Monitor live alerts**  
- **Analyze sensor trends**  

---

## 3️⃣ Configuration
Modify `config.json` or use environment variables to adjust system behavior.

### Environment Variables

Important environment variables that can be set in `.env`:

- `MQTT_BROKER` - MQTT broker hostname/IP
- `MQTT_PORT` - MQTT broker port
- `MQTT_USERNAME` - MQTT authentication username (if required)
- `MQTT_PASSWORD` - MQTT authentication password (if required)
- `SMTP_EMAIL` - Email address for sending alerts
- `SMTP_PASSWORD` - Email password or app password
- `SMTP_SERVER` - SMTP server address
- `SMTP_PORT` - SMTP server port

---

## 4️⃣ Project Structure
```
/SDGenMon
  ├── config.json                  # Configuration for sensors, alerts, MQTT, email
  ├── .env.example                 # Example environment variables
  ├── requirements.txt             # Dependencies
  ├── run.py                       # Script to run the full system
  ├── README.md                    # Documentation
  ├── LICENSE                      # Open-source license (Apache 2.0)
  ├── Dockerfile                   # Docker configuration
  ├── docker-compose.yml           # Docker Compose configuration
  │
  ├── utils.py                     # Shared utility functions
  ├── scada_data_generator.py      # Generates synthetic sensor data
  ├── scada_monitor.py             # Monitors real-time SCADA data & detects anomalies
  ├── scada_dashboard.py           # Web dashboard for live monitoring
  ├── sim_scada_sensor_publish.py  # Simulates sensor data publishing
  │
  ├── test_*.py                    # Unit tests
  ├── run_tests.py                 # Script to run all tests
  │
  ├── /mosquitto                   # MQTT broker configuration
  │   ├── /config                  # Configuration files
  │   ├── /data                    # Persistence data
  │   └── /log                     # Log files
  │
  └── /output_data                 # Folder for generated data files
```

---

## 5️⃣ Testing

### Run All Tests
```sh
python run_tests.py
```

### Run Individual Test Files
```sh
pytest test_utils.py -v
pytest test_scada_monitor.py -v
```

### Generate Coverage Report
```sh
pytest --cov=. --cov-report=term-missing
```

---

## 6️⃣ Security Considerations

For production use, consider these security enhancements:

1. **MQTT Authentication**: Enable username/password authentication in `mosquitto.conf` and configure credentials in `.env`.

2. **Secure Storage**: Use a secure vault solution (like HashiCorp Vault) instead of storing credentials in `.env`.

3. **TLS/SSL**: Configure MQTT and dashboard with TLS certificates for encrypted communications.

4. **Access Control**: Implement proper access controls for the dashboard.

5. **Container Security**: Follow Docker security best practices if deploying with containers.

---

## 7️⃣ Roadmap
🛠 **Planned Features:**  
- ✅ **Real-time anomaly detection (DONE)**  
- ✅ **Email alerts for failures (DONE)**  
- ✅ **Live sensor trend graphs in dashboard (DONE)**  
- 📩 **Slack/SMS notifications for critical failures**  
- 📡 **Integration with external SCADA APIs**  
- 🔐 **Enhanced security with TLS/SSL support**

📌 Want a feature? Open an [Issue](https://github.com/CCCSAdams/SDGenMon/issues).  

---

## 8️⃣ Contributing
👥 **Contributions are welcome!**  

1. **Fork the repo**  
2. **Create a feature branch**  
   ```sh
   git checkout -b feature-name
   ```
3. **Commit your changes**  
   ```sh
   git commit -m "Added feature"
   ```
4. **Push to GitHub**  
   ```sh
   git push origin feature-name
   ```
5. **Open a Pull Request 🚀**  

---

## 9️⃣ License
📜 This project is licensed under the **Apache License 2.0**.  
See [LICENSE](LICENSE) for details.

---

## 🔟 Contact
📧 **Email:** sadams@ccandc.ai  
🌍 **Website:** [CC&C](https://ccandc.ai)  

---
