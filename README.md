# SCADA AI Monitoring System
🚀 **Real-time SCADA monitoring system with synthetic data generation, anomaly detection, and a web dashboard.**

---

## Features
✅ **SCADA Sensor Data Simulation** – Generates realistic sensor data (temperature, pressure, flow rate, etc.).  
✅ **Real-Time Monitoring** – Uses MQTT to stream sensor data.  
✅ **Anomaly Detection** – Detects spikes, threshold violations, and sensor drift.  
✅ **Automated Alerts** – Logs alerts into a database and sends email notifications.  
✅ **Web Dashboard** – Displays live sensor data and alerts via a Flask-Dash web interface.  

---

## 1️⃣ Installation

### Step 1: Clone the Repository
```sh
git clone https://github.com/your-username/scada-ai-monitor.git
cd scada-ai-monitor
```

### Step 2: Install Dependencies
```sh
pip install -r requirements.txt
```

### Step 3: Configure the System
Modify **`config.json`** to set up:  
- **Sensors & their behavior** (drift, noise, thresholds)  
- **Failure conditions** (e.g., overheating, pressure spikes)  
- **MQTT settings** (for real-time streaming)  
- **Email notifications** (SMTP settings)  

---

## 2️⃣ Usage

### 1. Generate Synthetic SCADA Data
```sh
python scada_data_generator.py
```
📌 *This script generates realistic sensor data based on `config.json` and saves it in CSV, JSON, or a database.*  

### 2. Start Real-Time SCADA Monitoring
```sh
python scada_monitor.py
```
📌 *This script:*  
- **Listens for live sensor data via MQTT**  
- **Checks for anomalies (spikes, drift, threshold violations)**  
- **Logs alerts into an SQLite database**  
- **Sends email notifications for critical failures**  

### 3. Launch the Web Dashboard
```sh
python scada_dashboard.py
```
📌 *Visit:* **[`http://localhost:8050`](http://localhost:8050)**  
- **View real-time sensor readings**  
- **Monitor live alerts**  
- **Analyze past anomalies**  

---

## 3️⃣ Configuration
Modify `config.json` to adjust system behavior.

```json
{
  "sensors": [
    {
      "name": "temperature",
      "base_value": 100,
      "drift_rate": 0.01,
      "spike_frequency": 0.01,
      "spike_magnitude": 15,
      "noise_std": 0.5,
      "threshold": 120,
      "missing_data_rate": 0.01
    }
  ],
  "mqtt": {
    "broker": "mqtt.eclipseprojects.io",
    "port": 1883,
    "topic": "scada/sensors"
  },
  "email": {
    "sender_email": "your-email@gmail.com",
    "receiver_email": "alerts@example.com",
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 465,
    "sender_password": "yourpassword"
  }
}
```

---

## 4️⃣ Project Structure
```
/scada-ai-monitor
  ├── config.json                  # Configuration for sensors, alerts, MQTT, email
  ├── requirements.txt              # Dependencies
  ├── LICENSE                       # Open-source license (Apache 2.0)
  ├── README.md                     # Documentation
  ├── scada_data_generator.py       # Generates synthetic sensor data
  ├── scada_monitor.py              # Monitors real-time SCADA data & detects anomalies
  ├── scada_dashboard.py            # Web dashboard for live monitoring
  ├── /output_data                  # Folder for generated CSV/JSON files
  ├── /models                       # (Optional) AI models for anomaly detection
```

---

## 5️⃣ Roadmap
🛠 **Planned Features:**  
- ✅ **Real-time anomaly detection (DONE)**  
- ✅ **Email alerts for failures (DONE)**  
- 📊 **Live sensor trend graphs in dashboard**  
- 📩 **Slack/SMS notifications for critical failures**  
- 📡 **Integration with external SCADA APIs**  

📌 Want a feature? Open an [Issue](https://github.com/CCCSAdams/SDGenMon/issues).  

---

## 6️⃣ Contributing
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

## 7️⃣ License
📜 This project is licensed under the **Apache License 2.0**.  
See [LICENSE](LICENSE) for details.

---

## 8️⃣ Contact
📧 **Email:** sadams@ccandc.ai  
🌍 **Website:** [CC&C](https://ccandc.ai)  

---
