import pandas as pd
import requests
import os
import numpy as np
from datetime import datetime

GPR_URL = "https://www.matteoiacoviello.com/gpr_files/data_gpr_daily_recent.xls"
TEMP_FILE = "gpr_data.xls"

def _ensure_data():
    if not os.path.exists(TEMP_FILE):
        print(f"Fetching GPR data from {GPR_URL}...")
        response = requests.get(GPR_URL, timeout=15)
        response.raise_for_status()
        with open(TEMP_FILE, "wb") as f:
            f.write(response.content)

def fetch_latest_gpr(threshold_std=2.0):
    """
    Downloads and analyzes the Geopolitical Risk Index (GPR).
    Returns (latest_value, is_spiking, message)
    """
    try:
        _ensure_data()
        df = pd.read_excel(TEMP_FILE)
        
        if 'GPR' in df.columns:
            gpr_col = 'GPR'
        elif 'GPR_DAILY' in df.columns:
            gpr_col = 'GPR_DAILY'
        else:
            gpr_col = df.columns[1]
            
        df = df.dropna(subset=[gpr_col])
        latest_val = df[gpr_col].iloc[-1]
        mean_val = df[gpr_col].mean()
        std_val = df[gpr_col].std()
        
        z_score = (latest_val - mean_val) / std_val
        is_spiking = z_score > threshold_std
        
        status = "SPIKING" if is_spiking else "Normal"
        msg = f"Latest GPR: {latest_val:.2f} (Z-Score: {z_score:.2f}) - Status: {status}"
        
        return latest_val, is_spiking, msg

    except Exception as e:
        print(f"Error fetching GPR: {e}")
        return None, False, f"GPR Fetch Error: {e}"

def fetch_historical_gpr(threshold_std=2.0):
    """
    Downloads and returns the historical GPR series with Z-scores.
    """
    try:
        _ensure_data()
        df = pd.read_excel(TEMP_FILE)
        
        if 'Date' not in df.columns:
            df = df.rename(columns={df.columns[0]: 'Date'})
            
        if 'GPR' in df.columns:
            gpr_col = 'GPR'
        elif 'GPR_DAILY' in df.columns:
            gpr_col = 'GPR_DAILY'
        else:
            gpr_col = df.columns[1]
            
        df = df[['Date', gpr_col]].dropna()
        df['Date'] = pd.to_datetime(df['Date'])
        
        mean_val = df[gpr_col].mean()
        std_val = df[gpr_col].std()
        
        df['Z-Score'] = (df[gpr_col] - mean_val) / std_val
        df['Is_Spiking'] = df['Z-Score'] > threshold_std
        
        return df[['Date', 'Z-Score', 'Is_Spiking']]

    except Exception as e:
        print(f"Error fetching historical GPR: {e}")
        return pd.DataFrame()

if __name__ == "__main__":
    val, spike, msg = fetch_latest_gpr()
    print(msg)
    
    hist_df = fetch_historical_gpr()
    if not hist_df.empty:
        print("\nHistorical GPR (Last 5 days):")
        print(hist_df.tail())
