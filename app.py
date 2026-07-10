import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuración de la página e Identidad Visual (Tipografía Sans-Serif)
st.set_page_config(page_title="Dashboard de Tickets - Atom", layout="wide", initial_sidebar_state="expanded")

# Estilos CSS institucionales de Atom
st.markdown("""
    <style>
    html, body, [data-testid="stSidebar"] {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    h1, h2, h3 {
        color: #0B1F33 !important;
    }
    .stMetric {
        background-color: #F5F7FA;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #D9E1E8;
    }
    </style>
    """, unsafe_with_html=True)

# 2. Barra lateral con Identidad Visual
st.sidebar.markdown("<h2 style='color: #0B1F33; margin-top: 0;'>🤖 Atom Soporte</h2>", unsafe_with_html=True)

st.sidebar.header("📁 Carga de Datos")
uploaded_file = st.sidebar.file_uploader("Sube el archivo de tickets aquí (.xlsx o .csv)", type=["xlsx", "csv"])

# Título Principal con Línea de Marca (Naranja Atom) siempre visible
st.markdown("<h1 style='color: #0B1F33; margin-bottom: 0;'>📊 Dashboard de Estatus de Tickets</h1>", unsafe_with_html=True)
st.markdown("<hr style='border: 2px solid #FF6A1A; margin-top: 5px; margin-bottom: 25px;'>", unsafe_with_html=True)

