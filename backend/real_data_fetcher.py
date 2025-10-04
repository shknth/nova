# import earthaccess

# from xarray import open_dataset


# auth = earthaccess.login(strategy="interactive", persist=True)  # authenticate with Earthdata Login
# results = earthaccess.search_data(
#     short_name="TEMPO_O3_L3", 
#     version="V03",
#     temporal=("2024-08-30", "2024-09-01")  
# )

# print(f"Found {len(results)} granules.")

# earthaccess.download(results, local_path="tempo_data/SO2/")

# # xarray.open_dataset("tempo_data/TEMPO_HCHO_L3_V03_20250401_20251001.nc")

# curl -X GET "https://api.openaq.org/v3/locations?parameters_id=2&limit=1000" \
#      -H "X-API-Key: edca264c44c7f9f67ed3c43e6e53fd7eddc84fa474b3ef268bddabe26d3b6f7e"

# --------------------------------------------------------------------------------------

from openaq import OpenAQ
import pandas as pd
api = OpenAQ(api_key="edca264c44c7f9f67ed3c43e6e53fd7eddc84fa474b3ef268bddabe26d3b6f7eY")
# Example: get recent NO2 measurements in a country (e.g., US) in a pandas DataFrame
status, resp = api.measurements(city='Dublin', parameter='no2', date_from='2025-08-30', date_to='2025-09-01', df=True)

df=pd.DataFrame(resp)
df.to_csv("openaq_no2_dublin.csv", index=False)

# --------------------------------------------------------------------------------------

# results = earthaccess.search_data(
#     short_name="M2I1NXASM",
#     temporal=("2025-08-30", "2025-09-01"),
#     bounding_box=(-10.5, 51.4, -5.4, 55.4)  # example: a bounding box over CONUS (optional)
# )
# earthaccess.download(results, local_path="merra2_weather/ireland/")
