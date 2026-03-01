import pandas as pd
import re
from thefuzz import process

def clean_emails(email):
    """Limpia y valida el formato básico de un email."""
    if pd.isna(email): return None
    email = str(email).lower().strip()
    regex = r'^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
    return email if re.search(regex, email) else "Formato Inválido"

def standardize_categories(df, column, threshold=80):
    """
    Usa Lógica Difusa para agrupar palabras similares.
    Ej: 'Vzla', 'Venezuela' y 'venezuela' -> 'Venezuela'
    """
    unique_values = df[column].unique().tolist()
    mapped_values = {}
    
    for val in unique_values:
        if val not in mapped_values:
            # Encuentra las mejores coincidencias en la lista
            matches = process.extract(val, unique_values, limit=len(unique_values))
            for match, score in matches:
                if score >= threshold:
                    mapped_values[match] = val
                    
    return df[column].map(mapped_values)

def process_data(file):
    """Carga el archivo y aplica las limpiezas."""
    df = pd.read_csv(file) if file.name.endswith('.csv') else pd.read_excel(file)
    
    # 1. Eliminar filas vacías
    df = df.dropna(how='all')
    
    # 2. Limpiar nombres de columnas (quitar espacios y poner minúsculas)
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    
    return df