# TODO el procesamiento visual solo ocurre SI el usuario ya cargó un archivo
if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
            
        df['Assigned Date'] = pd.to_datetime(df['Assigned Date'], errors='coerce')
        df['Close Date'] = pd.to_datetime(df['Close Date'], errors='coerce')
        
        st.sidebar.header("🔍 Filtros Dinámicos")
        
        # Filtro 1: Record (Empresa)
        empresas_disponibles = sorted(df['record'].dropna().unique().tolist())
        selected_records = st.sidebar.multiselect("Filtrar por Empresa (record):", empresas_disponibles, default=empresas_disponibles)
        
        # Filtro 2: Assigned Date (Rango de Fechas)
        min_date = df['Assigned Date'].min()
        max_date = df['Assigned Date'].max()
        
        if pd.notnull(min_date) and pd.notnull(max_date):
            date_range = st.sidebar.date_input("Filtrar por Fecha de Asignación:", [min_date.date(), max_date.date()])
        else:
            date_range = None

        df_filtered = df[df['record'].isin(selected_records)]
        if date_range and len(date_range) == 2:
            start_date, end_date = date_range
            df_filtered = df_filtered[(df_filtered['Assigned Date'].dt.date >= start_date) & (df_filtered['Assigned Date'].dt.date <= end_date)]

        # KPIs Principales
        total_t = len(df_filtered)
        abiertos = len(df_filtered[df_filtered['Conversation Status'].str.lower() == 'open']) if 'Conversation Status' in df_filtered.columns else 0
        cerrados = len(df_filtered[df_filtered['Conversation Status'].str.lower() == 'closed']) if 'Conversation Status' in df_filtered.columns else 0
        
        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.metric("Total Tickets Filtrados", f"{total_t:,}")
        kpi2.metric("🔴 Tickets Abiertos", f"{abiertos:,}")
        kpi3.metric("🟢 Tickets Cerrados", f"{cerrados:,}")
        st.write("")

        # 📅 Línea de tiempo con números visibles en cada punto
        st.subheader("📅 Línea de Tiempo de Tickets Creados")
        view_time = st.radio("Ver agrupación por:", ["Día", "Semana", "Mes"], horizontal=True)
        
        df_time = df_filtered.dropna(subset=['Assigned Date']).copy()
        if view_time == "Día":
            df_time['Periodo'] = df_time['Assigned Date'].dt.to_period('D').astype(str)
        elif view_time == "Semana":
            df_time['Periodo'] = df_time['Assigned Date'].dt.to_period('W').astype(str)
        else:
            df_time['Periodo'] = df_time['Assigned Date'].dt.to_period('M').astype(str)
            
        df_time_grouped = df_time.groupby('Periodo').size().reset_index(name='Cantidad de Tickets')
        
        fig_time = px.line(df_time_grouped, x='Periodo', y='Cantidad de Tickets', markers=True, text='Cantidad de Tickets',
                           color_discrete_sequence=["#FF6A1A"])
        fig_time.update_traces(textposition="top center")
        fig_time.update_layout(xaxis_title="Período", yaxis_title="Tickets")
        st.plotly_chart(fig_time, use_container_width=True)
        st.write("")

        col1, col2 = st.columns(2)

        with col1:
            # 🍩 Gráfica de Rueda limpia sin textos redundantes en el hover
            st.subheader("🍩 Categorías de Conversación")
            if 'Categoría de Conversación' in df_filtered.columns and df_filtered['Categoría de Conversación'].notnull().any():
                df_pie = df_filtered.copy()
                df_pie['Categoría de Conversación'] = df_pie['Categoría de Conversación'].fillna('Sin Categoría')
                
                fig_cat = px.pie(df_pie, names='Categoría de Conversación', hole=0.4, 
                                 color_discrete_sequence=["#0B1F33", "#FF6A1A", "#0F9B8E", "#5E6B78", "#D9E1E8"])
                
                fig_cat.update_traces(hovertemplate="<b>%{label}</b><br>Tickets: %{value}<br>Porcentaje: %{percent}")
                st.plotly_chart(fig_cat, use_container_width=True)
            else:
                st.info("No hay suficientes datos en 'Categoría de Conversación'")

        with col2:
            st.subheader("👤 Clientes con Más Consultas (Top 10)")
            if 'Contact Name' in df_filtered.columns and df_filtered['Contact Name'].notnull().any():
                df_contact = df_filtered['Contact Name'].value_counts().reset_index()
                df_contact.columns = ['Nombre de Contacto', 'Tickets']
                fig_contact = px.bar(df_contact.head(10), x='Tickets', y='Nombre de Contacto', orientation='h', 
                                     color_discrete_sequence=["#0B1F33"])
                fig_contact.update_layout(yaxis={'categoryorder':'total ascending'}, xaxis_title="Cantidad de Tickets", yaxis_title="Contacto")
                st.plotly_chart(fig_contact, use_container_width=True)
            else:
                st.info("No hay suficientes datos en 'Contact Name'")

        st.write("")
        col3, col4 = st.columns(2)

        with col3:
            st.subheader("⚙️ Módulos Afectados")
            if 'Módulo Afectado' in df_filtered.columns and df_filtered['Módulo Afectado'].notnull().any():
                df_modulo = df_filtered['Módulo Afectado'].value_counts().reset_index()
                df_modulo.columns = ['Módulo', 'Cantidad']
                fig_modulo = px.bar(df_modulo, x='Módulo', y='Cantidad', color_discrete_sequence=["#0F9B8E"])
                fig_modulo.update_layout(xaxis_title="Módulos", yaxis_title="Cantidad de Fallos")
                st.plotly_chart(fig_modulo, use_container_width=True)
            else:
                st.info("No hay suficientes datos en 'Módulo Afectado'")

        with col4:
            st.subheader("⏳ Análisis de Tiempo de Cierre")
            if 'Tiempo de cierre' in df_filtered.columns and df_filtered['Tiempo de cierre'].notnull().any():
                df_close_time = df_filtered.dropna(subset=['Tiempo de cierre'])
                fig_close = px.histogram(df_close_time, x='Tiempo de cierre', color_discrete_sequence=["#5E6B78"])
                fig_close.update_layout(xaxis_title="Tiempo de Cierre", yaxis_title="Cantidad de Casos")
                st.plotly_chart(fig_close, use_container_width=True)
            else:
                st.info("No hay datos disponibles sobre 'Tiempo de cierre'.")

        st.write("")

        # 📋 Tabla de Auditoría
        st.markdown("<h3 style='color: #0B1F33;'>📋 Tabla de Auditoría Completa</h3>", unsafe_with_html=True)
        columnas_auditoria = [
            'record', 'Assigned Date', 'Assigned Support', 'Descripción del chat', 
            'Conversation Status', 'Contact Name', 'Módulo Afectado', 'Categoría de Conversación', 
            'Consulta / Solicitud / Problema', 'Solución Soporte', 'Resumen de la conversación', 
            'Tiempo de cierre', 'Close Date'
        ]
        cols_existentes = [c for c in columnas_auditoria if c in df_filtered.columns]
        df_display = df_filtered[cols_existentes].copy()
        st.dataframe(df_display, use_container_width=True)

    except Exception as e:
        st.error(f"Error procesando el archivo: {e}")
else:
    st.info("👋 ¡Bienvenido! Por favor, arrastra y suelta tu archivo Excel o CSV en el panel de la izquierda para renderizar el Dashboard.")
