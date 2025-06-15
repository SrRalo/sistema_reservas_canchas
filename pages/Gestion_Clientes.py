import streamlit as st
from components.database import supabase, registrar_auditoria
import pandas as pd
from datetime import datetime
import re

# Verificación de autenticación
if not st.session_state.get('autenticado', False):
    st.error("⛔ Debe iniciar sesión para acceder a esta página")
    st.stop()

# Verificación de rol
rol = st.session_state.get('usuario', {}).get('rol')
if rol not in ['admin', 'operador_reservas']:
    st.error("⛔ No tiene permisos para acceder a esta página")
    st.stop()

# Funciones de validación
def validar_email(email):
    """Valida el formato del email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validar_telefono(telefono):
    """Valida el formato del teléfono"""
    pattern = r'^[0-9]{10}$'
    return re.match(pattern, telefono) is not None

# Funciones CRUD
def obtener_clientes(busqueda="", mostrar_inactivos=False):
    """Obtiene la lista de clientes según los filtros"""
    try:
        query = supabase.table('clientes').select('*')
        
        if not mostrar_inactivos:
            query = query.eq('activo', True)
            
        if busqueda:
            query = query.or_(f"nombre.ilike.%{busqueda}%,apellido.ilike.%{busqueda}%,documento.ilike.%{busqueda}%")
            
        response = query.execute()
        return response.data
    except Exception as e:
        st.error(f"Error al obtener clientes: {str(e)}")
        return []

def crear_cliente(datos):
    """Crea un nuevo cliente en la base de datos"""
    try:
        # Verificar si existe el email o documento
        existe = supabase.table('clientes')\
            .select('id')\
            .or_(f"email.eq.{datos['email']},documento.eq.{datos['documento']}")\
            .execute()
            
        if existe.data:
            return False, "Ya existe un cliente con ese email o documento"
        
        response = supabase.table('clientes').insert(datos).execute()
        
        # Registrar en auditoría
        registrar_auditoria(
            st.session_state['usuario']['email'],
            'clientes',
            'INSERT',
            f"Se creó el cliente: {datos['nombre']} {datos['apellido']}",
            None,
            datos
        )
        
        return True, "Cliente creado exitosamente"
    except Exception as e:
        return False, f"Error al crear cliente: {str(e)}"

def actualizar_cliente(id_cliente, datos):
    """Actualiza un cliente existente"""
    try:
        # Obtener datos anteriores para auditoría
        cliente_anterior = supabase.table('clientes')\
            .select('*')\
            .eq('id', id_cliente)\
            .execute()
        
        # Verificar unicidad de email y documento
        if 'email' in datos or 'documento' in datos:
            existe = supabase.table('clientes')\
                .select('id')\
                .not_('id', 'eq', id_cliente)\
                .or_(
                    f"email.eq.{datos.get('email', '')},"\
                    f"documento.eq.{datos.get('documento', '')}"
                )\
                .execute()
                
            if existe.data:
                return False, "Ya existe otro cliente con ese email o documento"
        
        response = supabase.table('clientes')\
            .update(datos)\
            .eq('id', id_cliente)\
            .execute()
        
        # Registrar en auditoría
        registrar_auditoria(
            st.session_state['usuario']['email'],
            'clientes',
            'UPDATE',
            f"Se actualizó el cliente ID: {id_cliente}",
            cliente_anterior.data[0],
            datos
        )
        
        return True, "Cliente actualizado exitosamente"
    except Exception as e:
        return False, f"Error al actualizar cliente: {str(e)}"

def eliminar_cliente(id_cliente):
    """Elimina un cliente si no tiene reservas pendientes"""
    try:
        # Verificar si tiene reservas pendientes
        reservas = supabase.table('reservas')\
            .select('id')\
            .eq('id_cliente', id_cliente)\
            .not_('estado', 'eq', 'completada')\
            .execute()
        
        if reservas.data:
            return False, "No se puede eliminar el cliente porque tiene reservas pendientes"
        
        # Obtener datos para auditoría
        cliente = supabase.table('clientes')\
            .select('*')\
            .eq('id', id_cliente)\
            .execute()
        
        # Eliminar cliente
        response = supabase.table('clientes')\
            .delete()\
            .eq('id', id_cliente)\
            .execute()
        
        # Registrar en auditoría
        registrar_auditoria(
            st.session_state['usuario']['email'],
            'clientes',
            'DELETE',
            f"Se eliminó el cliente ID: {id_cliente}",
            cliente.data[0],
            None
        )
        
        return True, "Cliente eliminado exitosamente"
    except Exception as e:
        return False, f"Error al eliminar cliente: {str(e)}"

# Interfaz de usuario
st.title("👥 Gestión de Clientes")

# Barra de búsqueda y filtros
col1, col2 = st.columns([3, 1])
with col1:
    busqueda = st.text_input("🔍 Buscar por nombre, apellido o documento")
with col2:
    mostrar_inactivos = st.checkbox("Mostrar inactivos")

# Tabs para separar listado y creación
tab1, tab2 = st.tabs(["📋 Listado de Clientes", "➕ Nuevo Cliente"])

with tab1:
    st.subheader("Clientes Registrados")
    
    # Obtener y mostrar clientes
    clientes = obtener_clientes(busqueda, mostrar_inactivos)
    if clientes:
        for cliente in clientes:
            with st.expander(
                f"{'🟢' if cliente['activo'] else '🔴'} {cliente['nombre']} {cliente['apellido']} - {cliente['documento']}"
            ):
                col1, col2, col3 = st.columns([2,2,1])
                
                with col1:
                    st.write("**Información Personal**")
                    st.write(f"📧 Email: {cliente['email']}")
                    st.write(f"📞 Teléfono: {cliente['telefono']}")
                    if cliente['fecha_nacimiento']:
                        st.write(f"🎂 Fecha de Nacimiento: {cliente['fecha_nacimiento']}")
                
                with col2:
                    st.write("**Estado y Acciones**")
                    nuevo_estado = st.toggle("Cliente Activo", cliente['activo'], key=f"toggle_{cliente['id']}")
                    if nuevo_estado != cliente['activo']:
                        success, message = actualizar_cliente(cliente['id'], {'activo': nuevo_estado})
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                
                with col3:
                    st.write("**Acciones**")
                    if st.button("🗑️ Eliminar", key=f"del_{cliente['id']}"):
                        if st.button("¿Confirmar eliminación?", key=f"confirm_{cliente['id']}"):
                            success, message = eliminar_cliente(cliente['id'])
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)
    else:
        st.info("No se encontraron clientes con los filtros seleccionados")

with tab2:
    st.subheader("Registrar Nuevo Cliente")
    
    # Formulario de creación
    with st.form("nuevo_cliente"):
        col1, col2 = st.columns(2)
        
        with col1:
            nombre = st.text_input("Nombre")
            email = st.text_input("Email")
            documento = st.text_input("Documento")
        
        with col2:
            apellido = st.text_input("Apellido")
            telefono = st.text_input("Teléfono")
            fecha_nacimiento = st.date_input("Fecha de Nacimiento", min_value=datetime(1900, 1, 1).date())
        
        if st.form_submit_button("Registrar Cliente"):
            if not all([nombre, apellido, email, telefono, documento]):
                st.error("Por favor complete todos los campos requeridos")
            elif not validar_email(email):
                st.error("El formato del email no es válido")
            elif not validar_telefono(telefono):
                st.error("El teléfono debe contener 10 dígitos")
            else:
                datos = {
                    'nombre': nombre,
                    'apellido': apellido,
                    'email': email,
                    'telefono': telefono,
                    'documento': documento,
                    'fecha_nacimiento': fecha_nacimiento.isoformat(),
                    'activo': True
                }
                
                success, message = crear_cliente(datos)
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)