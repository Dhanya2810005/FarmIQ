import sqlite3
import pandas as pd
import numpy as np
import os
import re
import warnings

warnings.filterwarnings("ignore")

DB_PATH = "agri_india.db"
DATA_PROD = "files/Dataset_1.xlsx"
DATA_MANDI = "files/Dataset_2.csv"
DATA_RAIN = "files/Dataset_3.csv"
DATA_CROP_STATE = "files/horizontal_crop_vertical_year_report.xls"
DATA_EXPORT = "files/TradeStat-Eidb-Export-Commodity-wise (1).xlsx"
DATA_MSP = "files/Commodity-wise-MSP-Trend.csv"
DATA_WPI = "files/Wholesale-Price-Index-from-2012-to-2026.csv"

def setup_database():
    print("="*60)
    print("  AGRICHAIN SOLUTIONS - DATA ENGINE (ETL)")
    print("="*60)
    
    conn = sqlite3.connect(DB_PATH)
    
    # ---------------------------------------------------------
    # 1. CROP PRODUCTION DATA (Dataset_1.xlsx)
    # ---------------------------------------------------------
    print("\n[1/5] Processing Crop Production Data...")
    raw_prod = pd.read_excel(DATA_PROD, header=None)
    raw_prod.columns = [
        "Crop","Season",
        "Area_2122","Area_2223","Area_2324","Area_2425","Area_2526",
        "Prod_2122","Prod_2223","Prod_2324","Prod_2425","Prod_2526",
        "Yield_2122","Yield_2223","Yield_2324","Yield_2425","Yield_2526"
    ]
    df_prod = raw_prod.iloc[7:111].copy()
    df_prod["Crop"] = df_prod["Crop"].ffill()
    df_prod["Season"] = df_prod["Season"].astype(str).str.strip()
    
    num_cols = df_prod.columns[2:]
    for c in num_cols:
        df_prod[c] = pd.to_numeric(df_prod[c], errors="coerce")
        
    df_prod["Crop"] = df_prod["Crop"].str.strip().replace({"Soyabean": "Soybean"})
    
    MAJOR_CROPS = ['Rice', 'Wheat', 'Maize', 'Sugarcane', 'Cotton', 'Groundnut', 
                   'Rapeseed & Mustard', 'Soybean', 'Bajra', 'Gram', 'Jute & Mesta',
                   'Tur', 'Arhar/Tur', 'Urad', 'Moong', 'Lentil']
                   
    df_all = df_prod.copy()
    df_total = df_prod[df_prod["Season"] == "Total"].copy().reset_index(drop=True)
    df_season = df_prod[df_prod["Season"] != "Total"].copy().reset_index(drop=True)
    df_major = df_total[df_total["Crop"].isin(MAJOR_CROPS)].copy().reset_index(drop=True)
    
    df_all.to_sql("crop_all", conn, if_exists="replace", index=False)
    df_total.to_sql("crop_total", conn, if_exists="replace", index=False)
    df_season.to_sql("crop_season", conn, if_exists="replace", index=False)
    df_major.to_sql("crop_major", conn, if_exists="replace", index=False)
    print("  -> Tables created: crop_all, crop_total, crop_season, crop_major")

    # ---------------------------------------------------------
    # 2. MANDI MARKET DATA (Dataset_2.csv)
    # ---------------------------------------------------------
    print("\n[2/5] Processing Mandi Market Data...")
    raw_mandi = pd.read_csv(DATA_MANDI)
    raw_mandi.rename(columns={
        "Min_x0020_Price":   "Min_Price",
        "Max_x0020_Price":   "Max_Price",
        "Modal_x0020_Price": "Modal_Price"
    }, inplace=True)
    raw_mandi = raw_mandi[(raw_mandi["Modal_Price"] > 0) & (raw_mandi["Min_Price"] > 0) & (raw_mandi["Max_Price"] > 0)]
    
    stats = (raw_mandi.groupby("Commodity")
        .agg(
            n_markets=("Market", "nunique"),
            n_states=("State", "nunique"),
            min_price=("Modal_Price", "min"),
            max_price=("Modal_Price", "max"),
            avg_price=("Modal_Price", "mean"),
            median_price=("Modal_Price", "median"),
            std_price=("Modal_Price", "std"),
        ).reset_index())
    
    stats["cov_pct"] = (stats["std_price"] / stats["avg_price"] * 100).round(1)
    stats = stats[stats["n_markets"] >= 3].copy()
    
    raw_mandi.to_sql("mandi_prices", conn, index=False, if_exists="replace")
    stats.to_sql("commodity_stats", conn, index=False, if_exists="replace")
    print("  -> Tables created: mandi_prices, commodity_stats")

    # ---------------------------------------------------------
    # 3. RAINFALL DATA (Dataset_3.csv)
    # ---------------------------------------------------------
    print("\n[3/5] Processing Rainfall Data...")
    rain_raw = pd.read_csv(DATA_RAIN)
    rain_raw.columns = [c.strip() for c in rain_raw.columns]
    MONTHS = ["JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"]
    
    rain_state = rain_raw.groupby("STATE_UT_NAME")[MONTHS + ["ANNUAL","Jun-Sep"]].mean().reset_index()
    rain_state.rename(columns={"STATE_UT_NAME": "State", "Jun-Sep": "Monsoon_mm"}, inplace=True)
    rain_state["Monsoon_Pct"] = (rain_state["Monsoon_mm"] / rain_state["ANNUAL"] * 100).round(1)
    rain_state["State_Norm"] = rain_state["State"].str.strip().str.upper()
    
    rain_state.to_sql("rain_state", conn, index=False, if_exists="replace")
    print("  -> Tables created: rain_state")

    # ---------------------------------------------------------
    # 4. CROP STATE DATA (horizontal_crop...)
    # ---------------------------------------------------------
    print("\n[4/5] Processing State-level Crop Data...")
    tables = pd.read_html(DATA_CROP_STATE)
    raw_crop = tables[0]
    
    flat_cols = []
    for c in raw_crop.columns:
        if c[0] in ("State", "District", "Year"):
            flat_cols.append(c[0])
        else:
            metric = (c[2].replace("(Tonne/Hectare)","").replace("(Tonnes)","")
                      .replace("(Hectare)","").replace("(Bales)","")
                      .replace("(Nuts)","").replace("(Bales/Hectare)","")
                      .replace("(Nuts/Hectare)","").strip())
            flat_cols.append(f"{c[0]}|{metric}")
    raw_crop.columns = flat_cols
    
    raw_crop["State"] = raw_crop["State"].astype(str).apply(lambda x: re.sub(r"^\d+\.\s*", "", x).strip().upper())
    raw_crop = raw_crop[raw_crop["State"] != "NAN"].copy()
    
    crop_long_rows = []
    for col in raw_crop.columns:
        if "|" not in col: continue
        crop, metric = col.split("|", 1)
        if metric.strip() != "Yield": continue
        sub = raw_crop[["State", col]].copy()
        sub.columns = ["State", "Yield"]
        sub["Crop"] = crop
        crop_long_rows.append(sub)
        
    crop_long = pd.concat(crop_long_rows, ignore_index=True)
    crop_long["Yield"] = pd.to_numeric(crop_long["Yield"], errors="coerce")
    crop_long = crop_long.dropna(subset=["Yield"])
    
    crop_state_avg = crop_long.groupby(["State","Crop"])["Yield"].mean().reset_index()
    crop_state_avg.columns = ["State","Crop","Avg_Yield"]
    
    def norm_state(s):
        s = str(s).strip().upper()
        replace_map = {
            "CHHATTISGARH": "CHHATTISGARH",
            "UTTARAKHAND":  "UTTARAKHAND",
            "CHATTISGARH":  "CHHATTISGARH",
            "CHATISGARH":   "CHHATTISGARH",
            "JAMMU & KASHMIR": "JAMMU & KASHMIR",
            "ODISHA": "ORISSA",
        }
        return replace_map.get(s, s)
        
    crop_state_avg["State_Norm"] = crop_state_avg["State"].apply(norm_state)
    crop_state_avg.to_sql("crop_state_yield", conn, index=False, if_exists="replace")
    print("  -> Tables created: crop_state_yield")

    # ---------------------------------------------------------
    # 5. EXPORT DATA (TradeStat...)
    # ---------------------------------------------------------
    print("\n[5/5] Processing Export Data...")
    raw_exports = pd.read_excel(DATA_EXPORT, header=None, skiprows=2)
    raw_exports.columns = ["SNo", "HSCode", "Commodity", "Val_2223", "Share_2223", "Val_2324", "Share_2324", "Growth"]
    raw_exports = raw_exports.dropna(subset=["HSCode"])
    raw_exports = raw_exports[raw_exports["HSCode"] != "HSCode"]
    raw_exports["HSCode"] = pd.to_numeric(raw_exports["HSCode"], errors="coerce")
    raw_exports["Val_2324"] = pd.to_numeric(raw_exports["Val_2324"], errors="coerce")
    raw_exports["Growth"] = pd.to_numeric(raw_exports["Growth"], errors="coerce")
    
    short_names = {
        1:  "Live Animals", 2: "Meat", 3: "Fish / Seafood", 4: "Dairy / Honey",
        7:  "Vegetables", 8: "Fruit & Nuts", 9: "Spices / Tea", 10: "Cereals",
        11: "Milling Products", 12: "Oil Seeds", 15: "Fats & Oils",
        16: "Meat Preparations", 17: "Sugar Prod", 20: "Veg Preparations",
        21: "Misc Edibles", 22: "Beverages", 23: "Residues / Animal Feed"
    }
    raw_exports["ShortName"] = raw_exports["HSCode"].map(short_names).fillna(raw_exports["Commodity"].str[:20].str.title())
    
    raw_exports.to_sql("exports", conn, index=False, if_exists="replace")
    print("  -> Tables created: exports")
    
    # ---------------------------------------------------------
    # 6. MSP AND MACRO DATA (Phase 3)
    # ---------------------------------------------------------
    print("\n[6/6] Processing MSP and WPI Data...")
    try:
        raw_msp = pd.read_csv(DATA_MSP)
        raw_msp.columns = [c.strip() for c in raw_msp.columns]
        # Make crop names match for easier joins later
        raw_msp["Crop_Norm"] = raw_msp["Crop"].str.title().str.strip()
        raw_msp.to_sql("msp_data", conn, index=False, if_exists="replace")
        
        raw_wpi = pd.read_csv(DATA_WPI)
        # Melt WPI data from wide to long format for easier querying (Crop, Month_Year, Index)
        raw_wpi.rename(columns={"Crop": "Commodity"}, inplace=True)
        wpi_long = pd.melt(raw_wpi, id_vars=['Commodity'], var_name='Month_Year', value_name='WPI_Index')
        wpi_long['WPI_Index'] = pd.to_numeric(wpi_long['WPI_Index'], errors='coerce')
        wpi_long = wpi_long.dropna(subset=['WPI_Index'])
        wpi_long.to_sql("wpi_data", conn, index=False, if_exists="replace")
        
        print("  -> Tables created: msp_data, wpi_data")
    except Exception as e:
        print(f"  -> Error loading MSP or WPI data: {e}")

    conn.close()
    print("\nDatabase built successfully: ", DB_PATH)

if __name__ == "__main__":
    setup_database()
