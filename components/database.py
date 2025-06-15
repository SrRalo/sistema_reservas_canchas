from supabase import create_client
from datetime import datetime, date, time
from typing import Optional, Dict, Any
import os

# Initialize Supabase client - You'll need to set these environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing Supabase credentials. Please set SUPABASE_URL and SUPABASE_KEY environment variables.")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def crear_reserva(
    id_cliente: int,
    id_cancha: int,
    fecha: date,
    hora_inicio: time,
    hora_fin: time,
    observaciones: Optional[str] = None
) -> Dict[str, Any]:
    """
    Crea una nueva reserva en el sistema.
    
    Args:
        id_cliente: ID del cliente que hace la reserva
        id_cancha: ID de la cancha a reservar
        fecha: Fecha de la reserva
        hora_inicio: Hora de inicio de la reserva
        hora_fin: Hora de fin de la reserva
        observaciones: Observaciones opcionales de la reserva
    
    Returns:
        Dict con la información de la reserva creada
    """
    try:
        # Primero verificamos que la cancha esté disponible
        cancha = supabase.table('canchas').select('*').eq('id', id_cancha).eq('disponible', True).execute()
        if not cancha.data:
            raise ValueError('La cancha no está disponible')
        
        # Verificar que no haya conflicto de horarios
        conflicto = supabase.table('reservas')\
            .select('*')\
            .eq('id_cancha', id_cancha)\
            .eq('fecha', fecha.isoformat())\
            .neq('estado', 'cancelada')\
            .lte('hora_inicio', hora_fin.isoformat())\
            .gte('hora_fin', hora_inicio.isoformat())\
            .execute()
            
        if conflicto.data:
            raise ValueError('Ya existe una reserva en ese horario')
        
        # Calcular monto total
        tipo_cancha = supabase.rpc(
            'calcular_monto_reserva',
            {
                'p_id_cancha': id_cancha,
                'p_hora_inicio': hora_inicio.isoformat(),
                'p_hora_fin': hora_fin.isoformat()
            }
        ).execute()
        
        monto_total = tipo_cancha.data
        
        # Crear la reserva
        reserva = supabase.table('reservas').insert({
            'id_cliente': id_cliente,
            'id_cancha': id_cancha,
            'fecha': fecha.isoformat(),
            'hora_inicio': hora_inicio.isoformat(),
            'hora_fin': hora_fin.isoformat(),
            'monto_total': monto_total,
            'estado': 'confirmada',
            'observaciones': observaciones
        }).execute()
        
        # Registrar en auditoría
        registrar_auditoria(
            'sistema',
            'reservas',
            'INSERT',
            f'Nueva reserva creada para el cliente {id_cliente} en la cancha {id_cancha}',
            None,
            reserva.data[0]
        )
        
        return reserva.data[0]
    
    except Exception as e:
        raise Exception(f'Error al crear la reserva: {str(e)}')

def registrar_auditoria(
    nombre_usuario: str,
    tabla_afectada: str,
    tipo_accion: str,
    descripcion: str,
    datos_anteriores: Optional[Dict] = None,
    datos_nuevos: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Registra una entrada en la bitácora de auditoría.
    
    Args:
        nombre_usuario: Nombre del usuario que realiza la acción
        tabla_afectada: Nombre de la tabla afectada
        tipo_accion: Tipo de acción (INSERT, UPDATE, DELETE, SELECT)
        descripcion: Descripción detallada de la acción
        datos_anteriores: Datos antes del cambio (para UPDATE/DELETE)
        datos_nuevos: Datos después del cambio (para INSERT/UPDATE)
    
    Returns:
        Dict con la información del registro de auditoría
    """
    try:
        auditoria = supabase.table('auditoria_bitacora').insert({
            'nombre_usuario': nombre_usuario,
            'tabla_afectada': tabla_afectada,
            'tipo_accion': tipo_accion,
            'descripcion_detallada': descripcion,
            'datos_anteriores': datos_anteriores,
            'datos_nuevos': datos_nuevos,
            'hora_inicio_ingreso': datetime.now().isoformat()
        }).execute()
        
        return auditoria.data[0]
    
    except Exception as e:
        raise Exception(f'Error al registrar auditoría: {str(e)}')

def obtener_reservas_completas():
    """
    Obtiene todas las reservas con sus detalles completos incluyendo información de canchas y clientes.
    
    Returns:
        List[Dict] con todas las reservas y sus detalles
    """
    try:
        return supabase.from_('reservas')\
            .select('''
                *,
                clientes:id_cliente (
                    id,
                    nombre,
                    apellido
                ),
                canchas:id_cancha (
                    id,
                    nombre,
                    tipos_cancha:id_tipo (
                        id,
                        nombre,
                        precio_por_hora
                    )
                )
            ''')\
            .execute()
    except Exception as e:
        raise Exception(f'Error al obtener reservas completas: {str(e)}')

def obtener_estadisticas_canchas():
    """
    Obtiene estadísticas de uso por cancha.
    
    Returns:
        Dict con data conteniendo lista de estadísticas por cancha
    """
    try:
        # Primero obtenemos todas las canchas con sus tipos
        response = supabase.from_('canchas')\
            .select('''
                id,
                nombre,
                tipos_cancha!inner (
                    nombre,
                    precio_por_hora
                )
            ''')\
            .execute()
        
        if not response.data:
            return {"data": []}

        # Luego obtenemos las reservas para cada cancha
        for cancha in response.data:
            # Obtener reservas para esta cancha
            reservas = supabase.from_('reservas')\
                .select('fecha, hora_inicio, hora_fin, monto_total')\
                .eq('id_cancha', cancha['id'])\
                .neq('estado', 'cancelada')\
                .execute()
            
            # Agregar las reservas a los datos de la cancha
            cancha['reservas'] = reservas.data if reservas.data else []
        
        return response
        
    except Exception as e:
        print(f"Error en obtener_estadisticas_canchas: {str(e)}")  # Para debugging
        raise Exception(f'Error al obtener estadísticas de canchas: {str(e)}')