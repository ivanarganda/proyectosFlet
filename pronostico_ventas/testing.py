import re
import io
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error

def load_file(path: str):
    """
    Load a dataset from a local path or URL (including Google Drive).
    Supports CSV, Excel, JSON, Parquet, Feather, and Pickle formats.
    """
    # Map extensions to pandas functions
    extensions = {
        "csv": pd.read_csv,
        "xlsx": pd.read_excel,
        "xls": pd.read_excel,
        "json": pd.read_json,
        "parquet": pd.read_parquet,
        "feather": pd.read_feather,
        "pickle": pd.read_pickle,
    }

    url_pattern = r"^https?:\/\/"

    # If it's a URL
    if re.match(url_pattern, path):
        # Handle Google Drive links
        if "drive.google.com" in path:
            file_id = re.search(r"/d/([a-zA-Z0-9_-]+)", path)
            if file_id:
                path = f"https://drive.google.com/uc?id={file_id.group(1)}"

        # Download content
        response = requests.get(path)
        if response.status_code != 200:
            raise ValueError(f"Error {response.status_code} while accessing URL: {path}")

        # Guess file extension
        extension_match = re.search(r"\.(\w+)(?:\?|$)", path)
        extension = extension_match.group(1).lower() if extension_match else "csv"

        # Read file based on extension
        if extension in ["csv", "txt"]:
            df = pd.read_csv(io.StringIO(response.content.decode("utf-8")))
        elif extension in ["xlsx", "xls"]:
            df = pd.read_excel(io.BytesIO(response.content))
        elif extension == "json":
            df = pd.read_json(io.StringIO(response.content.decode("utf-8")))
        else:
            raise ValueError(f"Unsupported extension in URL: '{extension}'")

    # If it's a local file
    else:
        extension = path.split(".")[-1].lower()
        if extension not in extensions:
            raise ValueError(f"Unsupported file type: {extension}")
        df = extensions[extension](path)

    return df


df = load_file("./all_stocks_5yr.csv")

def leap_year(year: int) -> bool:
    """Check if a year is a leap year."""
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)

#  Create ranges of date
range_years = list(range(int(df["date"].min().split("-")[0]) , int(df["date"].max().split("-")[0])))
range_months = list(range(1,13))
febrary_days = 29 if leap_year(range_years[2]) else 28
month_days = {1:31, 2:febrary_days, 3:31, 4:30, 5:31, 6:30, 7:31, 8:31, 9:30, 10:31, 11:30, 12:31}
month = month_days[2]+1 if leap_year(range_years[2]) else month_days[2]
range_days = list(range(1,month+1))

print( range_years , range_months, range_days )

