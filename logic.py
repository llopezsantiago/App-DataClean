import pandas as pd
import re

def clean_emails(email):
    if pd.isna(email) or email == "": return "Vacío"
    email = str(email).lower().strip()
    regex = r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$'
    return email if re.search(regex, email) else "Formato Inválido"

def validate_numeric(df, column):
    return pd.to_numeric(df[column], errors='coerce')

def process_data(file):
    try:
        if file.name.endswith('.csv'):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)
        df = df.dropna(how='all')
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
        return df
    except:
        return None
    
def detect_outliers(df, column):
    if not pd.api.types.is_numeric_dtype(df[column]): return None
    Q1, Q3 = df[column].quantile(0.25), df[column].quantile(0.75)
    IQR = Q3 - Q1
    return (df[column] < (Q1 - 1.5 * IQR)) | (df[column] > (Q3 + 1.5 * IQR))

def smart_impute(df, column, strategy='mean'):
    if strategy == 'mean': return df[column].fillna(df[column].mean())
    return df[column]

def advanced_text_cleaning(text):
    if pd.isna(text): return text
    text = re.sub(r'[^a-zA-Z0-9\s]', '', str(text).lower())
    return " ".join(text.split())