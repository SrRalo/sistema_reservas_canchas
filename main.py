import streamlit as st
from components.auth import mostrar_login, mostrar_registro

# Configuración de la página
st.set_page_config(
    page_title="Sistema de Reservas de Canchas",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS para ocultar la barra lateral cuando no está autenticado
def hide_sidebar():
    st.markdown("""
        <style>
            [data-testid="collapsedControl"] {display: none;}
            section[data-testid="stSidebar"] {display: none;}
        </style>
        """, unsafe_allow_html=True)
        
def show_sidebar():
    st.markdown("""
        <style>
            [data-testid="collapsedControl"] {display: flex;}
            section[data-testid="stSidebar"] {display: block;}
        </style>
        """, unsafe_allow_html=True)

def mostrar_dashboard():
    """Muestra el dashboard principal una vez autenticado."""
    usuario = st.session_state.get('usuario', {})
    
    # Header con información del usuario y botón de logout
    col1, col2 = st.columns([3,1])
    with col1:
        st.title(f"Bienvenido {usuario.get('nombre', '')} 👋")
        st.write(f"Rol: {usuario.get('rol', '').title()}")
    
    with col2:
        if st.button("Cerrar Sesión", type="primary"):
            # Limpiar estado de sesión
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    # Contenido del dashboard
    st.markdown("---")
    st.header("🎯 Sistema de Gestión de Canchas Deportivas")
    
    # Descripción general
    st.markdown("""
    Este sistema integral permite gestionar reservas de canchas deportivas de manera eficiente y organizada.
    Diseñado para administradores y operadores, ofrece un control completo sobre canchas, clientes y reservas.
    """)
    
    # Módulos del sistema
    st.subheader("📚 Módulos del Sistema")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Módulos operativos
        st.markdown("### 🎮 Módulos Operativos")
        
        st.markdown("""
        #### 🏟️ Gestión de Canchas
        - Administración completa de canchas deportivas
        - Control de tipos de canchas y precios
        - Gestión de horarios disponibles
        - Búsqueda y filtrado de canchas
        
        #### 👥 Gestión de Clientes
        - Registro y mantenimiento de clientes
        - Control de estado (activo/inactivo)
        - Historial de reservas por cliente
        - Búsqueda avanzada de clientes
        
        #### 📅 Gestión de Reservas
        - Creación y seguimiento de reservas
        - Verificación de disponibilidad
        - Control de estados de reservas
        - Confirmación y cancelación
        """)
    
    with col2:
        # Módulos de control
        st.markdown("### 📊 Módulos de Control")
        
        st.markdown("""
        #### 📈 Reportes Business
        - Análisis de ocupación de canchas
        - Estadísticas de ingresos
        - Tendencias de reservas
        - Fidelización de clientes
        
        #### 📝 Auditoría
        - Registro detallado de acciones
        - Control de cambios en el sistema
        - Seguimiento de usuarios
        - Historial de modificaciones
        """)
    
    # Roles y permisos
    st.subheader("👥 Roles del Sistema")
    st.markdown("""
    - **Administrador**: Acceso completo a todas las funcionalidades
    - **Operador**: Gestión de canchas, clientes y reservas
    - **Consultor**: Visualización de reportes y consultas
    """)
    
    # Características destacadas
    st.subheader("⭐ Características Destacadas")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        - ✅ Interfaz intuitiva
        - ✅ Búsqueda avanzada
        - ✅ Filtros dinámicos
        """)
    
    with col2:
        st.markdown("""
        - ✅ Validaciones robustas
        - ✅ Control de horarios
        - ✅ Gestión de pagos
        """)
    
    with col3:
        st.markdown("""
        - ✅ Reportes detallados
        - ✅ Auditoría completa
        - ✅ Seguridad integrada
        """)
    
    # Nota de ayuda
    st.info("👈 Utiliza el menú lateral para acceder a los diferentes módulos según tu rol.")

def main():
    """Función principal que controla el flujo de la aplicación."""
    
    # Verificar si el usuario está autenticado
    if st.session_state.get('autenticado', False):
        show_sidebar()  # Mostrar la barra lateral
        mostrar_dashboard()
        return
    else:
        hide_sidebar()  # Ocultar la barra lateral
    
    # Si no está autenticado, mostrar login o registro
    if st.session_state.get('mostrar_registro', False):
        mostrar_registro()
    else:
        mostrar_login()

if __name__ == "__main__":
    main()