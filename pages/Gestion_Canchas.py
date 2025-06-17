import streamlit as st
from components.database import supabase, registrar_auditoria
import pandas as pd
from datetime import datetime, time

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

def obtener_canchas(busqueda=""):
    """Obtiene la lista de canchas con sus tipos desde la base de datos"""
    try:
        query = supabase.table('canchas')\
            .select('*, tipos_cancha(nombre, precio_por_hora)')
            
        if busqueda:
            query = query.or_(f"nombre.ilike.%{busqueda}%,ubicacion.ilike.%{busqueda}%")
            
        response = query.execute()
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

def crear_horarios_disponibles(id_cancha, dias_seleccionados, hora_inicio, hora_fin):
    """Crea los horarios disponibles para una cancha"""
    try:
        # Crear los horarios para cada día seleccionado
        for dia in dias_seleccionados:
            data = {
                'id_cancha': id_cancha,
                'dia_semana': dia,
                'hora_inicio': hora_inicio.isoformat(),
                'hora_fin': hora_fin.isoformat()
            }
            response = supabase.table('horarios_disponibles').insert(data).execute()
            
            # Registrar en auditoría
            registrar_auditoria(
                st.session_state['usuario']['email'],
                'horarios_disponibles',
                'INSERT',
                f"Se creó horario para la cancha {id_cancha}, día {dia}",
                None,
                data
            )
        
        return True, "Horarios creados exitosamente"
    except Exception as e:
        return False, f"Error al crear horarios: {str(e)}"

def mostrar_horarios_disponibles(id_cancha):
    """
    Muestra los horarios disponibles de una cancha organizados por día.
    """
    try:
        horarios = supabase.table('horarios_disponibles')\
            .select('*')\
            .eq('id_cancha', id_cancha)\
            .execute()
        
        if not horarios.data:
            st.info("No hay horarios disponibles configurados para esta cancha.")
            return

        dias_semana = {
            1: 'Lunes',
            2: 'Martes',
            3: 'Miércoles',
            4: 'Jueves',
            5: 'Viernes',
            6: 'Sábado',
            7: 'Domingo'
        }

        st.write("#### 📅 Horarios Disponibles")
        
        # Ordenar horarios por día de la semana
        horarios_ordenados = sorted(horarios.data, key=lambda x: x['dia_semana'])
        
        # Crear columnas para mostrar los horarios
        cols = st.columns(2)
        
        for idx, horario in enumerate(horarios_ordenados):
            with cols[idx % 2]:
                dia = dias_semana.get(horario['dia_semana'], 'Día no válido')
                # Convertir las horas a formato más legible
                hora_inicio = datetime.strptime(horario['hora_inicio'], '%H:%M:%S').strftime('%H:%M')
                hora_fin = datetime.strptime(horario['hora_fin'], '%H:%M:%S').strftime('%H:%M')
                
                with st.container():
                    st.markdown(f"**{dia}**")
                    st.markdown(f"⏰ {hora_inicio} - {hora_fin}")
                    st.markdown("---")

    except Exception as e:
        st.error(f"Error al mostrar los horarios: {str(e)}")

# Configuración de la página
st.set_page_config(
    page_title="Gestión de Canchas",
    page_icon="⚽",
    layout="wide"
)

st.title("⚽ Gestión de Canchas")

# Barra de búsqueda
busqueda = st.text_input("🔍 Buscar cancha por nombre o ubicación", "")

# Pestañas
tab_lista, tab_crear = st.tabs(["Lista de Canchas", "Crear Cancha"])

with tab_lista:
    st.subheader("Canchas Disponibles")
    
    # Obtener y mostrar canchas
    canchas = obtener_canchas(busqueda)
    if not canchas:
        st.info("No se encontraron canchas que coincidan con la búsqueda.")
    else:
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
                
                # Mostrar horarios disponibles
                mostrar_horarios_disponibles(cancha['id'])

with tab_crear:
    st.subheader("Agregar Nueva Cancha")
    
    # Formulario de creación
    with st.form("nueva_cancha"):
        st.write("**Información Básica**")
        nombre = st.text_input("Nombre de la Cancha")
        
        # Obtener y mostrar tipos de cancha
        tipos = obtener_tipos_cancha()
        tipos_dict = {t['id']: f"{t['nombre']} - ${t['precio_por_hora']}/hora" for t in tipos}
        tipo_seleccionado = st.selectbox("Tipo de Cancha", options=list(tipos_dict.keys()), format_func=lambda x: tipos_dict[x])
        
        ubicacion = st.text_input("Ubicación")
        capacidad = st.number_input("Capacidad Máxima", min_value=1, value=20)
        observaciones = st.text_area("Observaciones", max_chars=200)
        
        # Horarios de disponibilidad
        st.write("**Horarios de Disponibilidad**")
        dias_semana = {
            1: "Lunes",
            2: "Martes",
            3: "Miércoles",
            4: "Jueves",
            5: "Viernes",
            6: "Sábado",
            7: "Domingo"
        }
        dias_seleccionados = []
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("Días disponibles:")
            for dia in range(1, 8):  # 1 a 7
                if st.checkbox(dias_semana[dia], key=f"dia_{dia}"):
                    dias_seleccionados.append(dia)
        
        with col2:
            hora_inicio = st.time_input("Hora de apertura", value=time(7, 0))
            hora_fin = st.time_input("Hora de cierre", value=time(22, 0))
            
            if hora_fin <= hora_inicio:
                st.error("La hora de cierre debe ser posterior a la hora de apertura")
        
        if st.form_submit_button("Crear Cancha"):
            if not nombre or not tipo_seleccionado or not ubicacion:
                st.error("Por favor complete todos los campos requeridos")
            elif not dias_seleccionados:
                st.error("Debe seleccionar al menos un día de disponibilidad")
            elif hora_fin <= hora_inicio:
                st.error("El horario de cierre debe ser posterior al de apertura")
            else:
                # Crear la cancha
                success, message = crear_cancha(nombre, tipo_seleccionado, ubicacion, capacidad, observaciones)
                
                if success:
                    # Obtener el ID de la cancha creada
                    cancha = supabase.table('canchas')\
                        .select('id')\
                        .eq('nombre', nombre)\
                        .single()\
                        .execute()
                    
                    # Crear los horarios
                    success_horarios, message_horarios = crear_horarios_disponibles(
                        cancha.data['id'],
                        dias_seleccionados,
                        hora_inicio,
                        hora_fin
                    )
                    
                    if success_horarios:
                        st.success(f"{message}. {message_horarios}")
                        st.rerun()
                    else:
                        st.warning(f"{message}. Sin embargo, hubo un error con los horarios: {message_horarios}")
                else:
                    st.error(message)