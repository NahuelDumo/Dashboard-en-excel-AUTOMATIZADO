# utils/data_loader.py
import pandas as pd
import streamlit as st

@st.cache_data(show_spinner="Cargando archivos...")
def load_multiple_excels(uploaded_files):
    """
    Carga múltiples archivos Excel y los concatena en un DataFrame.
    También busca y procesa el archivo PLANES si existe.
    Retorna: (DataFrame_combinado, dict_planes_o_None)
    """
    dfs = []
    planes_data = None
    
    for file in uploaded_files:
        # Verificar si es el archivo de PLANES (nombre debe empezar con "PLANES")
        if file.name.upper().startswith("PLANES"):
            planes_data = load_planes_file(file)
            st.info(f"Archivo de planes cargado: {file.name}")
            continue
            
        # Para archivos de datos regulares (lógica original)
        ext = file.name.split(".")[-1].lower()
        if ext == "xlsb":
            df = pd.read_excel(file, engine="pyxlsb")
        elif ext == "xls":
            # Requiere paquete 'xlrd'
            df = pd.read_excel(file, engine="xlrd")
        else:
            # Para xlsx/xlsm usará openpyxl automáticamente
            df = pd.read_excel(file)
        dfs.append(df)
    
    # Si no hay dataframes de datos, retornar DataFrame vacío
    if not dfs:
        return pd.DataFrame(), planes_data
        
    # Concatenar todos los DataFrames de datos (lógica original)
    combined_df = pd.concat(dfs, ignore_index=True)
    return combined_df, planes_data

def load_planes_file(file):
    """
    Carga y procesa el archivo de PLANES.
    Retorna un diccionario con {nombre_plan: [lista_codigos_clientes]}
    """
    try:
        # Leer el archivo Excel usando la misma lógica que load_multiple_excels
        ext = file.name.split(".")[-1].lower()
        if ext == "xlsb":
            df = pd.read_excel(file, engine="pyxlsb", header=None)
        elif ext == "xls":
            df = pd.read_excel(file, engine="xlrd", header=None)
        else:
            df = pd.read_excel(file, header=None)
        
        planes_dict = {}
        
        # Procesar cada columna
        for col_idx in range(len(df.columns)):
            # Primera fila contiene el nombre del plan
            nombre_plan = df.iloc[0, col_idx]
            
            # Si el nombre del plan no está vacío
            if pd.notna(nombre_plan) and str(nombre_plan).strip():
                nombre_plan = str(nombre_plan).strip()
                
                # Extraer códigos de clientes de esa columna (desde fila 1 en adelante)
                codigos = []
                for row_idx in range(1, len(df)):
                    codigo = df.iloc[row_idx, col_idx]
                    if pd.notna(codigo):
                        # Convertir a string y limpiar
                        codigo_str = str(codigo).strip()
                        if codigo_str and codigo_str != 'nan':
                            # Si es número, convertir a int para quitar decimales
                            try:
                                codigo_int = int(float(codigo_str))
                                codigos.append(str(codigo_int))
                            except:
                                codigos.append(codigo_str)
                
                # Solo agregar si tiene códigos
                if codigos:
                    planes_dict[nombre_plan] = codigos
        
        return planes_dict
        
    except Exception as e:
        st.error(f"Error procesando archivo de planes: {str(e)}")
        return None