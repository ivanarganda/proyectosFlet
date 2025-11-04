import os
import sys
import pandas as pd
import re

def replaceAll( col , sval , dval ):

    col_replaced = col.astype(str)
    col_replaced = col

    for s, d in zip(sval, dval):
        col_replaced = col_replaced.str.replace(s, d, regex=True)
    return col_replaced

def sanatize_cols( cols ):

    clean_cols = []

    for col in cols:
        col = (
            col
                .astype(str)
                .str.strip()
        )

        col = replaceAll(
            col,
            [",", r"[\$\%\€\&]", r"[^\d\.]"],  # regex: elimina todo lo que no sea número o punto
            ["", "", ""]
        )

        col = pd.to_numeric(col, errors="coerce").fillna(0)
        clean_cols.append( col )

    return clean_cols

year_selected = "2013"
path = "./tablas_exportadas"

files = os.listdir(path)

if not files:
    print(f"No hay ficheros en el directorio {path}")
    sys.exit()

# Filtrar solo los ficheros del año seleccionado
dir_list = [file for file in files if file.startswith(year_selected)]

if not dir_list:
    print(f"No hay ficheros del año {year_selected}")
    sys.exit()

# Extraer alias del primer fichero (ej. nombre base sin la fecha)
file_alias = re.sub(r"^\d+_", "", dir_list[0])

all_data = []

for file in dir_list:
    try:
        df = pd.read_csv(f"{path}/{file}")
        # ✅ Eliminar filas con valores nulos en cualquier columna
        df = df.dropna(how="any")

        # Añadir fecha como columna legible
        date = file.split("_")[0]
        df["trading_date"] = f"{date[:4]}/{date[4:6]}/{date[6:8]}"

        df = df[df["trading_date"].str.match(r"^\d{4}/\d{2}/\d{2}$", na=False)]

        # Algunos tienen la columna volume (24h)
        if not "volume (24h)" in df.columns:
            df["volume (24h)"] = "0"            

        all_data.append(df)
        print(f"✅ Procesado {file} ({len(df)} filas después de limpiar)")
    except Exception as e:
        print(f"⚠️ Error al procesar {file}: {e}")
        continue

if not all_data:
    print("❌ No se generaron datos válidos")
    sys.exit()

# Combinar todos los DataFrames
final_df = pd.concat(all_data, ignore_index=True)

# Eliminar duplicados si fuera necesario
final_df = final_df.drop_duplicates()

print( final_df.dtypes )

columns = dict(final_df.dtypes)

for key,type_ in columns.items():
    final_df[key] = final_df[key].replace("--","0")

final_df["Circulating Supply"] = final_df["Circulating Supply"].apply( lambda val: val.split(" ")[0])

final_df["volume (24h)"], final_df["Market Cap"], final_df["Price"], final_df["Circulating Supply"], final_df["% 1h"], final_df["% 24h"], final_df["% 7d"] = sanatize_cols( 
    [ final_df["volume (24h)"] , final_df["Market Cap"] , final_df["Price"], final_df["Circulating Supply"], final_df["% 1h"], final_df["% 24h"], final_df["% 7d"]  ] 
)

# Guardar todo en un solo CSV por año
output_file = f"{year_selected}_{file_alias}"
final_df.to_csv(output_file, index=False)

print(f"\n💾 Datos limpios y combinados guardados en: {output_file}")
print(f"📊 Total de filas finales: {len(final_df)}")