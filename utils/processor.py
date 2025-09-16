import pandas as pd
from datetime import datetime

def extract_calibre(descripcion):
    import re
    match = re.search(r"(?:x\s*)?(\d{2,4})\s*(?:ml|cc|loc|l|lt)?", str(descripcion).lower())
    if match:
        return match.group(1)
    return "Sin Calibre"

def process_data(df, date_from, date_to):
    import re

    def extract_bultos(descripcion):
        match = re.search(r"(\d+)\s*[xX]", str(descripcion))
        return int(match.group(1)) if match else 1
        
    # Filtrar para que 'ccc ñandu' solo aparezca con calibre 330
    mask_ccc = df['Descripcion'].str.contains('ñandu', case=False, na=False)
    mask_calibre = ~df['Descripcion'].str.contains('330', na=False)
    df = df[~(mask_ccc & mask_calibre)].copy()

    df.columns = df.columns.str.strip()

    # Fechas
    # Verificar si la columna Fecha ya está en formato datetime
    if not pd.api.types.is_datetime64_any_dtype(df["Fecha"]):
        # Si no es datetime, intentar la conversión desde días desde 1899-12-30
        try:
            df["Fecha"] = pd.to_datetime("1899-12-30") + pd.to_timedelta(df["Fecha"].astype(float), unit="D")
        except (ValueError, TypeError):
            # Si falla, intentar convertir directamente a datetime
            df["Fecha"] = pd.to_datetime(df["Fecha"])
    
    # Asegurarse de que los filtros de fecha sean datetime
    date_from_dt = pd.to_datetime(date_from)
    date_to_dt = pd.to_datetime(date_to)
    
    # Eliminar filas sin fecha y aplicar filtros
    df = df.dropna(subset=["Fecha"])
    df = df[(df["Fecha"] >= date_from_dt) & (df["Fecha"] <= date_to_dt)]



    # HL y cálculos por fila
    df["HL"] = df["Kg_Lt"] / 100
    # Extraer el calibre numérico de los 'cc' y guardarlo en una nueva columna
    # Extraer el calibre numérico de los 'cc', mantener NaN si no se encuentra y luego convertir a Int64 (que soporta NaN)
    df['Calibre_CC'] = pd.to_numeric(df['Descripcion'].str.findall(r'(\d+)\s*cc').str[0], errors='coerce')

    df["Calibre"] = df["Descripcion"].apply(extract_calibre)
    df["Bultos"] = df["Descripcion"].apply(extract_bultos)

    # Bonificación y neto
    df["Bruto"] = df["NetoSD"]
    df["Neto"] = df["NetoSD"] * (1 - (df["PorcDescLinea"]/100))

    # --- Etiquetado de canal SUBDISTRIBUIDOR por lista de clientes ---
    # Si el Excel no trae este canal, lo generamos en base a la columna 'Nombre' o 'RazonSocial'.
    subdist_lista = {
        "nieto raul edgardo",
        "distribuciones aldana s.r.l",
        "palma jose lucas",
        "crede fernando miguel",
    }

    def _norm(s):
        import unicodedata
        s = str(s) if pd.notna(s) else ""
        s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
        return s.lower().strip()

    # Fuente principal de nombre de cliente
    nombre_col = None
    for c in ["Nombre", "RazonSocial"]:
        if c in df.columns:
            nombre_col = c
            break

    if nombre_col is not None:
        nombres_norm = df[nombre_col].apply(_norm)
        mask_subdist = nombres_norm.isin(subdist_lista)

        # Crear columna 'Canal' si no existe
        if "Canal" not in df.columns:
            df["Canal"] = "SIN_CANAL"

        # Asignar/forzar canal SUBDISTRIBUIDOR para esos clientes
        df.loc[mask_subdist, "Canal"] = "SUBDISTRIBUIDOR"

    return df

