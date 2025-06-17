import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta, date
from components.database import supabase, obtener_reservas_completas, obtener_estadisticas_canchas
from components.auth import verificar_autenticacion, verificar_rol

# Verificar autenticación y roles permitidos
if not verificar_autenticacion():
    st.error("Por favor, inicie sesión para acceder a esta página.")
    st.stop()

if not verificar_rol(['admin', 'supervisor']):
    st.error("No tiene permisos para acceder a esta página.")
    st.stop()

st.title("📊 Reportes de Negocio")

# Crear pestañas para los diferentes reportes
tab_ingresos, tab_clientes = st.tabs([
    "📈 Ingresos y Ocupación", 
    "👥 Clientes y Fidelización"
])

# === Pestaña de Ingresos y Ocupación ===
with tab_ingresos:
    st.header("Ingresos y Ocupación de Canchas")
    
    try:
        # Obtener datos de reservas
        reservas_response = obtener_reservas_completas()
        if not reservas_response or not hasattr(reservas_response, 'data'):
            st.warning("No se pudieron obtener los datos de reservas")
            st.stop()
        
        df_reservas = pd.DataFrame(reservas_response.data)
        
        # Procesar los datos para crear las columnas necesarias
        df_reservas['nombre_cliente'] = df_reservas.apply(
            lambda x: f"{x['clientes']['nombre']} {x['clientes']['apellido']}" 
            if x.get('clientes') else "Cliente Desconocido", 
            axis=1
        )
        df_reservas['nombre_cancha'] = df_reservas.apply(
            lambda x: x['canchas']['nombre'] if x.get('canchas') else "Cancha Desconocida",
            axis=1
        )
        
        # Convertir columnas de fecha/hora
        df_reservas['fecha'] = pd.to_datetime(df_reservas['fecha'])
        
        # Filtros
        col1, col2 = st.columns(2)
        with col1:
            fecha_inicio = st.date_input(
                "Fecha inicio",
                value=datetime.now() - timedelta(days=30)
            )
        with col2:
            fecha_fin = st.date_input(
                "Fecha fin",
                value=datetime.now()
            )
        
        # Filtrar por rango de fechas
        mask = (df_reservas['fecha'].dt.date >= fecha_inicio) & (df_reservas['fecha'].dt.date <= fecha_fin)
        df_filtrado = df_reservas[mask]
        
        if len(df_filtrado) > 0:
            # === Gráficos de Ingresos ===
            st.subheader("Análisis de Ingresos")
            
            # Gráfico de ingresos por día
            ingresos_diarios = df_filtrado.groupby('fecha')['monto_total'].sum().reset_index()
            fig_ingresos = px.line(
                ingresos_diarios, 
                x='fecha', 
                y='monto_total',
                title='Ingresos Diarios',
                labels={'fecha': 'Fecha', 'monto_total': 'Ingresos Totales ($)'}
            )
            st.plotly_chart(fig_ingresos, use_container_width=True)
            
            # Gráfico de ingresos por cancha
            ingresos_cancha = df_filtrado.groupby('nombre_cancha')['monto_total'].sum().reset_index()
            fig_canchas = px.pie(
                ingresos_cancha, 
                values='monto_total', 
                names='nombre_cancha',
                title='Distribución de Ingresos por Cancha'
            )
            st.plotly_chart(fig_canchas, use_container_width=True)
            
            # === Gráficos de Ocupación ===
            st.subheader("Análisis de Ocupación")
            
            try:
                # Obtener estadísticas de canchas
                stats_response = obtener_estadisticas_canchas()
                if stats_response and hasattr(stats_response, 'data') and stats_response.data:
                    # Procesar los datos de estadísticas
                    canchas_stats = []
                    for cancha in stats_response.data:
                        try:
                            nombre_cancha = cancha.get('nombre', 'Sin nombre')
                            tipo_cancha = cancha.get('tipos_cancha', {}).get('nombre', 'Sin tipo')
                            
                            horas_reservadas = 0
                            total_ingresos = 0
                            
                            # Procesar reservas
                            if cancha.get('reservas'):
                                for reserva in cancha['reservas']:
                                    try:
                                        hora_inicio = datetime.strptime(reserva['hora_inicio'], '%H:%M:%S').time()
                                        hora_fin = datetime.strptime(reserva['hora_fin'], '%H:%M:%S').time()
                                        horas = (datetime.combine(date.today(), hora_fin) - 
                                                datetime.combine(date.today(), hora_inicio)).seconds / 3600
                                        horas_reservadas += horas
                                        total_ingresos += float(reserva.get('monto_total', 0))
                                    except (ValueError, TypeError, KeyError) as e:
                                        st.warning(f"Error procesando reserva de la cancha {nombre_cancha}: {str(e)}")
                                        continue

                            canchas_stats.append({
                                'nombre_cancha': nombre_cancha,
                                'horas_reservadas': round(horas_reservadas, 2),
                                'tipo_cancha': tipo_cancha,
                                'ingresos_totales': round(total_ingresos, 2)
                            })
                        except Exception as e:
                            st.warning(f"Error al procesar datos de la cancha: {str(e)}")
                            continue
                    
                    if canchas_stats:
                        # Crear DataFrame y mostrar gráficos
                        df_stats = pd.DataFrame(canchas_stats)
                        
                        # Gráfico de horas reservadas por cancha
                        fig_ocupacion = px.bar(
                            df_stats,
                            x='nombre_cancha',
                            y='horas_reservadas',
                            title='Horas Reservadas por Cancha',
                            labels={'nombre_cancha': 'Cancha', 'horas_reservadas': 'Horas Reservadas'},
                            color='tipo_cancha'
                        )
                        st.plotly_chart(fig_ocupacion, use_container_width=True)

                        # Tabla de resumen
                        st.subheader("Resumen por Cancha")
                        st.dataframe(
                            df_stats.style.format({
                                'horas_reservadas': '{:.1f}',
                                'ingresos_totales': '${:,.2f}'
                            })
                        )
                    else:
                        st.warning("No hay datos de reservas para mostrar")
                else:
                    st.warning("No se pudieron obtener datos de las canchas")

            except Exception as e:
                st.error(f"Error al procesar estadísticas de canchas: {str(e)}")
                import traceback
                st.error(f"Detalles del error: {traceback.format_exc()}")
            
            # Tabla de métricas clave
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    "Ingresos Totales", 
                    f"${df_filtrado['monto_total'].sum():,.2f}"
                )
            with col2:
                st.metric(
                    "Reservas Totales", 
                    len(df_filtrado)
                )
            with col3:
                st.metric(
                    "Promedio por Reserva", 
                    f"${df_filtrado['monto_total'].mean():,.2f}"
                )
        else:
            st.warning("No hay datos para el rango de fechas seleccionado")
    except Exception as e:
        st.error(f"Error al procesar los datos: {str(e)}")

