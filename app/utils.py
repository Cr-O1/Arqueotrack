import string
import random
from datetime import datetime
from urllib.parse import urlparse, urljoin
from flask import request


# OCUPACIONES, TIPOS, ESTADOS Y ROLES

OCUPACIONES = [
    ("arqueologo", "Arqueólogo"), ("restaurador", "Restaurador"),
    ("topografo", "Topógrafo"), ("geologo", "Geólogo"),
    ("antropologo", "Antropólogo"), ("historiador", "Historiador"),
    ("fotografo", "Fotógrafo"), ("dibujante", "Dibujante Técnico"),
    ("peon", "Peón"), ("estudiante", "Estudiante"),
    ("voluntario", "Voluntario"), ("admin", "Administrador"),
    ("otro", "Otro"),
]

TIPOS_HALLAZGO = [
    ("ceramica", "Cerámica"), ("hueso", "Hueso"), ("metal", "Metal"),
    ("piedra", "Piedra"), ("estructura", "Estructura"), ("moneda", "Moneda"),
    ("herramienta", "Herramienta"), ("joya", "Joya"), ("textil", "Textil"),
    ("vidrio", "Vidrio"), ("organico", "Material Orgánico"), ("otro", "Otro"),
]

TIPOS_EVENTO = [
    ("hallazgo", "Hallazgo"), ("reunion", "Reunión"),
    ("cambio_estado", "Cambio de Estado"), ("analisis", "Análisis"),
    ("decision", "Decisión"), ("visita", "Visita"),
    ("entrega", "Entrega"), ("otro", "Otro"),
]

ESTADOS_CONSERVACION = [
    ("excelente", "Excelente"), ("bueno", "Bueno"),
    ("regular", "Regular"), ("malo", "Malo"),
    ("muy_malo", "Muy Malo"), ("fragmentado", "Fragmentado"),
]

FASES_PREDEFINIDAS = [
    ("valoracion", "Valoración Inicial"),
    ("planificacion", "Planificación"),
    ("excavacion", "Excavación"),
    ("analisis", "Análisis"),
    ("conservacion", "Conservación"),
    ("documentacion", "Documentación"),
    ("restauracion", "Restauración"),
    ("exposicion", "Exposición"),
    ("cierre", "Cierre del Proyecto"),
]

ROLES_PERMISOS = {
    "visualizador": {"read"},
    "editor": {"read", "edit"},
    "colaborador": {"read", "edit", "create"},
    "asistente": {"read", "edit", "create", "delete"},
    "propietario": {"read", "edit", "create", "delete", "manage"}
}

def generar_codigo_unico():
    """Genera código alfanumérico único"""
    caracteres = string.ascii_uppercase + string.digits
    return ''.join(random.choice(caracteres) for _ in range(10))

def allowed_file(filename):
    """Verifica extensión permitida"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def is_safe_url(target):
    """Verifica URL segura"""
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

def time_ago(fecha):
    """Calcula tiempo transcurrido"""
    if isinstance(fecha, str):
        try:
            fecha = datetime.strptime(fecha, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return fecha

    if isinstance(fecha, datetime):
        ahora = datetime.utcnow()
        diff = ahora - fecha

        if diff.days > 365:
            return f"Hace {diff.days // 365} año(s)"
        elif diff.days > 30:
            return f"Hace {diff.days // 30} mes(es)"
        elif diff.days > 0:
            return f"Hace {diff.days} día(s)"
        elif diff.seconds > 3600:
            return f"Hace {diff.seconds // 3600} hora(s)"
        elif diff.seconds > 60:
            return f"Hace {diff.seconds // 60} minuto(s)"
        else:
            return "Hace unos segundos"

    return fecha