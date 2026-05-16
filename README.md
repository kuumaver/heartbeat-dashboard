# 🤖 Vital Signs Monitor Dashboard

A lightweight, real-time telemetry dashboard designed to display vitals streamed over WebSockets. The system features a fast asynchronous Python backend and a highly responsive Svelte frontend interface.

## 📋 Features
* **Real-time Streaming:** Utilizes WebSockets (`/ws`) for instant data delivery without polling overhead.
* **Three-Channel Metrics:** Tracks Heart Rate (BPM), Breath Rate (RPM), and Distance tracking measurements.
* **Live Dynamic Graphing:** Uses Chart.js line charts optimized with disabled animations for ultra-low CPU footprint during continuous updates.
* **Dual Execution Environments:** Includes a Mock Mode for desktop/local development and a Hardware Serial Mode for production on a Raspberry Pi connected to an ESP32 microcontroller.

## 🗂️ Project Structure
```text
├── backend/
│   ├── main.py          # FastAPI server application and WebSocket coordinator
│   ├── sensor.py        # Sensor reading architecture (Mock / Hardware Serial)
│   └── requirements.txt # Python ecosystem dependencies
└── frontend/
    ├── src/
    │   ├── components/  # Isolated UI chart modules (Heartbeat, Breath, Distance)
    │   ├── App.svelte   # Primary layout, dashboard interface, and WS controller
    │   └── main.js      # Svelte 5 initialization mount point
    ├── index.html       # Application entry frame
    └── package.json     # Node framework configurations and build scripts

    Here is the updated and complete `README.md` file for your project. It now includes explicit environment version verification steps, comprehensive installation guides, and a dedicated section mapping your everyday run commands to the workflow you are already familiar with.

```markdown
# 🤖 Vital Signs Monitor Dashboard

A lightweight, real-time telemetry dashboard designed to display vitals streamed over WebSockets. The system features a fast asynchronous Python backend and a highly responsive Svelte frontend interface.

## 📋 Features
* **Real-time Streaming:** Utilizes WebSockets (`/ws`) for instant data delivery without polling overhead.
* **Three-Channel Metrics:** Tracks Heart Rate (BPM), Breath Rate (RPM), and Distance tracking measurements.
* **Live Dynamic Graphing:** Uses Chart.js line charts optimized with disabled animations for ultra-low CPU footprint during continuous updates.
* **Dual Execution Environments:** Includes a Mock Mode for desktop/local development and a Hardware Serial Mode for production on a Raspberry Pi connected to an ESP32 microcontroller.

## 🗂️ Project Structure
```text
├── backend/
│   ├── main.py          # FastAPI server application and WebSocket coordinator
│   ├── sensor.py        # Sensor reading architecture (Mock / Hardware Serial)
│   └── requirements.txt # Python ecosystem dependencies
└── frontend/
    ├── src/
    │   ├── components/  # Isolated UI chart modules (Heartbeat, Breath, Distance)
    │   ├── App.svelte   # Primary layout, dashboard interface, and WS controller
    │   └── main.js      # Svelte 5 initialization mount point
    ├── index.html       # Application entry frame
    └── package.json     # Node framework configurations and build scripts

```

---

## 🛠️ Initial Setup & Installation

Follow these steps when setting up the project on a new computer for the first time.

### 1. Verify Prerequisites (Version Check)

Open your terminal or command prompt and ensure you have the required runtimes installed by checking their versions:

* **Python 3.9 or higher** Check by running:
```bash
python --version

```


*(Note: If `python` isn't recognized, try `python3 --version`)*
* **Node.js LTS (v18 or higher) & NPM** Check by running:
```bash
node -v
npm -v

```



### 2. Backend Installation & Environment Setup

Navigate into the backend directory to isolate your environment and pull down the python packages:

1. Move to the backend folder:
```bash
cd backend

```


2. Create a local virtual environment (`venv`) to keep your system dependencies clean:
```bash
python -m venv venv

python -m venv lifesaving-env (for raspberry pi 5)

```


3. Activate the virtual environment:
* **Windows (Command Prompt):** `venv\Scripts\activate`
* **Windows (PowerShell):** `.\venv\Scripts\Activate.ps1`
* **macOS / Linux:** `source lifesaving-env/bin/activate`


4. Install all python requirements listed in the config file:
```bash
pip install -r requirements.txt

```


5. Create a local environment configuration file named `.env` directly inside the `backend/` directory to control your mode execution:
```env
USE_MOCK=true

```


*(Setting this to `true` allows the app to simulate sensor telemetry data safely on your PC without needing a physical hardware serial device attached).*

### 3. Frontend Installation

Open a separate terminal window and install the web development assets:

1. Move to the frontend folder:
```bash
cd frontend

```


2. Install the necessary JavaScript module packages:
```bash
npm install

```



---

## 🚀 Everyday Run Commands

Every time you reopen this project to run it locally, you will need to start both the backend server and the frontend server simultaneously using separate terminal windows.

If you are coming from a traditional PHP/Laravel stack, here is how the commands map directly to what you already know:

### 🔹 1. Running the Backend Server

Instead of using a command like `php artisan serve`, you will use **Uvicorn** to serve the FastAPI backend app.

1. Open a terminal and enter the backend directory:
```bash
cd backend

```


2. Make sure your virtual environment is activated:
```bash
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

```


3. Boot up the local web api container:
```bash
uvicorn main:app --reload --port 8001

```


* The backend application container will now be actively hosting its live processes over at: `http://localhost:8000`



### 🔹 2. Running the Frontend UI

This uses the exact same layout script workflow you are familiar with from your previous projects.

1. Open a second terminal window and enter the frontend directory:
```bash
cd frontend

```


2. Launch your local hot-reloading development server layout environment:
```bash
npm run dev

```


3. Launch your browser window and navigate to the application address output by Vite (typically `htstp://localhost:5173`) to view your real-time vital signs dashboard streaming telemetry parameters dynamically.

```

```