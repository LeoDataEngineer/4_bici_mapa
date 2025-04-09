import pandas as pd
import os
#from config import *  # CLIENT_ID y CLIENT_SECRET
from google.cloud import bigquery



client_id = os.environ['CLIENT_ID']
client_secret = os.environ['CLIENT_SECRET']

# Autenticación con Google Cloud
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "clave_gcp.json" 

# URLs de los endpoints
endpoint_1 = f'https://apitransporte.buenosaires.gob.ar/ecobici/gbfs/stationInformation?client_id={client_id}&client_secret={client_secret}'
endpoint_2 = f'https://apitransporte.buenosaires.gob.ar/ecobici/gbfs/stationStatus?client_id={client_id}&client_secret={client_secret}'

def get_and_clean_df(endpoint):
    json = pd.read_json(endpoint)
    df = pd.DataFrame(json['data'][0])

    if endpoint == endpoint_1:
        columnas_a_eliminar = ['physical_configuration', 'altitude', 'is_charging_station',
                               'obcn', '_ride_code_support', 'rental_uris', 'cross_street', 
                               'post_code', 'rental_methods', 'groups', 'short_name', 'nearby_distance']
        df = df.drop(columns=columnas_a_eliminar)
        df['station_id'] = df['station_id'].astype('int64')

    elif endpoint == endpoint_2:
        columnas_a_eliminar = ['num_bikes_available_types', 'is_charging_station', 'traffic']
        df = df.drop(columns=columnas_a_eliminar)
        df['last_reported'] = pd.to_datetime(df['last_reported'], unit='s')
        df['station_id'] = df['station_id'].astype('int64')

    return df

# Obtener y limpiar los DataFrames
df_1 = get_and_clean_df(endpoint_1)
df_2 = get_and_clean_df(endpoint_2)

# Subir a BigQuery con google-cloud-bigquery
client = bigquery.Client()

# Dataset y tablas
project_id = 'nimble-sight-395723'                   # ID de proyecto
dataset_id = 'bici'                                  # Dataset
tabla_1 = 'station_information'
tabla_2 = 'station_status'

# Tabla completa (dataset.tabla)
table_id_1 = f'{project_id}.{dataset_id}.{tabla_1}'
table_id_2 = f'{project_id}.{dataset_id}.{tabla_2}'

# Cargar los DataFrames a BigQuery
job_1 = client.load_table_from_dataframe(df_1, table_id_1, job_config=bigquery.LoadJobConfig(write_disposition="WRITE_APPEND",  autodetect=True))
job_2 = client.load_table_from_dataframe(df_2, table_id_2, job_config=bigquery.LoadJobConfig(write_disposition="WRITE_APPEND",  autodetect=True))

# Esperar a que terminen los jobs
job_1.result()
job_2.result()

print("Datos subidos correctamente a BigQuery.")