def build_global_summary(df, date_to, salidas_mes, salidas_actuales, cartera_manual):
    if df.empty:
        return pd.DataFrame()

    # DataFrame completo para todas las métricas EXCEPTO HL (ya viene filtrado por fechas y otros filtros)
    df_completo = df.copy()

    # DataFrame solo del último mes para HL y HL Proyectado
    # IMPORTANTE: El último mes debe estar dentro del rango de fechas ya filtrado
    ultimo_mes = pd.to_datetime(date_to).month
    ultimo_anio = pd.to_datetime(date_to).year
    df_mes = df_completo[(df_completo["Fecha"].dt.month == ultimo_mes) &
                         (df_completo["Fecha"].dt.year == ultimo_anio)].copy()

    # 1. HL (UM pasa a ser HL) - Litros VENDIDOS = KG / 100 -> SOLO DEL ULTIMO MES (dentro del rango)
    hl = df_mes["Kg_Lt"].sum() / 100 if "Kg_Lt" in df_mes.columns and not df_mes.empty else 0

    # 2. UM PROYECTADO = HectoLitro / salida * Salida del mes -> BASADO EN HL DEL ULTIMO MES
    hl_proyectado = (hl / salidas_actuales) * salidas_mes if salidas_actuales else 0

    # 3. HECTOLITROREAL = HECTOLITROREAL -> ACUMULADO DEL RANGO COMPLETO FILTRADO
    hectolitro_real = df_completo["Kg_Lt"].sum() / 100 if "Kg_Lt" in df_completo.columns else 0

    # 4. % BONIFICACION = Sale la Bruto - Neto / Bruto -> DEL RANGO COMPLETO FILTRADO
    bruto = df_completo["NetoSD"].sum()
    # El Neto se calcula sumando la columna 'Neto', que ya fue calculada en process_data
    neto = df_completo["Neto"].sum()
    print(f"--- DEBUG: VALOR DE NETO CALCULADO: {neto} ---")
    porc_bonif = ((bruto - neto) / bruto * 100) if bruto else 0

    # 5. Cálculo de clientes con compra (CCE) para diferentes categorías
    def calcular_cce(df_filtrado):
        return (
            df_filtrado.groupby("CodigoCliente")["Kg_Lt"]
            .sum()
            .loc[lambda x: x > 0]
            .count()
        )

    # CCE General (todos los productos)
    clientes_con_compra = calcular_cce(df_completo)
    
    # CCE Agua Pura (Rubro = 'AGUA')
    cce_agua_pura = 0
    if 'Rubro' in df_completo.columns:
        df_agua_pura = df_completo[df_completo['Rubro'].str.upper() == 'AGUA']
        cce_agua_pura = calcular_cce(df_agua_pura)
        print(f"DEBUG -> CCE Agua Pura: {cce_agua_pura} clientes")
    
    # CCE Agua Saborizada (Rubro = 'SABORISADAS')
    cce_agua_saborizada = 0
    if 'Rubro' in df_completo.columns:
        df_agua_saborizada = df_completo[df_completo['Rubro'].str.upper() == 'SABORISADAS']
        cce_agua_saborizada = calcular_cce(df_agua_saborizada)
        print(f"DEBUG -> CCE Agua Saborizada: {cce_agua_saborizada} clientes")
        if not df_agua_saborizada.empty:
            print(f"DEBUG -> Ejemplo de Rubros encontrados: {df_agua_saborizada['Rubro'].unique()}")
        else:
            print("DEBUG -> No se encontraron registros con Rubro = 'SABORISADAS'")
            print(f"DEBUG -> Valores únicos en Rubro: {df_completo['Rubro'].dropna().unique()}")

    # Debug información de clientes con compra
    clientes_con_kg = df_completo[df_completo["Kg_Lt"] > 0].groupby('CodigoCliente')['Kg_Lt'].sum().reset_index()
    print("DEBUG Cobertura -> Clientes con compra y sus kg:")
    for _, row in clientes_con_kg.head(10).iterrows():  # Mostrar solo los primeros 10 para no saturar
        print(f"Código: {row['CodigoCliente']}, Kg: {row['Kg_Lt']:.2f}")
    print(f"... y {len(clientes_con_kg) - 10} clientes más" if len(clientes_con_kg) > 10 else "")

    cobertura = (clientes_con_compra / cartera_manual) if cartera_manual else 0

    # 6. Drop = SUMA(BULTOS) / CCE (clientes con compra) -> DEL RANGO COMPLETO FILTRADO
    total_bultos = df_completo["Bultos"].sum() if "Bultos" in df_completo.columns else 0
    drop = total_bultos / clientes_con_compra if clientes_con_compra else 0
    print(f"DEBUG Drop -> Total Bultos: {total_bultos}, CCE: {clientes_con_compra}, Drop: {drop}")


    # 8. Sabores por PV -> Solo LEVITE. Promedio de sabores distintos por CodigoCliente
    #    (equivale a Cantidad de sabores comprados por código / Total compradores)
    #    Se excluye explícitamente el sabor "limonada" del cálculo
    if not df_completo.empty and "Marcas" in df_completo.columns and "Descripcion" in df_completo.columns:
        marcas_norm = df_completo["Marcas"].astype(str).str.strip()
        desc_norm = df_completo["Descripcion"].astype(str).str.lower()
        
        # Filtrar solo productos de marca LEVITE con ventas positivas
        mask_levite = marcas_norm.str.contains(r"\bLEVITE\b", case=False, na=False)
        df_levite = df_completo[mask_levite & (df_completo.get("Kg_Lt", 0) > 0)].copy()
        
        if not df_levite.empty:
            # Denominador: compradores de LEVITE (con venta > 0)
            compradores_levite = df_levite["CodigoCliente"].nunique()
            print(f"DEBUG Sabores-PV Levite -> Compradores Levite: {compradores_levite}")

            # Numerador: sabores distintos por cliente (solo si se logró identificar el sabor)
            import re
            extraido = df_levite["Descripcion"].astype(str).str.lower().str.extract(r"levite\s+([a-záéíóúñ]+(?:\s+[a-záéíóúñ]+)?)")[0]
            df_levite["Sabor"] = extraido.fillna("").str.strip().str.title()
            
            # Filtrar sabores válidos (no vacíos y que no sean "limonada")
            df_levite = df_levite[
                (df_levite["Sabor"] != "") & 
                (~df_levite["Sabor"].str.contains(r"limonada", case=False, na=False))
            ]
            
            if not df_levite.empty:
                sabores_por_cliente = df_levite.groupby("CodigoCliente")["Sabor"].nunique()
                suma_sabores = sabores_por_cliente.sum()
                print(f"DEBUG Sabores-PV Levite -> Suma de sabores distintos entre clientes (excluyendo 'limonada'): {suma_sabores}")
                productos_por_cliente = (suma_sabores / compradores_levite) if compradores_levite > 0 else 0
                print(f"DEBUG Sabores-PV Levite -> Resultado KPI (suma_sabores/compradores): {productos_por_cliente}")
            else:
                print("DEBUG Sabores-PV Levite -> No se encontraron sabores válidos después de excluir 'limonada'")
                productos_por_cliente = 0
        else:
            print("DEBUG Sabores-PV Levite -> No hay datos válidos después de filtrar")
            productos_por_cliente = 0
    else:
        print("DEBUG Sabores-PV Levite -> No se pudo calcular: faltan columnas requeridas")
        productos_por_cliente = 0
    # 9. CCC Ñandú -> Clientes con compra de 2 o 3 marcas entre: Heineken, Miller, Imperial Golden
    import unicodedata
    def _sin_acentos(s):
        s = str(s) if pd.notna(s) else ""
        return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn').lower().strip()

    if {"Marcas", "Descripcion"}.issubset(df_completo.columns):
        marcas_norm = df_completo["Marcas"].apply(_sin_acentos)
        desc_norm = df_completo["Descripcion"].apply(_sin_acentos)

        # Crear máscara para calibre 330 (buscando "330" en la descripción)
        mask_calibre_330 = df_completo["Descripcion"].astype(str).str.contains(r"\b330\b", na=False)
        
        # Máscaras para cada marca de porrón
        mask_heineken = marcas_norm.str.contains("heineken", na=False)
        mask_miller = marcas_norm.str.contains("miller", na=False)
        mask_imperial_golden = marcas_norm.str.contains("imperial", na=False) & desc_norm.str.contains("golden", na=False)

        # Filtrar solo registros con calibre 330
        df_ccu = df_completo[mask_calibre_330 & (df_completo.get("Kg_Lt", 0) > 0)].copy()
        
        print(f"DEBUG CCC Ñandú -> Total registros con calibre 330: {len(df_ccu)}")

        # Etiquetar la marca del set objetivo
        import numpy as np
        # Asegurarse de que los índices coincidan
        mask_heineken = mask_heineken.reindex(df_ccu.index, fill_value=False)
        mask_miller = mask_miller.reindex(df_ccu.index, fill_value=False)
        mask_imperial_golden = mask_imperial_golden.reindex(df_ccu.index, fill_value=False)
        
        # Usar string vacío como valor por defecto en lugar de np.nan
        df_ccu["MarcaCCC"] = np.select(
            [mask_heineken, mask_miller, mask_imperial_golden],
            ["Heineken", "Miller", "Imperial Golden"],
            default=""
        )
        df_ccu = df_ccu.dropna(subset=["MarcaCCC"])  # seguridad

        # Primero filtramos clientes con Kg_Lt acumulado > 0
        clientes_con_kg_positivo = df_ccu.groupby("CodigoCliente")["Kg_Lt"].sum()
        clientes_con_kg_positivo = clientes_con_kg_positivo[clientes_con_kg_positivo > 0].index
        
        # Luego contamos marcas únicas solo para estos clientes
        marcas_por_cliente = df_ccu[df_ccu["CodigoCliente"].isin(clientes_con_kg_positivo)]
        marcas_por_cliente = marcas_por_cliente.groupby("CodigoCliente")["MarcaCCC"].nunique()
        
        # Finalmente contamos los que tienen 2 o más marcas
        ccc_nandu = (marcas_por_cliente > 1).sum()

        # Debug
        print(f"DEBUG CCC Ñandú -> Heineken rows: {mask_heineken.sum()}, Miller rows: {mask_miller.sum()}, Imperial Golden rows: {mask_imperial_golden.sum()}")
        print(f"DEBUG CCC Ñandú -> Clientes con 2+ marcas: {((marcas_por_cliente>=2)&(marcas_por_cliente<=3)).sum()}")
    else:
        ccc_nandu = 0

    # 10. Función del BRUTO -> DEL RANGO COMPLETO FILTRADO
    funcion_bruto = bruto

    # Crear el diccionario de resumen
    resumen_dict = {
        "HL (Litros Vendidos)": round(hl, 1),
        "HL Proyectado": round(hl_proyectado, 1),
        "HectoLitro Real (Acumulado)": round(hectolitro_real, 1),
        "% Bonificación": f"{porc_bonif:.1f}%",
        "CCE (Clientes con compra)": round(clientes_con_compra, 1)
    }
    
    # Agregar CCE Agua Pura si existe
    if 'cce_agua_pura' in locals():
        resumen_dict["CCE Agua Pura"] = round(cce_agua_pura, 1)
    
    # Agregar CCE Agua Saborizada si existe
    if 'cce_agua_saborizada' in locals():
        resumen_dict["CCE Agua Saborizada"] = round(cce_agua_saborizada, 1)
    
    # Continuar con el resto de las columnas
    resumen_dict.update({
        "Cartera": round(cartera_manual, 1),
        "Cobertura": f"{cobertura*100:.1f}%",
        "Drop (Bultos/Clientes)": round(drop, 1),
        "Sabores por PV (Levite)": productos_por_cliente,
        "CCC Ñandú (Multi-marca)": round(ccc_nandu, 1),
        "$ Bruto": round(bruto, 1),
        "$ Neto": round(neto, 1),
        "Diferencia Bruto - Neto": round(bruto - neto, 1),
        "Función del Bruto": round(funcion_bruto, 1)
    })
    
    # Crear el DataFrame del resumen
    resumen = pd.DataFrame([resumen_dict])

    return resumen

