import streamlit as st
from components.database import supabase, registrar_auditoria, obtener_reservas_completas
import pandas as pd
from datetime import datetime, timedelta, time

# Verificación de autenticación
if not st.session_state.get('autenticado', False):
    st.error("⛔ Debe iniciar sesión para acceder a esta página")
    st.stop()

# Verificación de rol
rol = st.session_state.get('usuario', {}).get('rol')
if rol not in ['admin', 'operador_reservas']:
    st.error("⛔ No tiene permisos para acceder a esta página")
    st.stop()

# Funciones auxiliares
def obtener_clientes_activos(busqueda=""):
    """Obtiene la lista de clientes activos"""
    try:
        query = supabase.table('clientes')\
            .select('*')\
            .eq('activo', True)
        
        if busqueda:
            query = query.or_(f"nombre.ilike.%{busqueda}%,apellido.ilike.%{busqueda}%,documento.ilike.%{busqueda}%")
            
        response = query.execute()
        return response.data
    except Exception as e:
        st.error(f"Error al obtener clientes: {str(e)}")
        return []

def obtener_canchas_disponibles():
    """Obtiene la lista de canchas disponibles con sus tipos"""
    try:
        response = supabase.table('canchas')\
            .select('*, tipos_cancha(nombre, precio_por_hora)')\
            .eq('disponible', True)\
            .execute()
        return response.data
    except Exception as e:
        st.error(f"Error al obtener canchas: {str(e)}")
        return []

def verificar_disponibilidad(id_cancha, fecha, hora_inicio, hora_fin):
    """Verifica si la cancha está disponible en el horario seleccionado"""
    try:
        # Verificar horario de funcionamiento
        dia_semana = fecha.weekday() + 1  # Python: 0-6, BD: 1-7
        horario = supabase.table('horarios_disponibles')\
            .select('*')\
            .eq('id_cancha', id_cancha)\
            .eq('dia_semana', dia_semana)\
            .execute()
        
        if not horario.data:
            return False, "No hay horario definido para este día"
        
        # Convertir strings de hora a objetos time
        hora_inicio_permitida = datetime.strptime(horario.data[0]['hora_inicio'], '%H:%M:%S').time()
        hora_fin_permitida = datetime.strptime(horario.data[0]['hora_fin'], '%H:%M:%S').time()
        
        if hora_inicio < hora_inicio_permitida or hora_fin > hora_fin_permitida:
            return False, f"El horario está fuera del rango permitido ({hora_inicio_permitida.strftime('%H:%M')} - {hora_fin_permitida.strftime('%H:%M')})"
        
        # Verificar reservas existentes
        reservas = supabase.table('reservas')\
            .select('*')\
            .eq('id_cancha', id_cancha)\
            .eq('fecha', fecha.isoformat())\
            .neq('estado', 'cancelada')\
            .execute()
        
        for reserva in reservas.data:
            hora_inicio_reserva = datetime.strptime(reserva['hora_inicio'], '%H:%M:%S').time()
            hora_fin_reserva = datetime.strptime(reserva['hora_fin'], '%H:%M:%S').time()
            
            if (hora_inicio < hora_fin_reserva and hora_fin > hora_inicio_reserva):
                return False, f"Ya existe una reserva en el horario {hora_inicio_reserva.strftime('%H:%M')} - {hora_fin_reserva.strftime('%H:%M')}"
        
        return True, "Horario disponible"
    except Exception as e:
        return False, f"Error al verificar disponibilidad: {str(e)}"

def obtener_reservas_filtradas(busqueda="", fecha_inicio=None, fecha_fin=None, estado=None):
    """Obtiene las reservas con filtros aplicados"""
    try:
        response = obtener_reservas_completas()
        if not response.data:
            return []
        
        df = pd.DataFrame(response.data)
        
        # Aplicar filtros
        if busqueda:
            busqueda = busqueda.lower()
            df = df[
                df['clientes'].apply(lambda x: 
                    busqueda in x['nombre'].lower() or 
                    busqueda in x['apellido'].lower()
                )
            ]
        
        if fecha_inicio:
            df = df[df['fecha'] >= fecha_inicio.isoformat()]
        
        if fecha_fin:
            df = df[df['fecha'] <= fecha_fin.isoformat()]
            
        if estado:
            df = df[df['estado'] == estado]
            
        return df.to_dict('records')
    except Exception as e:
        st.error(f"Error al obtener reservas: {str(e)}")
        return []

def cambiar_estado_reserva(id_reserva, nuevo_estado):
    """Actualiza el estado de una reserva"""
    try:
        # Obtener datos anteriores para auditoría
        reserva_anterior = supabase.table('reservas')\
            .select('*')\
            .eq('id', id_reserva)\
            .single()\
            .execute()
        
        response = supabase.table('reservas')\
            .update({'estado': nuevo_estado})\
            .eq('id', id_reserva)\
            .execute()
        
        # Registrar en auditoría
        registrar_auditoria(
            st.session_state['usuario']['email'],
            'reservas',
            'UPDATE',
            f"Se cambió el estado de la reserva ID: {id_reserva} a {nuevo_estado}",
            reserva_anterior.data,
            {'estado': nuevo_estado}
        )
        
        return True, "Estado actualizado exitosamente"
    except Exception as e:
        return False, f"Error al actualizar estado: {str(e)}"

