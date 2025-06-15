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
    st.header("Panel de Control �")
    st.info("El sistema está en construcción. Pronto tendrás acceso a todas las funcionalidades según tu rol.")

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