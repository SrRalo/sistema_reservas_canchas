# Roles definidos en BD (según tabla usuarios)
ROLES = {
    'admin': 'Administrador',
    'operador_reservas': 'Operador', 
    'consultor': 'Consultor'
}

# Permisos por módulo
PERMISOS = {
    'admin': ['canchas', 'clientes', 'reservas', 'pagos', 'reportes', 'auditoria', 'usuarios'],
    'operador_reservas': ['canchas', 'clientes', 'reservas', 'pagos', 'reportes'],
    'consultor': ['reportes']
}


import streamlit as st
import bcrypt
from datetime import datetime
from components.database import supabase, registrar_auditoria

def hash_password(password: str) -> str:
    """Genera un hash seguro de la contraseña usando bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    """Verifica si la contraseña coincide con el hash almacenado."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def autenticar(email: str, password: str):
    """Autentica un usuario contra la base de datos."""
    try:
        # Buscar usuario por email
        response = supabase.table('usuarios')\
            .select('*')\
            .eq('email', email)\
            .eq('activo', True)\
            .execute()
        
        if not response.data:
            return None, "Usuario no encontrado"
        
        usuario = response.data[0]
        
        # Verificar contraseña
        if not verify_password(password, usuario['password_hash']):
            return None, "Contraseña incorrecta"
        
        # Actualizar último acceso
        supabase.table('usuarios')\
            .update({'ultimo_acceso': datetime.now().isoformat()})\
            .eq('id', usuario['id'])\
            .execute()
        
        # Registrar en auditoría
        registrar_auditoria(
            email,
            'usuarios',
            'LOGIN',
            f'Inicio de sesión exitoso del usuario {email}',
            None,
            None
        )
        
        return usuario, None
        
    except Exception as e:
        return None, f"Error de autenticación: {str(e)}"

def registrar_usuario(nombre: str, email: str, password: str, rol: str):
    """Registra un nuevo usuario en el sistema."""
    try:
        # Verificar que el rol sea válido
        if rol not in ROLES:
            return False, "Rol no válido"
        
        # Verificar si el email ya existe
        existe = supabase.table('usuarios')\
            .select('id')\
            .eq('email', email)\
            .execute()
            
        if existe.data:
            return False, "El email ya está registrado"
        
        # Crear hash de la contraseña
        password_hash = hash_password(password)
        
        # Insertar nuevo usuario
        usuario = supabase.table('usuarios').insert({
            'nombre': nombre,
            'email': email,
            'password_hash': password_hash,
            'rol': rol,
            'activo': True,
            'created_at': datetime.now().isoformat()
        }).execute()
        
        # Registrar en auditoría
        registrar_auditoria(
            'sistema',
            'usuarios',
            'INSERT',
            f'Nuevo usuario registrado: {email} con rol {rol}',
            None,
            usuario.data[0]
        )
        
        return True, "Usuario registrado exitosamente"
        
    except Exception as e:
        return False, f"Error al registrar usuario: {str(e)}"

def mostrar_login():
    """Interfaz gráfica del login con lógica de autenticación."""
    
    # Container principal para centrar el formulario
    with st.container():
        st.title("Inicio de Sesión 🔐")
        
        # Formulario
        email = st.text_input("Email", placeholder="usuario@ejemplo.com")
        password = st.text_input("Contraseña", type="password", placeholder="********")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Ingresar", type="primary"):
                if not email or not password:
                    st.error("Por favor ingrese email y contraseña")
                    return
                
                usuario, error = autenticar(email, password)
                if error:
                    st.error(error)
                else:
                    # Guardar datos de sesión
                    st.session_state['usuario'] = usuario
                    st.session_state['autenticado'] = True
                    st.success(f"Bienvenido {usuario['nombre']}!")
                    st.rerun()  # Recargar la página
        
        with col2:
            if st.button("Registrarse"):
                st.session_state['mostrar_registro'] = True
                st.rerun()

def mostrar_registro():
    """Interfaz gráfica del registro de usuarios."""
    
    with st.container():
        st.title("Registro de Usuario 📝")
        
        nombre = st.text_input("Nombre completo")
        email = st.text_input("Email")
        password = st.text_input("Contraseña", type="password")
        confirm_password = st.text_input("Confirmar contraseña", type="password")
        rol = st.selectbox("Rol", options=list(ROLES.keys()), format_func=lambda x: ROLES[x])
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Registrar", type="primary"):
                if not all([nombre, email, password, confirm_password]):
                    st.error("Todos los campos son obligatorios")
                    return
                
                if password != confirm_password:
                    st.error("Las contraseñas no coinciden")
                    return
                
                success, message = registrar_usuario(nombre, email, password, rol)
                if success:
                    st.success(message)
                    st.session_state['mostrar_registro'] = False
                    st.rerun()
                else:
                    st.error(message)
        
        with col2:
            if st.button("Volver al login"):
                st.session_state['mostrar_registro'] = False
                st.rerun()

def verificar_autenticacion() -> bool:
    """Verifica si hay un usuario autenticado en la sesión."""
    return st.session_state.get('autenticado', False)

def verificar_rol(roles_permitidos: list) -> bool:
    """
    Verifica si el usuario actual tiene uno de los roles permitidos.
    
    Args:
        roles_permitidos: Lista de roles que tienen permiso
        
    Returns:
        bool: True si el usuario tiene un rol permitido, False en caso contrario
    """
    if not verificar_autenticacion():
        return False
        
    usuario = st.session_state.get('usuario')
    if not usuario:
        return False
        
    return usuario.get('rol') in roles_permitidos

def cerrar_sesion():
    """Cierra la sesión del usuario actual."""
    if 'usuario' in st.session_state:
        email = st.session_state['usuario']['email']
        registrar_auditoria(
            email,
            'usuarios',
            'LOGOUT',
            f'Cierre de sesión del usuario {email}',
            None,
            None
        )
    
    # Limpiar datos de sesión
    if 'usuario' in st.session_state:
        del st.session_state['usuario']
    if 'autenticado' in st.session_state:
        del st.session_state['autenticado']
    st.session_state['mostrar_registro'] = False