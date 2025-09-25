import streamlit as st
import pandas as pd
from datetime import datetime
from utils.data_loader import load_multiple_excels
from utils.processor import process_data, build_global_summary, prepare_yoy_data
from utils.plotter import plot_yoy_comparison, plot_channel_breakdown, plot_volume_mix, plot_yearly_totals
from utils.exporter import export_to_excel, export_clientes_y_sabores
from utils.license_manager import LicenseManager

st.set_page_config(page_title="📊 Dashboard CCU", layout="wide")

# ===== VERIFICACIÓN DE LICENCIA =====
license_manager = LicenseManager()
if not license_manager.require_valid_license():
    st.stop()

st.title("📊 Dashboard CCU - Consolidado Global")

uploaded_files = st.file_uploader("📁 Subí archivos Excel:", type=["xls", "xlsx", "xlsb"], accept_multiple_files=True)

# Filtros de fecha
col1, col2 = st.columns(2)
with col1:
    date_from = st.date_input("📅 Desde:", value=datetime(2024, 1, 1))
with col2:
    date_to = st.date_input("📅 Hasta:", value=datetime.today())

# Parámetros manuales
st.markdown("### ✍️ Parámetros de proyección")
col1, col2, col3 = st.columns(3)
with col1:
    salidas_mes = st.number_input("📆 Salidas del mes", min_value=1, value=20)
with col2:
    salidas_actuales = st.number_input("📆 Salidas hasta hoy", min_value=1, value=10)
with col3:
    cartera_manual = st.number_input("👥 Cartera", min_value=0, value=1000)

