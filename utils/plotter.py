import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

def plot_yearly_totals(df, metric='Volumen', title_suffix=''):
    """
    Genera un gráfico de barras mostrando los totales anuales de una métrica.
    Muestra específicamente 2024 (azul) y 2025 (naranja) con sus totales.
    """
    if df.empty:
        return go.Figure()

    # Calcular el total por año, sumando todos los canales
    if 'Canal' in df.columns:
        # Agrupar solo por año para obtener el total
        yearly_totals = df.groupby('Año')[metric].sum().reset_index()
    else:
        # Si no hay columna 'Canal', usar los datos tal cual
        yearly_totals = df.groupby('Año')[metric].sum().reset_index()
    
    # Ordenar por año
    yearly_totals = yearly_totals.sort_values('Año')
    
    # Obtener todos los años únicos para mostrar en el gráfico
    years_in_data = yearly_totals['Año'].unique()
    
    # Crear el gráfico
    fig = go.Figure()
    
    # Colores fijos para 2024 (azul) y 2025 (naranja)
    colors = {
        2024: '#1f77b4',  # Azul
        2025: '#ff7f0e'   # Naranja
    }
    
    # Agregar una barra por año
    for _, row in yearly_totals.iterrows():
        year = int(row['Año'])
        color = colors.get(year, '#2ca02c')  # Verde por defecto si hay otros años
        
        fig.add_trace(go.Bar(
            x=[str(year)],
            y=[row[metric]],
            name=str(year),
            text=[f"{row[metric]:.1f}"],
            textposition='outside',
            texttemplate='%{text:.1f}',
            cliponaxis=False,
            marker_color=color,
            showlegend=False,
            width=0.5  # Hacer las barras un poco más delgadas
        ))
    
    title = f'Total Anual {metric} {title_suffix}'.strip()
    
    fig.update_layout(
        title=title,
        xaxis_title="Año",
        yaxis_title=metric,
        yaxis=dict(tickformat=".1f"),
        barmode='group',
        uniformtext_minsize=12,
        uniformtext_mode='hide',
        height=400,
        margin=dict(t=40, b=80, l=50, r=20, pad=10),
        plot_bgcolor='rgba(0,0,0,0)',  # Fondo transparente
        xaxis=dict(
            tickmode='array',
            tickvals=[str(y) for y in years_in_data],  # Mostrar todos los años disponibles
            ticktext=[str(int(y)) for y in years_in_data]  # Asegurar que se muestren como enteros
        )
    )
    
    return fig

def plot_yoy_comparison(df_yoy, metric='Volumen', period='YTD'):
    """
    Genera un gráfico de barras para comparar una métrica (Volumen o CCC) 
    entre el año actual y el anterior, para un período (YTD o Mes).
    """
    if df_yoy.empty:
        return go.Figure()

    title_text = f'{metric} Mensual - Año Actual vs. Anterior'

    fig = go.Figure()
    texttemplate = '%{text:.1f}'

    # Mapear número de mes -> nombre en español y fijar orden
    month_names = [
        'Enero','Febrero','Marzo','Abril','Mayo','Junio',
        'Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre'
    ]
    # Nombres presentes según los datos (en orden 1..12)
    meses_presentes = sorted(df_yoy['Mes'].unique())
    categorias_ordenadas = [month_names[m-1] for m in meses_presentes if 1 <= m <= 12]

    for year in df_yoy['Año'].unique():
        df_year = df_yoy[df_yoy['Año'] == year].copy()
        df_year['MesNombre'] = df_year['Mes'].apply(lambda m: month_names[m-1] if 1 <= m <= 12 else str(m))
        fig.add_trace(go.Bar(
            x=df_year['MesNombre'],
            y=df_year[metric],
            name=str(year),
            text=df_year[metric].round(1),
            textposition='outside',
            texttemplate=texttemplate,
            cliponaxis=False
        ))

    fig.update_layout(
        title=title_text,
        xaxis_title="Mes",
        xaxis=dict(categoryorder='array', categoryarray=categorias_ordenadas),
        yaxis_title=metric,
        yaxis=dict(tickformat=".1f"),
        barmode='group',
        legend_title="Año",
        uniformtext_minsize=8,
        uniformtext_mode='hide'
    )
    return fig


def plot_channel_breakdown(df_channel, metric='Volumen'):
    """
    Genera un gráfico de barras para mostrar el desglose por canal de una métrica.
    """
    if df_channel.empty:
        return go.Figure()

    title_text = f'Desglose de {metric} por Canal'
    
    fig = go.Figure()
    texttemplate = '%{text:.1f}'

    for year in df_channel['Año'].unique():
        df_year = df_channel[df_channel['Año'] == year]
        fig.add_trace(go.Bar(
            x=df_year['Canal'],
            y=df_year[metric],
            name=str(year),
            text=df_year[metric].round(1),
            textposition='outside',
            texttemplate=texttemplate,
            cliponaxis=False
        ))

    fig.update_layout(
        title=title_text,
        xaxis_title="Canal",
        yaxis_title=metric,
        yaxis=dict(tickformat=".1f"),
        barmode='group',
        legend_title="Año",
        uniformtext_minsize=8,
        uniformtext_mode='hide'
    )
    return fig


