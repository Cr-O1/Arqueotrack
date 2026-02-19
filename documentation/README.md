# 🏺 ArqueoTrack

> **Si encuentras algo… no lo muevas. Regístralo.**

ArqueoTrack es una plataforma web de gestión arqueológica diseñada para hacer accesible la documentación y conservación del patrimonio histórico, tanto para ciudadanos que realizan hallazgos inesperados como para equipos profesionales que gestionan excavaciones a gran escala.

---

## 🎯 Propósito

Cuando alguien descubre restos arqueológicos, el instinto habitual es recogerlos y llevarlos a las autoridades. Sin embargo, **el contexto del hallazgo —dónde estaba, cómo estaba y en qué capa del suelo— es tan valioso como el objeto mismo**. Al moverlo, esa información se pierde para siempre.

ArqueoTrack nace para resolver este problema: guiar al ciudadano en el momento exacto del descubrimiento y centralizar toda la información en una sola plataforma que también sirve a los profesionales del sector.

### Problema que resuelve

- La mayoría de hallazgos llegan a los expertos sin información sobre su ubicación original.
- Los canales existentes (llamadas al 112, formularios administrativos) no son accesibles ni intuitivos para el ciudadano común.
- Los equipos arqueológicos carecen de herramientas digitales unificadas para gestionar excavaciones complejas.

---

## ✨ Funcionalidades

### Para el ciudadano
- **Registro guiado de hallazgos**: formulario sencillo para documentar lo encontrado sin necesidad de conocimientos técnicos.
- **Geolocalización en mapa**: marca la ubicación exacta del hallazgo usando coordenadas GPS sobre un mapa interactivo (Leaflet).
- **Fotografía adjunta**: sube una imagen del objeto directamente desde el registro (PNG, JPG, JPEG, GIF, WEBP, hasta 16 MB).
- **Código único de acceso**: cada hallazgo recibe un identificador alfanumérico de 8 caracteres generado automáticamente para su etiquetado y seguimiento.
- **Invitación a expertos**: comparte el yacimiento con arqueólogos por correo electrónico para que revisen y validen el registro.
- **Búsqueda por código**: accede a cualquier hallazgo directamente introduciendo su código único.

### Para el profesional
- **Gestión completa de yacimientos**: crea y administra excavaciones con nombre, descripción, fechas, responsable, área en m², altitud media y polígono geoespacial.
- **Fases de proyecto configurables**: divide la excavación en etapas predefinidas (valoración, planificación, excavación, análisis, conservación, documentación, restauración, exposición, cierre) con fechas, estado, objetivos, metodología, presupuesto, equipo participante y resultados esperados.
- **Sectores geoespaciales**: delimita zonas del terreno mediante polígonos GeoJSON sobre el mapa, cada uno con nombre, descripción y color identificativo.
- **Documentación científica de hallazgos**: registra tipo, descripción, estado de conservación, coordenadas precisas y unidad estratigráfica de cada pieza.
- **Timeline de eventos**: historial cronológico completo con tipos diferenciados (hallazgo, reunión, cambio de estado, análisis, decisión, visita, entrega) y niveles de prioridad (baja, media, alta, urgente).
- **Sistema de comentarios**: comunicación del equipo directamente sobre cada hallazgo, con historial completo y marcas de tiempo.
- **Roles y permisos granulares**: control de acceso diferenciado por yacimiento con cinco niveles de rol.
- **Panel de estadísticas**: resumen de hallazgos totales, yacimientos activos y finalizados, visible desde el dashboard principal.
- **Mapa de sectores con hallazgos superpuestos**: vista combinada de sectores delimitados y posición exacta de cada hallazgo.

### Sistema de roles y permisos

ArqueoTrack implementa un sistema de permisos por yacimiento con cinco niveles:

| Rol | Permisos |
|-----|---------|
| **Visualizador** | Lectura |
| **Editor** | Lectura + edición de elementos existentes |
| **Colaborador** | Lectura + edición + creación de hallazgos, fases, sectores y eventos |
| **Asistente** | Todo lo anterior + eliminación (excepto el yacimiento completo) |
| **Propietario** | Acceso total, incluyendo gestión de permisos e invitaciones |

---

## 🗂️ Estructura del Proyecto

