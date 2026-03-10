import pandas as pd
import requests
import os
import numpy as np
from datetime import datetime

GPR_URL = "https://www.matteoiacoviello.com/gpr_files/data_gpr_daily_recent.xls"
TEMP_FILE = "gpr_data.xls"

def fetch_latest_gpr(threshold_std=2.0):
    """
    Downloads and analyzes the Geopolitical Risk Index (GPR).
    Returns (latest_value, is_spiking, message)
    """
    try:
        print(f"Fetching GPR data from {GPR_URL}...")
        response = requests.get(GPR_URL, timeout=15)
        response.raise_for_status()
        
        with open(TEMP_FILE, "wb") as f:
            f.write(response.content)
            
        # Read Excel
        # Iacoviello's file often has 'Date' as the first column
        df = pd.read_excel(TEMP_FILE)
        
        # Clean up: Find the GPR column (usually named 'GPR' or 'GPR_DAILY')
        # Typical columns: ['Date', 'GPR']
        if 'GPR' in df.columns:
            gpr_col = 'GPR'
        elif 'GPR_DAILY' in df.columns:
            gpr_col = 'GPR_DAILY'
        else:
            # Fallback to the second column if headers are weird
            gpr_col = df.columns[1]
            
        df = df.dropna(subset=[gpr_col])
        
        # Calculate stats for spikes
        latest_val = df[gpr_col].iloc[-1]
        mean_val = df[gpr_col].mean()
        std_val = df[gpr_col].std()
        
        z_score = (latest_val - mean_val) / std_val
        is_spiking = z_score > threshold_std
        
        status = "SPIKING" if is_spiking else "Normal"
        msg = f"Latest GPR: {latest_val:.2f} (Z-Score: {z_score:.2f}) - Status: {status}"
        
        # Clean up temp file
        if os.path.exists(TEMP_FILE):
            os.remove(TEMP_FILE)
            
        return latest_val, is_spiking, msg

    except Exception as e:
        print(f"Error fetching GPR: {e}")
        return None, False, f"GPR Fetch Error: {e}"

if __name__ == "__main__":
    val, spike, msg = fetch_latest_gpr()
    print(msg)