def prepare_yoy_data(df, date_to):
    """
    Prepara los datos para los gráficos de comparación interanual (YTD y mensual)
    para Volumen (HL) y CCC (Clientes con Compra).
    """
    if df.empty:
        return pd.DataFrame(), pd.DataFrame()

    # Asegurarse de que la fecha es datetime
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    
    # Extraer año y mes
    df['Año'] = df['Fecha'].dt.year
    df['Mes'] = df['Fecha'].dt.month

    # Tomar los años presentes en los datos
    available_years = sorted(df['Año'].unique())
    if not available_years:
        # No hay datos para procesar
        return pd.DataFrame(), pd.DataFrame()
    
    # Usar todos los años disponibles
    df_comp = df[df['Año'].isin(available_years)].copy()

    # Calcular el mes de referencia (el mes de 'date_to')
    ref_month = pd.to_datetime(date_to).month

    # --- Cálculos para el gráfico YTD (Volumen y CCC) ---
    # Filtrar datos hasta el mes de referencia para ambos años
    df_ytd = df_comp[df_comp['Mes'] <= ref_month].copy()

    # Agrupar por Año y Mes
    yoy_data = df_ytd.groupby(['Año', 'Mes']).agg(
        Volumen=('HL', 'sum'),
        CCC=('CodigoCliente', pd.Series.nunique)
    ).reset_index()

    # --- Cálculos para el desglose por Canal (YTD) ---
    channel_data = df_ytd.groupby(['Año', 'Canal']).agg(
        Volumen=('HL', 'sum'),
        CCC=('CodigoCliente', pd.Series.nunique)
    ).reset_index()

    return yoy_data, channel_data
