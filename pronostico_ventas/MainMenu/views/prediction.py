import pandas as pd
from prophet import Prophet
import matplotlib.pyplot as plt
import joblib  # para guardar el modelo
import os

# Ruta del dataset

# Cargar datos
df = pd.read_csv("./all_stocks_5yr.csv")

# Elegimos una acción (puedes cambiar el nombre)
accion = "AAPL"  # ejemplo: Apple
data = df[df["Name"] == accion].copy()

# Preparamos los datos para Prophet
data = data[["date", "close"]]
data.rename(columns={"date": "ds", "close": "y"}, inplace=True)

# Convertir fechas al formato correcto
data["ds"] = pd.to_datetime(data["ds"])

# Creamos el modelo Prophet
model = Prophet(
    yearly_seasonality=True,
    weekly_seasonality=True,
    daily_seasonality=False,
    seasonality_mode="multiplicative"
)

# Entrenamos el modelo
model.fit(data)

# Hacemos predicciones a futuro
future = model.make_future_dataframe(periods=60)  # 60 días hacia adelante
forecast = model.predict(future)

print(forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail())
