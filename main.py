import os
import gzip
import json
import time
import shutil
import requests
import xarray as xr
import numpy as np
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Radar Weather API",
    description="Provides latest MRMS Reflectivity at Lowest Altitude (RALA) data as JSON for frontend display.",
    version="1.1"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MRMS_URL = "https://mrms.ncep.noaa.gov/2D/ReflectivityAtLowestAltitude/MRMS_ReflectivityAtLowestAltitude.latest.grib2.gz"
GRIB_GZ = "reflectivity.grib2.gz"
GRIB_FILE = "reflectivity.grib2"
JSON_FILE = "reflectivity.json"


def safe_download():
    """Download MRMS data in chunks with retry and handle incomplete reads."""
    print("⏳ Downloading MRMS radar data...")

    for attempt in range(3):
        try:
            with requests.get(MRMS_URL, stream=True, timeout=120) as r:
                r.raise_for_status()
                with open(GRIB_GZ, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            print("✅ File downloaded successfully.")
            return
        except Exception as e:
            print(f"⚠️ Attempt {attempt+1} failed: {e}")
            time.sleep(3)

    raise Exception("❌ Download failed after 3 attempts")


def download_and_extract():
    """Download and decompress MRMS reflectivity file if cache is old."""
    # Cache for 15 minutes
    if os.path.exists(GRIB_FILE):
        age = time.time() - os.path.getmtime(GRIB_FILE)
        if age < 900:
            print("⏩ Using cached radar file")
            return

    safe_download()

    with gzip.open(GRIB_GZ, "rb") as f_in, open(GRIB_FILE, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)

    print("✅ Extracted GRIB2 file.")


def convert_to_json():
    """Convert GRIB2 radar data into simplified JSON with lat/lon/value."""
    print("🔄 Converting GRIB2 to JSON...")
    ds = xr.open_dataset(GRIB_FILE, engine="cfgrib")

    var_name = next((v for v in ds.data_vars if "Reflectivity" in v or "DZ" in v), list(ds.data_vars.keys())[0])
    ds_small = ds[var_name].isel(
        {
            list(ds[var_name].dims)[0]: slice(None, None, 20),
            list(ds[var_name].dims)[1]: slice(None, None, 20)
        }
    )

    lat = ds["latitude"].values
    lon = ds["longitude"].values
    values = np.nan_to_num(ds_small.values)

    points = []
    for i, la in enumerate(lat[::20]):
        for j, lo in enumerate(lon[::20]):
            val = float(values[i, j])
            if val > -50:
                lon_fixed = float(lo - 360 if lo > 180 else lo)
                points.append({"lat": float(la), "lon": lon_fixed, "value": val})

    timestamp = ""
    if "time" in ds.coords:
        try:
            timestamp = str(ds.time.values.item())
        except Exception:
            timestamp = str(ds.time.values)

    data = {
        "timestamp": timestamp,
        "metadata": {
            "units": ds[var_name].attrs.get("units", ""),
            "long_name": ds[var_name].attrs.get("long_name", "Reflectivity at Lowest Altitude"),
            "source": MRMS_URL
        },
        "points": points
    }

    with open(JSON_FILE, "w") as f:
        json.dump(data, f)

    print(f"✅ Saved JSON with {len(points)} valid points.")
    return data


@app.get("/radar")
def get_radar():
    try:
        download_and_extract()
        data = convert_to_json()
        return JSONResponse(content=data)
    except Exception as e:
        print("❌ Error fetching radar:", e)
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/")
def root():
    return {"message": "Radar Weather API is running. Visit /radar for data."}