if uploaded_files:
    df, planes_data = load_multiple_excels(uploaded_files)

    # Excluir las familias 'POP' y 'PALLETS' de todos los análisis
    if 'Grupo' in df.columns:
        familias_a_excluir = ['POP', 'PALLETS']
        df = df[~df['Grupo'].isin(familias_a_excluir)].copy()

    st.subheader("🔍 Vista previa datos crudos")
    st.dataframe(df.head(10))

    df = process_data(df, date_from, date_to)

    # 🔧 Filtros dinámicos
    st.markdown("### 🔎 Filtros de análisis")

    # --- Lógica de Filtros ---
    df_para_filtros = df.copy()
    filtros_activos = []

    col1, col2, col3 = st.columns(3)

    with col1:
        familia_options = sorted(df_para_filtros['Grupo'].dropna().unique())
        familia = st.multiselect("Familia", familia_options)
        if familia:
            df_para_filtros = df_para_filtros[df_para_filtros["Grupo"].isin(familia)]
            filtros_activos.append('familia')

        canal_options = sorted(df_para_filtros['Canal'].dropna().unique())
        canal = st.multiselect("Canal", canal_options)
        if canal:
            df_para_filtros = df_para_filtros[df_para_filtros["Canal"].isin(canal)]
            filtros_activos.append('canal')

    with col2:
        marca_options = sorted(df_para_filtros['Marcas'].dropna().unique())
        marca = st.multiselect("Marca", marca_options)
        if marca:
            df_para_filtros = df_para_filtros[df_para_filtros["Marcas"].isin(marca)]
            filtros_activos.append('marca')

        supervisor_options = sorted(df_para_filtros['NomSupervisor'].dropna().unique())
        supervisor = st.multiselect("Supervisor", supervisor_options)
        if supervisor:
            df_para_filtros = df_para_filtros[df_para_filtros["NomSupervisor"].isin(supervisor)]
            filtros_activos.append('supervisor')

    with col3:
        # Lógica híbrida para Calibre, usando la columna pre-procesada 'Calibre_CC'
        source_df_calibre = df_para_filtros if filtros_activos else df
        calibre_series = source_df_calibre['Calibre_CC'].dropna()
        calibre_options = sorted(calibre_series.unique().astype(int))
        calibre_options = [str(c) for c in calibre_options]

        calibre_seleccionado = st.multiselect("Calibre", calibre_options)
        if calibre_seleccionado:
            # Mantener las opciones visuales basadas en 'Calibre_CC', pero filtrar por presencia del número en 'Descripcion'
            import re
            calibres_a_filtrar = [int(c) for c in calibre_seleccionado]
            mask = False
            for c in calibres_a_filtrar:
                # Coincidencia del número como token (evitar que 100 matchee 1000)
                pattern = rf"(?<!\d){re.escape(str(c))}(?!\d)"
                m = df_para_filtros['Descripcion'].astype(str).str.contains(pattern, case=False, regex=True, na=False)
                mask = m if isinstance(mask, bool) and mask is False else (mask | m)
            df_para_filtros = df_para_filtros[mask]

        vendedor_options = sorted(df_para_filtros['NomVendedor'].dropna().unique())
        vendedor = st.multiselect("Vendedor", vendedor_options)
        if vendedor:
            df_para_filtros = df_para_filtros[df_para_filtros["NomVendedor"].isin(vendedor)]

    cliente_options = sorted(df_para_filtros['RazonSocial'].dropna().unique())
    cliente = st.multiselect("Cliente", cliente_options)
    if cliente:
        df_para_filtros = df_para_filtros[df_para_filtros["RazonSocial"].isin(cliente)]

    # Filtro de Plan (solo si se cargó archivo PLANES)
    if planes_data:
        st.markdown("#### 📋 Filtro por Plan")
        plan_options = sorted(planes_data.keys())
        plan_seleccionado = st.selectbox(
            "Seleccionar Plan (filtro por códigos de clientes del plan)",
            ["Todos los planes"] + plan_options,
            help="Si seleccionas un plan específico, solo se mostrarán los datos de los clientes que pertenecen a ese plan"
        )
        
        if plan_seleccionado != "Todos los planes":
            # Filtrar por códigos de clientes del plan seleccionado
            codigos_plan = planes_data[plan_seleccionado]
            # Convertir CodigoCliente a string para la comparación
            df_para_filtros_plan = df_para_filtros[
                df_para_filtros["CodigoCliente"].astype(str).isin(codigos_plan)
            ].copy()
            
            # Mostrar información del filtro aplicado
            st.info(f"📋 Plan aplicado: {plan_seleccionado} ({len(codigos_plan)} clientes en el plan)")
            if len(df_para_filtros_plan) > 0:
                clientes_encontrados = df_para_filtros_plan["CodigoCliente"].nunique()
                st.success(f"✅ Se encontraron {clientes_encontrados} clientes del plan con datos en el período seleccionado")
            else:
                st.warning("⚠️ No se encontraron datos para los clientes de este plan en el período seleccionado")
            
            df_para_filtros = df_para_filtros_plan

    df_filtrado = df_para_filtros.copy()

    st.subheader("📊 Resumen consolidado del último mes")
    resumen = build_global_summary(df_filtrado, date_to, salidas_mes, salidas_actuales, cartera_manual)
    st.dataframe(resumen)

    st.markdown("<h3 style='text-align: center;'> Indicadores clave</h3>", unsafe_allow_html=True)

    # Primera fila - Métricas de volumen
    col1, col2, col3 = st.columns(3)
    col1.metric("HL (Litros Vendidos)", f"{resumen['HL (Litros Vendidos)'].iloc[0]:.1f}")
    col2.metric("HL Proyectado", f"{resumen['HL Proyectado'].iloc[0]:.1f}")
    col3.metric("HectoLitro Real", f"{resumen['HectoLitro Real (Acumulado)'].iloc[0]:.1f}")

    # Segunda fila - Métricas financieras
    col4, col5, col6 = st.columns(3)
    col4.metric("% Bonificación", resumen['% Bonificación'].iloc[0])
    col5.metric("$ Bruto", f"${resumen['$ Bruto'].iloc[0]:.1f}")
    col6.metric("$ Neto", f"${resumen['$ Neto'].iloc[0]:.1f}")

    # Tercera fila - Métricas de clientes
    col7, col8, col9 = st.columns(3)
    col7.metric("CCE (Clientes)", f"{resumen['CCE (Clientes con compra)'].iloc[0]:.1f}")
    col8.metric("Cobertura", resumen['Cobertura'].iloc[0])
    col9.metric("CCC Ñandú", f"{resumen['CCC Ñandú (Multi-marca)'].iloc[0]:.1f}")
    
    # Cuarta fila - Métricas de CCE por tipo de agua
    col10, col11, col12 = st.columns(3)
    if 'CCE Agua Pura' in resumen.columns:
        col10.metric("CCE Agua Pura", f"{resumen['CCE Agua Pura'].iloc[0]:.1f}")
    if 'CCE Agua Saborizada' in resumen.columns:
        col11.metric("CCE Agua Saborizada", f"{resumen['CCE Agua Saborizada'].iloc[0]:.1f}")
    col12.metric(
        "Sabores por PV (Levite)",
        f"{resumen['Sabores por PV (Levite)'].iloc[0]:.2f}"
    )
    # Quinta fila - Otras métricas de productos
    col13, col14, col15 = st.columns(3)
    col13.metric("Drop (Bultos/Clientes)", f"{resumen['Drop (Bultos/Clientes)'].iloc[0]:.1f}")
    col14.metric("Dif Bruto - Neto", f"${resumen['Diferencia Bruto - Neto'].iloc[0]:.1f}")
    
    # Sexta fila - Métricas adicionales
    col15.metric("Cartera", f"{resumen['Cartera'].iloc[0]:.1f}")

    # ===== NUEVO BOTÓN DE EXPORTACIÓN CCC ÑANDÚ Y PV LEVITE =====
    st.markdown("---")
    st.markdown("### 📋 Exportar Información Detallada de Indicadores")
    
    if st.button("📊 Exportar CCC Ñandú y PV LEVITE", 
                help="Descargar un archivo Excel con el detalle de clientes que conforman los indicadores CCC Ñandú y PV Levite"):
        try:
            # Llamar a la función de exportación con los datos ya procesados
            excel_data, filename = export_clientes_y_sabores(df_filtrado)
            
            # Crear el botón de descarga
            st.download_button(
                label="⬇️ Descargar archivo Excel",
                data=excel_data,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            st.success("✅ Archivo generado correctamente. Haz clic en el botón de descarga.")
        except Exception as e:
            st.error(f"❌ Error al generar el archivo: {str(e)}")
    
    st.markdown("---")
    st.markdown("<h3 style='text-align: center;'> Gráficos de Comparación Anual</h3>", unsafe_allow_html=True)

    # Preparar datos para los gráficos
    yoy_data, channel_data = prepare_yoy_data(df_filtrado, date_to)
    figuras_export = []

    if not yoy_data.empty and not channel_data.empty:
        # Fila 1: Gráficos de Volumen - Mensual vs Anual
        st.write("#### Comparación de Volumen")
        col1, col2 = st.columns(2)
        with col1:
            fig_volumen_yoy = plot_yoy_comparison(yoy_data, metric='Volumen', period='YTD')
            st.plotly_chart(fig_volumen_yoy, use_container_width=True)
            figuras_export.append(fig_volumen_yoy)
        with col2:
            fig_volumen_anual = plot_yearly_totals(yoy_data, metric='Volumen', title_suffix='(YTD)')
            st.plotly_chart(fig_volumen_anual, use_container_width=True)
            figuras_export.append(fig_volumen_anual)

        # Fila 2: Gráficos de CCC - Mensual vs Anual
        st.write("#### Comparación de CCC (YTD)")
        col1, col2 = st.columns(2)
        with col1:
            fig_ccc_yoy = plot_yoy_comparison(yoy_data, metric='CCC', period='YTD')
            st.plotly_chart(fig_ccc_yoy, use_container_width=True)
            figuras_export.append(fig_ccc_yoy)
        with col2:
            fig_ccc_anual = plot_yearly_totals(yoy_data, metric='CCC', title_suffix='(YTD)')
            st.plotly_chart(fig_ccc_anual, use_container_width=True)
            figuras_export.append(fig_ccc_anual)

        # Fila 3: Gráficos por Canal - Volumen
        st.write("#### Desglose por Canal - Volumen (YTD)")
        col1, col2 = st.columns(2)
        with col1:
            fig_volumen_canal = plot_channel_breakdown(channel_data, metric='Volumen')
            st.plotly_chart(fig_volumen_canal, use_container_width=True)
            figuras_export.append(fig_volumen_canal)
        with col2:
            # Crear un DataFrame con los totales por canal y año para el gráfico de barras
            channel_totals = channel_data.groupby(['Canal', 'Año'])['Volumen'].sum().reset_index()
            fig_volumen_canal_anual = plot_yearly_totals(channel_totals, metric='Volumen', title_suffix='por Canal (YTD)')
            st.plotly_chart(fig_volumen_canal_anual, use_container_width=True)
            figuras_export.append(fig_volumen_canal_anual)

        # Fila 4: Gráficos por Canal - CCC
        st.write("#### Desglose por Canal - CCC (YTD)")
        col1, col2 = st.columns(2)
        with col1:
            fig_ccc_canal = plot_channel_breakdown(channel_data, metric='CCC')
            st.plotly_chart(fig_ccc_canal, use_container_width=True)
            figuras_export.append(fig_ccc_canal)
        with col2:
            # Crear un DataFrame con los totales por canal y año para el gráfico de barras
            ccc_totals = channel_data.groupby(['Canal', 'Año'])['CCC'].sum().reset_index()
            fig_ccc_canal_anual = plot_yearly_totals(ccc_totals, metric='CCC', title_suffix='por Canal (YTD)')
            st.plotly_chart(fig_ccc_canal_anual, use_container_width=True)
            figuras_export.append(fig_ccc_canal_anual)

        # Fila 5: Mix de Volumen (se mantiene igual)
        st.write("#### Mix de Volumen por Canal (YTD Año Actual)")
        fig_mix_volumen = plot_volume_mix(channel_data)
        st.plotly_chart(fig_mix_volumen, use_container_width=True)
        figuras_export.append(fig_mix_volumen)




    st.download_button(
        "📥 Exportar Excel",
        data=export_to_excel(resumen, figuras=figuras_export),
        file_name="resumen_ventas.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("⬆️ Por favor, cargá al menos un archivo Excel.")