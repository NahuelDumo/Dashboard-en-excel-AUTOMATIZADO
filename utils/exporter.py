import pandas as pd
from io import BytesIO
import plotly.graph_objects as go
import plotly.express as px

def export_to_excel(resumen_global_df, figuras=None):
    """
    Exporta:
    - Hoja 'Resumen Global' con los indicadores (incluye todos los KPIs)
    - Hoja 'Graficos' con capturas PNG de figuras Plotly (si se proveen)
    """
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        # Hoja de indicadores
        resumen_global_df.to_excel(writer, index=False, sheet_name="Resumen Global")

        # Hoja de gráficos (opcional)
        if figuras:
            workbook = writer.book
            ws = workbook.add_worksheet("Graficos")

            # Insertar imágenes, una por fila, grandes
            row, col = 1, 1  # usando base 0 -> esto es fila 2, col B para dejar margen
            row_step = 35     # separación de filas entre imágenes (más alto para gráficos grandes)

            for i, fig in enumerate(figuras, start=1):
                try:
                    # Exportar respetando el Figure original (tema, colores y tamaños)
                    fig_export = go.Figure(fig)
                    # Si no hay template explícito, usar uno colorido por defecto para evitar barras negras
                    if fig_export.layout.template is None:
                        fig_export.update_layout(template="plotly")
                    # Si no hay colorway, asignar una cualitativa por defecto
                    if not getattr(fig_export.layout, 'colorway', None):
                        fig_export.update_layout(colorway=px.colors.qualitative.Plotly)
                    # Usar dimensiones del layout si existen
                    export_width = getattr(fig_export.layout, 'width', None) or 1400
                    export_height = getattr(fig_export.layout, 'height', None) or 700
                    fig_export.update_layout(width=export_width, height=export_height)
                    img_bytes = fig_export.to_image(format="png", scale=3, engine="kaleido")
                    img_io = BytesIO(img_bytes)
                    ws.insert_image(row, col, f"grafico_{i}.png", {
                        'image_data': img_io,
                        'x_scale': 1.6,
                        'y_scale': 1.6
                    })
                    # Siguiente imagen en una nueva fila
                    row += row_step
                    col = 1
                except Exception as e:
                    # Si falla la exportación de una figura, continuamos con las demás
                    ws.write(row, col, f"Error exportando figura {i}: {e}")
                    row += row_step
                    col = 1
    output.seek(0)
    return output
