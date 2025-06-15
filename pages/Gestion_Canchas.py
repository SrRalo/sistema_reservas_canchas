import streamlit as st
from components.database import supabase, registrar_auditoria
import pandas as pd
from datetime import datetime

# Verificación de autenticación
if not st.session_state.get('autenticado', False):
    st.error("⛔ Debe iniciar sesión para acceder a esta página")
    st.stop()

# Verificación de rol
rol = st.session_state.get('usuario', {}).get('rol')
if rol not in ['admin', 'operador_reservas']:
    st.error("⛔ No tiene permisos para acceder a esta página")
    st.stop()

# Funciones CRUD
def obtener_tipos_cancha():
    """Obtiene la lista de tipos de cancha desde la base de datos"""
    try:
        response = supabase.table('tipos_cancha').select('*').execute()
        return response.data
    except Exception as e:
        st.error(f"Error al obtener tipos de cancha: {str(e)}")
        return []

def obtener_canchas():
    """Obtiene la lista de canchas con sus tipos desde la base de datos"""
    try:
        response = supabase.table('canchas')\
            .select('*, tipos_cancha(nombre, precio_por_hora)')\
            .execute()
        return response.data
    except Exception as e:
        st.error(f"Error al obtener canchas: {str(e)}")
        return []

def crear_cancha(nombre, id_tipo, ubicacion, capacidad, observaciones):
    """Crea una nueva cancha en la base de datos"""
    try:
        data = {
            'nombre': nombre,
            'id_tipo': id_tipo,
            'ubicacion': ubicacion,
            'capacidad_maxima': capacidad,
            'observaciones': observaciones,
            'disponible': True
        }
        response = supabase.table('canchas').insert(data).execute()
        
        # Registrar en auditoría
        registrar_auditoria(
            st.session_state['usuario']['email'],
            'canchas',
            'INSERT',
            f"Se creó la cancha: {nombre}",
            None,
            data
        )
        
        return True, "Cancha creada exitosamente"
    except Exception as e:
        return False, f"Error al crear cancha: {str(e)}"

def actualizar_cancha(id_cancha, datos):
    """Actualiza una cancha existente"""
    try:
        # Obtener datos anteriores para auditoría
        cancha_anterior = supabase.table('canchas')\
            .select('*')\
            .eq('id', id_cancha)\
            .execute()
        
        response = supabase.table('canchas')\
            .update(datos)\
            .eq('id', id_cancha)\
            .execute()
        
        # Registrar en auditoría
        registrar_auditoria(
            st.session_state['usuario']['email'],
            'canchas',
            'UPDATE',
            f"Se actualizó la cancha ID: {id_cancha}",
            cancha_anterior.data[0],
            datos
        )
        
        return True, "Cancha actualizada exitosamente"
    except Exception as e:
        return False, f"Error al actualizar cancha: {str(e)}"

def eliminar_cancha(id_cancha):
    """Elimina una cancha si no tiene reservas asociadas"""
    try:
        # Verificar si hay reservas
        reservas = supabase.table('reservas')\
            .select('id')\
            .eq('id_cancha', id_cancha)\
            .execute()
        
        if reservas.data:
            return False, "No se puede eliminar la cancha porque tiene reservas asociadas"
        
        # Obtener datos para auditoría
        cancha = supabase.table('canchas')\
            .select('*')\
            .eq('id', id_cancha)\
            .execute()
        
        # Eliminar cancha
        response = supabase.table('canchas')\
            .delete()\
            .eq('id', id_cancha)\
            .execute()
        
        # Registrar en auditoría
        registrar_auditoria(
            st.session_state['usuario']['email'],
            'canchas',
            'DELETE',
            f"Se eliminó la cancha ID: {id_cancha}",
            cancha.data[0],
            None
        )
        
        return True, "Cancha eliminada exitosamente"
    except Exception as e:
        return False, f"Error al eliminar cancha: {str(e)}"

# Interfaz de usuario
st.title("⚽ Gestión de Canchas")

# Tabs para separar listado y creación
tab1, tab2 = st.tabs(["📋 Listado de Canchas", "➕ Nueva Cancha"])

with tab1:
    st.subheader("Canchas Disponibles")
    
    # Obtener y mostrar canchas
    canchas = obtener_canchas()
    if canchas:
        df = pd.DataFrame(canchas)
        
        # Preparar datos para mostrar
        df['tipo'] = df['tipos_cancha'].apply(lambda x: x['nombre'])
        df['precio_hora'] = df['tipos_cancha'].apply(lambda x: x['precio_por_hora'])
        df['estado'] = df['disponible'].apply(lambda x: "🟢 Disponible" if x else "🔴 No Disponible")
        
        # Mostrar tabla con acciones
        for idx, cancha in df.iterrows():
            with st.expander(f"{cancha['nombre']} - {cancha['tipo']} - {cancha['estado']}"):
                col1, col2, col3 = st.columns([3,2,1])
                
                with col1:
                    st.write(f"**Ubicación:** {cancha['ubicacion']}")
                    st.write(f"**Capacidad:** {cancha['capacidad_maxima']} personas")
                    st.write(f"**Precio/hora:** ${cancha['precio_hora']}")
                    if cancha['observaciones']:
                        st.write(f"**Observaciones:** {cancha['observaciones']}")
                
                with col2:
                    nuevo_estado = st.toggle("Disponible", cancha['disponible'], key=f"toggle_{cancha['id']}")
                    if nuevo_estado != cancha['disponible']:
                        success, message = actualizar_cancha(cancha['id'], {'disponible': nuevo_estado})
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                
                with col3:
                    if st.button("🗑️ Eliminar", key=f"del_{cancha['id']}"):
                        if st.button("¿Confirmar eliminación?", key=f"confirm_{cancha['id']}"):
                            success, message = eliminar_cancha(cancha['id'])
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)

with tab2:
    st.subheader("Agregar Nueva Cancha")
    
    # Formulario de creación
    with st.form("nueva_cancha"):
        nombre = st.text_input("Nombre de la Cancha")
        
        # Obtener y mostrar tipos de cancha
        tipos = obtener_tipos_cancha()
        tipos_dict = {t['id']: f"{t['nombre']} - ${t['precio_por_hora']}/hora" for t in tipos}
        tipo_seleccionado = st.selectbox("Tipo de Cancha", options=list(tipos_dict.keys()), format_func=lambda x: tipos_dict[x])
        
        ubicacion = st.text_input("Ubicación")
        capacidad = st.number_input("Capacidad Máxima", min_value=1, value=20)
        observaciones = st.text_area("Observaciones", max_chars=200)
        
        if st.form_submit_button("Crear Cancha"):
            if not nombre or not tipo_seleccionado or not ubicacion:
                st.error("Por favor complete todos los campos requeridos")
            else:
                success, message = crear_cancha(nombre, tipo_seleccionado, ubicacion, capacidad, observaciones)
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)