```
arqueotrack/
├── app/
│   ├── __init__.py              # Application factory (Flask)
│   ├── models/
│   │   ├── user.py              # Modelo Usuario
│   │   ├── yacimiento.py        # Modelo Yacimiento
│   │   ├── hallazgo.py          # Modelo Hallazgo
│   │   ├── sector.py            # Modelo Sector
│   │   ├── fase.py              # Modelo FaseProyecto
│   │   ├── evento.py            # Modelo Evento (timeline)
│   │   ├── comentario.py        # Modelo Comentario
│   │   └── invitacion.py        # Modelo Invitacion
│   ├── blueprints/
│   │   ├── auth.py              # Registro, login, logout
│   │   ├── main.py              # Dashboard, perfil, búsqueda
│   │   ├── yacimiento.py        # CRUD yacimientos
│   │   ├── hallazgo.py          # CRUD hallazgos
│   │   ├── sector.py            # CRUD sectores + mapa
│   │   ├── fase.py              # Gestión de fases
│   │   ├── evento.py            # Timeline de eventos
│   │   └── invitacion.py        # Sistema de invitaciones
│   ├── forms.py                 # Formularios WTForms
│   └── utils.py                 # Helpers, constantes y generador de códigos
├── templates/
│   ├── base.html                # Layout principal con navegación responsive
│   ├── portada.html             # Landing page
│   ├── inicio.html              # Dashboard con estadísticas
│   ├── buscar_codigo.html       # Búsqueda por código
│   ├── fases/                   # Templates de fases
│   ├── sectores/                # Templates de sectores y mapas
│   ├── invitaciones/            # Templates de invitaciones
│   └── errores/                 # Páginas 404, 403, 500
├── static/
│   └── css/styles.css
├── uploads/                     # Archivos subidos por usuarios
├── config.py                    # Configuración centralizada
├── run.py                       # Punto de entrada con auto-setup
└── requirements.txt
```

---

## 🛠️ Stack Tecnológico

| Capa | Tecnología |
|------|-----------|
| **Backend** | Python 3.x + Flask |
| **ORM** | SQLAlchemy (con soporte para GeoJSON en texto) |
| **Base de datos** | SQLite (desarrollo) / PostgreSQL + PostGIS (producción) |
| **Autenticación** | Flask-Login + Flask-Bcrypt |
| **Formularios** | Flask-WTF + WTForms |
| **Protección CSRF** | Flask-WTF CSRFProtect |
| **Mapas** | Leaflet.js |
| **Geoespacial** | GeoJSON + polígonos Leaflet + coordenadas lat/lng |
| **Frontend** | Jinja2 + HTML/CSS vanilla con diseño responsive |
| **Archivos** | Gestión local con validación de extensión y límite de tamaño |

---

## ⚙️ Instalación y Puesta en Marcha

### Requisitos previos
- Python 3.9+
- pip

### Pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/tu-usuario/arqueotrack.git
cd arqueotrack

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno (opcional)
cp .env.example .env

# 5. Ejecutar la aplicación
python run.py
```

La aplicación estará disponible en `http://localhost:5000`.

> **Nota Replit**: El proyecto detecta automáticamente el entorno Replit (`REPL_ID`) y realiza el setup de la base de datos sin pasos adicionales.

---

## 🔐 Configuración

El archivo `config.py` centraliza toda la configuración de la aplicación:

| Variable | Descripción | Valor por defecto |
|----------|-------------|------------------|
| `SECRET_KEY` | Clave secreta de sesión | `dev-secret-key-...` |
| `SQLALCHEMY_DATABASE_URI` | URI de base de datos | `sqlite:///arqueotrack.db` |
| `UPLOAD_FOLDER` | Ruta de almacenamiento de imágenes | `./uploads` |
| `MAX_CONTENT_LENGTH` | Tamaño máximo de archivo | `16 MB` |
| `ALLOWED_EXTENSIONS` | Formatos de imagen permitidos | `png, jpg, jpeg, gif, webp` |
| `PERMANENT_SESSION_LIFETIME` | Duración de sesión | `7 días` |
| `WTF_CSRF_ENABLED` | Protección CSRF | `True` |
| `SESSION_COOKIE_HTTPONLY` | Cookies HTTP-only | `True` |
| `SESSION_COOKIE_SAMESITE` | Política SameSite | `Lax` |
| `ITEMS_PER_PAGE` | Paginación | `20` |

---

## 🔑 Modelo de Datos

### Usuario
```
id · nombre_usuario (único) · email (único) · contraseña (hash bcrypt)
nombre · apellidos · fecha_nacimiento · ocupacion · fecha_registro · activo · rol
```

### Yacimiento
```
id · user_id (FK) · nombre · ubicacion · descripcion
lat · lng · polygon_geojson · area_m2 · altitud_media
responsable · fecha_inicio · fecha_fin · fecha_creacion · fecha_actualizacion
```

### Hallazgo
```
id · codigo_acceso (8 chars, único) · yacimiento_id (FK) · user_id (FK)
tipo · descripcion · estado_conservacion · latitud · longitud
foto · fecha_hallazgo · encontrado_por_id (FK)
```
Tipos soportados: `cerámica, hueso, metal, piedra, estructura, moneda, herramienta, joya, textil, vidrio, material orgánico, otro`

Estados de conservación: `excelente, bueno, regular, malo, muy malo, fragmentado`