def plot_volume_mix(df_channel):
    """
    Gráfico comparativo del mix de volumen por canal:
    - Muestra los dos años más recientes disponibles (máximo 2 años)
    - Si solo hay un año: muestra una sola torta
    - Si hay dos o más años: muestra los dos más recientes
    GAP = (Actual / Anterior) - 1
    """
    if df_channel.empty:
        return go.Figure()

    # Obtener los dos años más recientes
    years_available = sorted(df_channel['Año'].unique(), reverse=True)
    
    # Tomar como máximo 2 años
    years_to_show = years_available[:2]
    
    # Si solo hay un año o menos
    if len(years_to_show) == 0:
        return go.Figure()
        
    current_year = years_to_show[0]
    df_curr = df_channel[df_channel['Año'] == current_year].copy()
    
    # Si solo hay un año, mostrar solo ese
    if len(years_to_show) == 1:
        if df_curr.empty:
            return go.Figure()
        fig = go.Figure(data=[go.Pie(
            labels=df_curr['Canal'],
            values=df_curr['Volumen'],
            hole=.3,
            textinfo='text',
            texttemplate='%{label}<br>%{value:.1f} (%{percent:.1%})',
            textposition='outside',
            automargin=True,
            insidetextorientation='radial',
            textfont=dict(size=11)
        )])
        fig.update_layout(
            title_text=f'Mix de Volumen por Canal ({current_year})',
            paper_bgcolor='gray', plot_bgcolor='white',
            width=900, height=500,
        )
        return fig
        
    # Si hay dos años, mostrar comparación
    prev_year = years_to_show[1]
    df_prev = df_channel[df_channel['Año'] == prev_year].copy()

    # Este bloque ya no es necesario ya que lo movimos arriba
    pass

    # Alinear canales entre años
    canales = sorted(set(df_curr['Canal']).union(set(df_prev['Canal'])))
    s_curr = df_curr.set_index('Canal')['Volumen'].reindex(canales).fillna(0.0)
    s_prev = df_prev.set_index('Canal')['Volumen'].reindex(canales).fillna(0.0)

    # Calcular GAP
    import numpy as np
    with np.errstate(divide='ignore', invalid='ignore'):
        gap = np.where(s_prev.values > 0, (s_curr.values / s_prev.values) - 1.0, np.nan)

    # Colores por GAP
    gap_colors = [('#2E7D32' if not np.isnan(g) and g >= 0 else ('#C62828' if not np.isnan(g) else '#757575')) for g in gap]

    # Crear subplots: Pie Anterior | Tabla GAP | Pie Actual
    fig = make_subplots(
        rows=1, cols=3,
        specs=[[{'type': 'domain'}, {'type': 'table'}, {'type': 'domain'}]],
        column_widths=[0.38, 0.24, 0.38],
        subplot_titles=(f"{prev_year}", "GAP por Canal", f"{current_year}")
    )

    # Pie año anterior
    fig.add_trace(go.Pie(
        labels=canales,
        values=s_prev.values,
        hole=.3,
        textinfo='text',
        texttemplate='%{label}<br>%{value:.1f} (%{percent:.1%})',
        textposition='outside',
        automargin=True,
        insidetextorientation='radial',
        textfont=dict(size=11)
    ), row=1, col=1)

    # Tabla central con GAP
    gap_pct = [f"{g*100:.1f}%" if not np.isnan(g) else 's/d' for g in gap]
    curr_vals = [f"{v:.1f}" for v in s_curr.values]
    prev_vals = [f"{v:.1f}" for v in s_prev.values]
    fig.add_trace(go.Table(
        columnorder=[1, 2, 3, 4],
        columnwidth=[110, 90, 90, 80],
        header=dict(
            values=["Canal", "Actual", "Anterior", "GAP"],
            fill_color="#2b2b2b",
            align=['left', 'right', 'right', 'right'],
            font=dict(color='white', size=12),
            line_color="#3a3a3a"
        ),
        cells=dict(
            values=[canales, curr_vals, prev_vals, gap_pct],
            align=['left', 'right', 'right', 'right'],
            fill_color="#1e1e1e",
            font=dict(color=['white', 'white', 'white', gap_colors], size=11),
            height=24,
            line_color="#3a3a3a"
        )
    ), row=1, col=2)

    # Pie año actual
    fig.add_trace(go.Pie(
        labels=canales,
        values=s_curr.values,
        hole=.3,
        textinfo='text',
        texttemplate='%{label}<br>%{value:.1f} (%{percent:.1%})',
        textposition='outside',
        automargin=True,
        insidetextorientation='radial',
        textfont=dict(size=11)
    ), row=1, col=3)

    fig.update_layout(
        title_text=f"Mix de Volumen por Canal - Comparativo {prev_year} vs {current_year}",
        paper_bgcolor='#0f0f0f',
        plot_bgcolor='#0f0f0f',
        width=1200,
        height=550,
        margin=dict(l=40, r=40, t=60, b=40),
        legend=dict(orientation='v', x=1.02, y=0.5, font=dict(size=11, color='white')),
        font=dict(color='white')
    )
    return fig