# === Pestaña de Clientes y Fidelización ===
with tab_clientes:
    st.header("Análisis de Clientes y Fidelización")
    
    # === Análisis de Clientes ===
    if 'df_filtrado' in locals() and len(df_filtrado) > 0:
        st.subheader("Comportamiento de Clientes")
        
        # Frecuencia de reservas por cliente
        frecuencia_clientes = df_filtrado.groupby('nombre_cliente').size().reset_index(name='reservas')
        frecuencia_clientes = frecuencia_clientes.sort_values('reservas', ascending=False).head(10)
        
        fig_frecuencia = px.bar(
            frecuencia_clientes,
            x='nombre_cliente',
            y='reservas',
            title='Top 10 Clientes por Número de Reservas',
            labels={'nombre_cliente': 'Cliente', 'reservas': 'Número de Reservas'}
        )
        st.plotly_chart(fig_frecuencia, use_container_width=True)
        
        # Gasto total por cliente
        gasto_clientes = df_filtrado.groupby('nombre_cliente')['monto_total'].sum().reset_index()
        gasto_clientes = gasto_clientes.sort_values('monto_total', ascending=False).head(10)
        
        fig_gasto = px.bar(
            gasto_clientes,
            x='nombre_cliente',
            y='monto_total',
            title='Top 10 Clientes por Gasto Total',
            labels={'nombre_cliente': 'Cliente', 'monto_total': 'Gasto Total ($)'}
        )
        st.plotly_chart(fig_gasto, use_container_width=True)
        
        # === Métricas de Fidelización ===
        st.subheader("Métricas de Fidelización")
        
        # Calcular métricas de fidelización
        clientes_unicos = df_filtrado['id_cliente'].nunique()
        clientes_frecuentes = len(frecuencia_clientes[frecuencia_clientes['reservas'] > 3])
        tasa_retencion = (clientes_frecuentes / clientes_unicos) * 100 if clientes_unicos > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Clientes Únicos", clientes_unicos)
        with col2:
            st.metric("Clientes Frecuentes", clientes_frecuentes)
        with col3:
            st.metric("Tasa de Retención", f"{tasa_retencion:.1f}%")
        
        
    else:
        st.warning("No hay datos disponibles para el análisis de clientes")