def crear_reserva(id_cliente, id_cancha, fecha, hora_inicio, hora_fin, observaciones=""):
    """Crea una nueva reserva"""
    try:
        # Verificar disponibilidad
        disponible, mensaje = verificar_disponibilidad(id_cancha, fecha, hora_inicio, hora_fin)
        if not disponible:
            return False, mensaje
        
        # Calcular duración y monto
        duracion = (datetime.combine(fecha, hora_fin) - 
                   datetime.combine(fecha, hora_inicio)).seconds / 3600
        
        # Obtener precio por hora
        cancha = supabase.table('canchas')\
            .select('tipos_cancha(precio_por_hora)')\
            .eq('id', id_cancha)\
            .single()\
            .execute()
        
        precio_hora = cancha.data['tipos_cancha']['precio_por_hora']
        monto_total = precio_hora * duracion
        
        # Crear reserva
        data = {
            'id_cliente': id_cliente,
            'id_cancha': id_cancha,
            'fecha': fecha.isoformat(),
            'hora_inicio': hora_inicio.isoformat(),
            'hora_fin': hora_fin.isoformat(),
            'estado': 'pendiente',
            'monto_total': monto_total,
            'observaciones': observaciones
        }
        
        response = supabase.table('reservas').insert(data).execute()
        
        # Registrar en auditoría
        registrar_auditoria(
            st.session_state['usuario']['email'],
            'reservas',
            'INSERT',
            f"Se creó una reserva para el cliente {id_cliente}",
            None,
            data
        )
        
        return True, "Reserva creada exitosamente"
    except Exception as e:
        return False, f"Error al crear reserva: {str(e)}"

# Interfaz de usuario
st.title("📅 Gestión de Reservas")

# Crear pestañas
tab_lista, tab_crear = st.tabs(["📋 Lista de Reservas", "➕ Nueva Reserva"])

# Pestaña de Lista de Reservas
with tab_lista:
    st.subheader("Reservas Registradas")
    
    # Filtros
    col1, col2, col3 = st.columns([2,2,1])
    
    with col1:
        busqueda = st.text_input("🔍 Buscar por cliente")
    
    with col2:
        fecha_inicio, fecha_fin = st.date_input(
            "Rango de fechas",
            value=(datetime.now().date(), datetime.now().date() + timedelta(days=30)),
            min_value=datetime.now().date() - timedelta(days=365),
            max_value=datetime.now().date() + timedelta(days=365)
        )
    
    with col3:
        estado_filtro = st.selectbox(
            "Estado",
            options=["Todos", "pendiente", "confirmada", "cancelada", "completada"],
            index=0
        )
    
    # Obtener y mostrar reservas
    estado = None if estado_filtro == "Todos" else estado_filtro
    reservas = obtener_reservas_filtradas(busqueda, fecha_inicio, fecha_fin, estado)
    
    if not reservas:
        st.info("No se encontraron reservas con los filtros seleccionados")
    else:
        for reserva in reservas:
            with st.expander(
                f"📍 {reserva['canchas']['nombre']} - "\
                f"👤 {reserva['clientes']['nombre']} {reserva['clientes']['apellido']} - "\
                f"📅 {datetime.fromisoformat(reserva['fecha']).strftime('%d/%m/%Y')}"
            ):
                col1, col2 = st.columns([3,1])
                
                with col1:
                    st.write("**Detalles de la Reserva**")
                    st.write(f"🕒 Horario: {reserva['hora_inicio'][:5]} - {reserva['hora_fin'][:5]}")
                    st.write(f"💰 Monto: ${reserva['monto_total']:.2f}")
                    if reserva['observaciones']:
                        st.write(f"📝 Observaciones: {reserva['observaciones']}")
                    
                    # Estado actual con color
                    estado_color = {
                        'pendiente': '🟡',
                        'confirmada': '🟢',
                        'cancelada': '🔴',
                        'completada': '🔵'
                    }
                    st.write(f"Estado: {estado_color.get(reserva['estado'], '⚪')} {reserva['estado'].title()}")
                
                with col2:
                    # Acciones según el estado actual
                    if reserva['estado'] in ['pendiente', 'confirmada']:
                        if st.button("✅ Completar", key=f"complete_{reserva['id']}"):
                            success, message = cambiar_estado_reserva(reserva['id'], 'completada')
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)
                        
                        if st.button("❌ Cancelar", key=f"cancel_{reserva['id']}"):
                            if st.button("¿Confirmar cancelación?", key=f"confirm_cancel_{reserva['id']}"):
                                success, message = cambiar_estado_reserva(reserva['id'], 'cancelada')
                                if success:
                                    st.success(message)
                                    st.rerun()
                                else:
                                    st.error(message)