def export_clientes_y_sabores(df_filtrado):
    """
    Exporta información detallada de:
    - CCC Ñandú: Clientes que compraron 2+ marcas (Heineken, Miller, Imperial Golden) calibre 330
    - PV Levite: Clientes y cantidad de sabores distintos que compraron (excluyendo limonada)
    
    Reutiliza la misma lógica que ya está implementada en build_global_summary()
    """
    from datetime import datetime
    import unicodedata
    import numpy as np
    import re
    
    output = BytesIO()
    
    def _sin_acentos(s):
        s = str(s) if pd.notna(s) else ""
        return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn').lower().strip()
    
    # =============================================================================
    # ANÁLISIS CCC ÑANDÚ - MISMA LÓGICA QUE EN build_global_summary
    # =============================================================================
    ccc_nandu_df = pd.DataFrame()
    
    if {"Marcas", "Descripcion"}.issubset(df_filtrado.columns):
        marcas_norm = df_filtrado["Marcas"].apply(_sin_acentos)
        desc_norm = df_filtrado["Descripcion"].apply(_sin_acentos)

        # Crear máscara para calibre 330 (buscando "330" en la descripción)
        mask_calibre_330 = df_filtrado["Descripcion"].astype(str).str.contains(r"\b330\b", na=False)
        
        # Máscaras para cada marca de porrón
        mask_heineken = marcas_norm.str.contains("heineken", na=False)
        mask_miller = marcas_norm.str.contains("miller", na=False)
        mask_imperial_golden = marcas_norm.str.contains("imperial", na=False) & desc_norm.str.contains("golden", na=False)

        # Filtrar solo registros con calibre 330
        df_ccu = df_filtrado[mask_calibre_330 & (df_filtrado.get("Kg_Lt", 0) > 0)].copy()
        
        if not df_ccu.empty:
            # Reindexar las máscaras para que coincidan con df_ccu
            mask_heineken = mask_heineken.reindex(df_ccu.index, fill_value=False)
            mask_miller = mask_miller.reindex(df_ccu.index, fill_value=False)
            mask_imperial_golden = mask_imperial_golden.reindex(df_ccu.index, fill_value=False)
            
            # Etiquetar la marca del set objetivo
            df_ccu["MarcaCCC"] = np.select(
                [mask_heineken, mask_miller, mask_imperial_golden],
                ["Heineken", "Miller", "Imperial Golden"],
                default=""
            )
            df_ccu = df_ccu.dropna(subset=["MarcaCCC"])

            # Primero filtramos clientes con Kg_Lt acumulado > 0
            clientes_con_kg_positivo = df_ccu.groupby("CodigoCliente")["Kg_Lt"].sum()
            clientes_con_kg_positivo = clientes_con_kg_positivo[clientes_con_kg_positivo > 0].index
            
            # Luego contamos marcas únicas solo para estos clientes
            marcas_por_cliente = df_ccu[df_ccu["CodigoCliente"].isin(clientes_con_kg_positivo)]
            marcas_por_cliente_count = marcas_por_cliente.groupby("CodigoCliente")["MarcaCCC"].nunique()
            
            # Clientes con 2+ marcas
            clientes_ccc = marcas_por_cliente_count[marcas_por_cliente_count > 1].index
            
            if len(clientes_ccc) > 0:
                # Obtener información completa de estos clientes
                clientes_info = df_ccu[df_ccu["CodigoCliente"].isin(clientes_ccc)].copy()
                
                # Agrupar para obtener datos por cliente
                ccc_nandu_df = clientes_info.groupby(['CodigoCliente', 'RazonSocial']).agg({
                    'MarcaCCC': lambda x: len(x.unique()),  # Cantidad de marcas distintas
                    'Kg_Lt': 'sum'  # Total kg/lt
                }).reset_index()
                
                # Obtener detalle de marcas por cliente
                detalle_marcas = clientes_info.groupby(['CodigoCliente', 'RazonSocial'])['MarcaCCC'].apply(
                    lambda x: ', '.join(sorted(x.unique()))
                ).reset_index()
                
                # Combinar
                ccc_nandu_df = ccc_nandu_df.merge(detalle_marcas, on=['CodigoCliente', 'RazonSocial'], how='left', suffixes=('', '_detalle'))
                
                # Renombrar columnas
                ccc_nandu_df = ccc_nandu_df.rename(columns={
                    'CodigoCliente': 'Código Cliente',
                    'RazonSocial': 'Razón Social', 
                    'MarcaCCC': 'Cantidad Marcas',
                    'MarcaCCC_detalle': 'Marcas Compradas',
                    'Kg_Lt': 'Total Kg/Lt'
                })

    # =============================================================================
    # ANÁLISIS PV LEVITE - MISMA LÓGICA QUE EN build_global_summary
    # =============================================================================
    pv_levite_df = pd.DataFrame()
    
    if not df_filtrado.empty and "Marcas" in df_filtrado.columns and "Descripcion" in df_filtrado.columns:
        marcas_norm = df_filtrado["Marcas"].astype(str).str.strip()
        
        # Filtrar solo productos de marca LEVITE con ventas positivas
        mask_levite = marcas_norm.str.contains(r"\bLEVITE\b", case=False, na=False)
        df_levite = df_filtrado[mask_levite & (df_filtrado.get("Kg_Lt", 0) > 0)].copy()
        
        if not df_levite.empty:
            # Extraer sabores (MISMA LÓGICA que build_global_summary)
            extraido = df_levite["Descripcion"].astype(str).str.lower().str.extract(r"levite\s+([a-záéíóúñ]+(?:\s+[a-záéíóúñ]+)?)")[0]
            df_levite["Sabor"] = extraido.fillna("").str.strip().str.title()
            
            # Filtrar sabores válidos (no vacíos y que no sean "limonada")
            df_levite_valido = df_levite[
                (df_levite["Sabor"] != "") & 
                (~df_levite["Sabor"].str.contains(r"limonada", case=False, na=False))
            ].copy()
            
            if not df_levite_valido.empty:
                # Sabores por cliente (igual que en build_global_summary)
                sabores_por_cliente = df_levite_valido.groupby("CodigoCliente")["Sabor"].nunique()
                
                # Solo clientes con sabores > 0
                clientes_con_sabores = sabores_por_cliente[sabores_por_cliente > 0]
                
                if len(clientes_con_sabores) > 0:
                    # Obtener información completa de estos clientes
                    clientes_levite = df_levite_valido[df_levite_valido["CodigoCliente"].isin(clientes_con_sabores.index)].copy()
                    
                    # Agrupar información por cliente
                    pv_levite_df = clientes_levite.groupby(['CodigoCliente', 'RazonSocial']).agg({
                        'Sabor': 'nunique',  # Cantidad de sabores distintos
                        'Kg_Lt': 'sum'  # Total kg/lt
                    }).reset_index()
                    
                    # Obtener lista de sabores por cliente
                    detalle_sabores = clientes_levite.groupby(['CodigoCliente', 'RazonSocial'])['Sabor'].apply(
                        lambda x: ', '.join(sorted(x.unique()))
                    ).reset_index()
                    
                    # Combinar
                    pv_levite_df = pv_levite_df.merge(detalle_sabores, on=['CodigoCliente', 'RazonSocial'], how='left', suffixes=('', '_detalle'))
                    
                    # Renombrar columnas
                    pv_levite_df = pv_levite_df.rename(columns={
                        'CodigoCliente': 'Código Cliente',
                        'RazonSocial': 'Razón Social',
                        'Sabor': 'Cantidad Sabores',
                        'Sabor_detalle': 'Sabores Comprados', 
                        'Kg_Lt': 'Total Kg/Lt'
                    })

    # =============================================================================
    # EXPORTAR A EXCEL
    # =============================================================================
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        # Hoja CCC Ñandú
        if not ccc_nandu_df.empty:
            ccc_nandu_df.to_excel(writer, index=False, sheet_name="CCC Ñandú")
            worksheet1 = writer.sheets["CCC Ñandú"]
            worksheet1.set_column('A:A', 15)  # Código Cliente
            worksheet1.set_column('B:B', 40)  # Razón Social
            worksheet1.set_column('C:C', 15)  # Cantidad Marcas
            worksheet1.set_column('D:D', 30)  # Marcas Compradas
            worksheet1.set_column('E:E', 15)  # Total Kg/Lt
        else:
            pd.DataFrame(columns=['Código Cliente', 'Razón Social', 'Cantidad Marcas', 'Marcas Compradas', 'Total Kg/Lt']).to_excel(
                writer, index=False, sheet_name="CCC Ñandú"
            )
        
        # Hoja PV Levite
        if not pv_levite_df.empty:
            pv_levite_df.to_excel(writer, index=False, sheet_name="PV Levite")
            worksheet2 = writer.sheets["PV Levite"]
            worksheet2.set_column('A:A', 15)  # Código Cliente
            worksheet2.set_column('B:B', 40)  # Razón Social
            worksheet2.set_column('C:C', 18)  # Cantidad Sabores
            worksheet2.set_column('D:D', 40)  # Sabores Comprados
            worksheet2.set_column('E:E', 15)  # Total Kg/Lt
        else:
            pd.DataFrame(columns=['Código Cliente', 'Razón Social', 'Cantidad Sabores', 'Sabores Comprados', 'Total Kg/Lt']).to_excel(
                writer, index=False, sheet_name="PV Levite"
            )
        
        # Hoja resumen
        resumen_data = {
            'Indicador': ['CCC Ñandú', 'PV Levite'],
            'Descripción': [
                'Clientes que compraron 2+ marcas entre Heineken, Miller, Imperial Golden (calibre 330)',
                'Clientes que compraron sabores Levite (excluyendo limonada)'
            ],
            'Total Clientes': [len(ccc_nandu_df), len(pv_levite_df)]
        }
        pd.DataFrame(resumen_data).to_excel(writer, index=False, sheet_name="Resumen")
        worksheet3 = writer.sheets["Resumen"]
        worksheet3.set_column('A:A', 15)
        worksheet3.set_column('B:B', 60)
        worksheet3.set_column('C:C', 15)
    
    output.seek(0)
    
    # Generar nombre de archivo con timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"CCC_Nandu_PV_Levite_{timestamp}.xlsx"
    
    return output.getvalue(), filename