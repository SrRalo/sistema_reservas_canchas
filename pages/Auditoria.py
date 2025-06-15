import streamlit as st
from datetime import datetime, timedelta
from st_aggrid import AgGrid, GridOptionsBuilder
from components.database import supabase
import pandas as pd

# Verificación de autenticación y rol
if not st.session_state.get('autenticado', False):
    st.error("⛔ Debe iniciar sesión para acceder a esta página")
    st.stop()

if st.session_state.get('usuario', {}).get('rol') != 'admin':
    st.error("⛔ No tiene permisos para acceder a esta página")
    st.stop()

# Configuración de la página
st.title("📋 Bitácora del Sistema")
st.markdown("---")

# Filtros en la barra lateral
st.sidebar.header("Filtros de Búsqueda")

# Filtro de fechas
fecha_fin = datetime.now()
fecha_inicio = fecha_fin - timedelta(days=7)
fecha_inicio, fecha_fin = st.sidebar.date_input(
    "Rango de fechas",
    (fecha_inicio, fecha_fin),
    key="date_range"
)

# Filtro de usuarios
try:
    usuarios = supabase.table('usuarios').select('nombre, email').execute()
    usuarios_list = ['Todos'] + [u['email'] for u in usuarios.data]
    usuario_filtro = st.sidebar.selectbox("Usuario", usuarios_list)
except Exception as e:
    st.sidebar.error(f"Error al cargar usuarios: {str(e)}")
    usuario_filtro = "Todos"

# Filtro de tipo de acción
tipos_accion = ['Todos', 'INSERT', 'UPDATE', 'DELETE', 'LOGIN', 'LOGOUT']
tipo_accion_filtro = st.sidebar.selectbox("Tipo de Acción", tipos_accion)

# Consulta a la base de datos con filtros
try:    # Obtener todos los registros primero
    query = supabase.table('auditoria_bitacora').select('*')
    resultado = query.execute()
    
    if not resultado.data:
        st.info("No hay registros en la bitácora")
        st.stop()
    
    # Convertir a DataFrame
    df = pd.DataFrame(resultado.data)
    
    # Asegurarse de que todas las columnas necesarias existan
    columnas_requeridas = [
        'nombre_usuario', 'hora_inicio_ingreso', 'hora_salida', 
        'navegador', 'ip_acceso', 'nombre_maquina', 
        'tabla_afectada', 'tipo_accion', 'descripcion_detallada'
    ]
    
    for col in columnas_requeridas:
        if col not in df.columns:
            df[col] = ''  # Agregar columna vacía si no existe
    
    # Aplicar filtros al DataFrame
    if usuario_filtro != "Todos":
        df = df[df['nombre_usuario'] == usuario_filtro]
    if tipo_accion_filtro != "Todos":
        df = df[df['tipo_accion'] == tipo_accion_filtro]
    
    # Filtrar por fecha
    df['hora_inicio_ingreso'] = pd.to_datetime(df['hora_inicio_ingreso'])
    df = df[
        (df['hora_inicio_ingreso'].dt.date >= fecha_inicio) & 
        (df['hora_inicio_ingreso'].dt.date <= fecha_fin)
    ]
    
    if len(df) == 0:
        st.info("No se encontraron registros en la bitácora para los filtros seleccionados")
        st.stop()
    
    # Formatear fechas para visualización
    df['hora_inicio_ingreso'] = df['hora_inicio_ingreso'].dt.strftime('%Y-%m-%d %H:%M:%S')
    df['hora_salida'] = pd.to_datetime(df['hora_salida']).dt.strftime('%Y-%m-%d %H:%M:%S')
    
    # Renombrar columnas para mejor visualización
    df = df.rename(columns={
        'nombre_usuario': 'Usuario',
        'hora_inicio_ingreso': 'Hora de Ingreso',
        'hora_salida': 'Hora de Salida',
        'navegador': 'Navegador',
        'ip_acceso': 'IP',
        'nombre_maquina': 'Nombre PC',
        'tabla_afectada': 'Tabla',
        'tipo_accion': 'Acción',
        'descripcion_detallada': 'Descripción'
    })
      # Mostrar tabla directamente sin configuración compleja
    st.subheader("Registros de la Bitácora")
    
    # Crear una tabla simple
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

except Exception as e:
    st.error(f"Error al cargar los datos de la bitácora: {str(e)}")