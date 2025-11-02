# 🚀 Radar Weather API (FastAPI)

This project is a FastAPI backend that serves radar weather data.  
It runs with **Uvicorn** (development) or **PM2** (production).

---

## 🧰 Prerequisites

Make sure your server has:
- Python 3.9 or higher  
- pip  
- npm (to install PM2)

---

## ⚙️ Setup Commands

### 1️⃣ Clone the Project
```bash
git clone https://github.com/varinder-singh1/varinder_rwrd_backend.git
cd varinder_rwrd_backend


2️⃣ Create Virtual Environment
python3 -m venv venv
source venv/bin/activate

3️⃣ Install Dependencies
pip install -r requirements.txt

If pip warns about system packages, use:

pip install -r requirements.txt --break-system-packages

Run in Development Mode
source venv/bin/activate
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload