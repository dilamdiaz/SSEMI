# Backend/app/recordatorios/recordatorios_service.py

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text, and_
from .recordatorios_models import Notificacion
from app.database import SessionLocal # Importación para uso en el scheduler

# --- CONFIGURACIÓN ---
# Cuántos días antes se debe enviar el recordatorio (Requisito: "suficiente anticipación")
DIAS_DE_ANTICIPACION = 3 
# ---

def generar_recordatorios_pendientes(db: Session):
    """
    Función principal que revisa tareas pendientes y genera recordatorios
    en la tabla 'notificacion', aplicando restricciones de unicidad.
    """
    
    fecha_limite_recordatorio = datetime.now() + timedelta(days=DIAS_DE_ANTICIPACION)
    print(f"⏰ Buscando tareas con fecha_limite <= {fecha_limite_recordatorio.strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # 1. Consulta de Tareas Relevantes
        # **IMPORTANTE:** Ajusta la tabla 'tarea' y los nombres de las columnas 
        # ('fecha_limite', 'nombre', 'id_usuario_fk', 'estado') si difieren en tu BD.
        sql_select_tareas = text("""
        SELECT t.id_tarea, t.nombre AS nombre_tarea, t.fecha_limite, t.id_usuario_fk
        FROM tarea t
        WHERE t.fecha_limite <= :limite_fecha
          AND t.fecha_limite > NOW() 
          AND t.estado IN ('pendiente', 'en_revision') 
        """)
        
        tareas_pendientes = db.execute(sql_select_tareas, {'limite_fecha': fecha_limite_recordatorio}).fetchall()
        
        recordatorios_generados = 0
        
        for tarea in tareas_pendientes:
            id_tarea, nombre_tarea, fecha_limite, id_usuario = tarea
            
            # 2. Restricción: Evitar recordatorios duplicados (Requisito)
            # Verifica si ya existe una notificación PENDIENTE (leida=False) para esta tarea y usuario.
            existe_duplicado = db.query(Notificacion).filter(
                and_(
                    Notificacion.tarea_id_tarea == id_tarea,
                    Notificacion.id_usuario_fk == id_usuario,
                    Notificacion.leida == False
                )
            ).first()
            
            if existe_duplicado:
                continue # Evita inserción de duplicados

            # 3. Generación del Mensaje con Enlace Directo (Requisito)
            url_tarea = f"/dashboard/tarea/{id_tarea}"
            mensaje_base = (
                f"**Recordatorio:** Tienes pendiente la tarea '{nombre_tarea}' "
                f"con fecha límite el {fecha_limite.strftime('%Y-%m-%d')}. "
                f"**Haz clic aquí para ir a la tarea.**"
            )
            # Adjuntamos el enlace al mensaje para que el frontend lo pueda separar
            mensaje_completo = f"{mensaje_base}|URL:{url_tarea}" 

            # 4. Creación e Inserción del Recordatorio
            nuevo_recordatorio = Notificacion(
                id_usuario_fk=id_usuario,
                mensaje=mensaje_completo,
                tarea_id_tarea=id_tarea
            )
            
            db.add(nuevo_recordatorio)
            recordatorios_generados += 1

        db.commit()
        print(f"✅ Proceso de recordatorios finalizado. {recordatorios_generados} nuevos recordatorios generados.")
        
    except Exception as e:
        print(f"❌ Error al generar recordatorios: {e}")
        db.rollback()