### FaseProyecto
```
id · yacimiento_id (FK) · nombre · descripcion · estado · orden
fecha_inicio · fecha_fin · objetivos · metodologia
recursos_necesarios · resultados_esperados · presupuesto
equipo_participante · responsable_id (FK) · notas
```

### Sector
```
id · yacimiento_id (FK) · nombre · descripcion · color
lat · lng · polygon_geojson · area
```

### Evento (timeline)
```
id · yacimiento_id (FK) · usuario_id (FK) · fase_id (FK)
hallazgo_id (FK) · sector_id (FK)
tipo · titulo · descripcion · fecha · ubicacion
participantes · resultados · prioridad · estado_evento
```
Tipos de evento: `hallazgo, reunión, cambio de estado, análisis, decisión, visita, entrega, otro`

Prioridades: `baja, media, alta, urgente` — Estados: `pendiente, en progreso, completado, cancelado`

### Comentario
```
id · hallazgo_id (FK) · usuario_id (FK) · texto · fecha
```

### Invitación
```
id · yacimiento_id (FK) · invitado_por_id (FK) · invitado_id (FK) · rol · estado
```

---

## 🤝 Sistema de Colaboración e Invitaciones

ArqueoTrack incluye un sistema de invitaciones que permite compartir cualquier yacimiento con otros usuarios de la plataforma:

1. El propietario accede al panel de invitaciones del yacimiento e introduce el correo del colaborador.
2. Selecciona el rol que quiere asignar: visualizador, editor, colaborador o asistente.
3. El colaborador recibe la invitación en su panel y puede aceptarla o rechazarla.
4. Una vez aceptada, el yacimiento aparece en el dashboard del colaborador junto a los suyos propios.
5. Todos los accesos y operaciones quedan sujetos al sistema de permisos granular según el rol asignado.

---

## 🗺️ Rutas Principales

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/` | Landing page |
| `GET/POST` | `/registro` | Registro de nuevo usuario |
| `GET/POST` | `/iniciar-sesion` | Inicio de sesión |
| `GET` | `/cerrar-sesion` | Cierre de sesión |
| `GET` | `/inicio` | Dashboard con estadísticas y mapa |
| `GET` | `/perfil` | Perfil del usuario |
| `GET/POST` | `/nuevo_yacimiento` | Crear yacimiento |
| `GET` | `/yacimiento/<id>` | Detalle de yacimiento |
| `GET` | `/yacimiento/<id>/fases` | Listar fases |
| `GET/POST` | `/yacimiento/<id>/nueva_fase` | Crear fase |
| `GET` | `/yacimiento/<id>/sectores` | Listar sectores |
| `GET` | `/yacimiento/<id>/mapa_sectores` | Mapa combinado sectores + hallazgos |
| `GET/POST` | `/yacimiento/<id>/invitaciones` | Gestión de invitaciones |
| `GET/POST` | `/buscar_codigo` | Buscar hallazgo por código único |
| `GET` | `/mis_invitaciones` | Panel de invitaciones del usuario |
| `GET/POST` | `/nuevo_hallazgo/<yacimiento_id>` | Registrar hallazgo |
| `GET` | `/hallazgo/<id>` | Detalle de hallazgo con comentarios |
| `GET/POST` | `/nuevo_evento/<yacimiento_id>` | Crear evento en el timeline |

---

## 🔒 Seguridad

- **Contraseñas**: hash con bcrypt mediante Flask-Bcrypt; nunca se almacenan en texto plano.
- **Protección CSRF**: todas las peticiones POST están protegidas con tokens CSRF gestionados por Flask-WTF.
- **Control de acceso por recurso**: cada endpoint verifica permisos del usuario sobre el yacimiento concreto antes de operar.
- **Cookies de sesión**: configuradas con `HttpOnly` y política `SameSite=Lax`.
- **Validación de archivos**: se comprueban extensión y tamaño antes de almacenar cualquier imagen subida.
- **Manejo de errores**: rollback automático de transacciones en caso de error de base de datos, con páginas de error personalizadas (403, 404, 500).

---

## 🧩 Constantes y Enumeraciones

Definidas en `app/utils.py` y reutilizadas en formularios, modelos y vistas:

```python
OCUPACIONES          # 13 roles profesionales del ámbito arqueológico
TIPOS_HALLAZGO       # 12 categorías de objeto (cerámica, hueso, metal...)
TIPOS_EVENTO         # 8 tipos de evento para el timeline
ESTADOS_CONSERVACION # 6 estados de conservación de hallazgos
FASES_PREDEFINIDAS   # 9 etapas estándar de un proyecto arqueológico
ROLES_PERMISOS       # Mapa de rol → conjunto de permisos
```

El generador de códigos únicos (`generar_codigo_unico`) produce cadenas de 10 caracteres alfanuméricos en mayúsculas usando `string.ascii_uppercase + string.digits`, garantizando identificadores irrepetibles para cada hallazgo registrado en la plataforma.