# Pestaña de Nueva Reserva
with tab_crear:
    st.subheader("Nueva Reserva")
    
    # Inicializar estado de confirmación
    if 'confirmar_reserva' not in st.session_state:
        st.session_state.confirmar_reserva = False
    
    # Paso 1: Seleccionar Cliente
    st.subheader("1. Seleccionar Cliente")
    busqueda_cliente = st.text_input("🔍 Buscar cliente por nombre, apellido o documento")
    clientes = obtener_clientes_activos(busqueda_cliente)

    if not clientes:
        st.warning("No se encontraron clientes activos")
        st.stop()

    cliente_seleccionado = st.selectbox(
        "Cliente",
        options=clientes,
        format_func=lambda x: f"{x['nombre']} {x['apellido']} - {x['documento']}"
    )

    # Paso 2: Seleccionar Cancha
    st.subheader("2. Seleccionar Cancha")
    canchas = obtener_canchas_disponibles()

    if not canchas:
        st.warning("No hay canchas disponibles")
        st.stop()

    cancha_seleccionada = st.selectbox(
        "Cancha",
        options=canchas,
        format_func=lambda x: f"{x['nombre']} - {x['tipos_cancha']['nombre']} - ${x['tipos_cancha']['precio_por_hora']}/hora"
    )

    # Paso 3: Seleccionar Fecha y Hora
    st.subheader("3. Seleccionar Fecha y Hora")
    col1, col2 = st.columns(2)

    with col1:
        fecha = st.date_input(
            "Fecha de reserva",
            min_value=datetime.now().date(),
            max_value=datetime.now().date() + timedelta(days=30)
        )

    with col2:
        hora_inicio = st.time_input("Hora de inicio", value=time(9, 0))
        hora_fin = st.time_input("Hora de fin", value=time(10, 0))

    # Validaciones mejoradas
    validaciones_ok = True
    
    # Validar fecha
    if fecha < datetime.now().date():
        st.error("La fecha debe ser futura")
        validaciones_ok = False
    
    # Validar horario
    if hora_fin <= hora_inicio:
        st.error("La hora de fin debe ser posterior a la hora de inicio")
        validaciones_ok = False
    else:
        duracion = (datetime.combine(fecha, hora_fin) - 
                   datetime.combine(fecha, hora_inicio)).seconds / 3600
        if duracion > 4:
            st.warning("⚠️ La duración excede 4 horas. ¿Está seguro?")
    
    # Verificar disponibilidad
    if validaciones_ok:
        disponible, mensaje = verificar_disponibilidad(
            cancha_seleccionada['id'],
            fecha,
            hora_inicio,
            hora_fin
        )
        
        if not disponible:
            st.error(mensaje)
            validaciones_ok = False

    # Si pasa todas las validaciones, mostrar resumen y confirmación
    if validaciones_ok:
        # Calcular monto
        duracion = (datetime.combine(fecha, hora_fin) - 
                   datetime.combine(fecha, hora_inicio)).seconds / 3600
        monto = cancha_seleccionada['tipos_cancha']['precio_por_hora'] * duracion
        
        # Mostrar resumen en un cuadro destacado
        st.subheader("4. Resumen de la Reserva")
        with st.container():
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Cliente:**", f"{cliente_seleccionado['nombre']} {cliente_seleccionado['apellido']}")
                st.write("**Cancha:**", cancha_seleccionada['nombre'])
                st.write("**Tipo:**", cancha_seleccionada['tipos_cancha']['nombre'])
            
            with col2:
                st.write("**Fecha:**", fecha.strftime("%d/%m/%Y"))
                st.write("**Horario:**", f"{hora_inicio.strftime('%H:%M')} - {hora_fin.strftime('%H:%M')}")
                st.write("**Duración:**", f"{duracion:.1f} horas")
                st.write("**Monto Total:** $", f"{monto:.2f}")
        
        # Observaciones
        observaciones = st.text_area("Observaciones (opcional)", max_chars=200)
        
        # Botón de confirmación con doble verificación
        if not st.session_state.confirmar_reserva:
            if st.button("💾 Crear Reserva", type="primary"):
                st.session_state.confirmar_reserva = True
                st.rerun()
        else:
            st.warning("⚠️ ¿Está seguro de crear esta reserva?")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Sí, Confirmar", type="primary"):
                    success, message = crear_reserva(
                        cliente_seleccionado['id'],
                        cancha_seleccionada['id'],
                        fecha,
                        hora_inicio,
                        hora_fin,
                        observaciones
                    )
                    
                    if success:
                        st.success(message)
                        st.session_state.confirmar_reserva = False
                        st.rerun()
                    else:
                        st.error(message)
            
            with col2:
                if st.button("❌ Cancelar"):
                    st.session_state.confirmar_reserva = False
                    st.rerun()