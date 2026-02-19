# Plan de Refactorización Profesional - ArqueoTrack

## 📋 Análisis del Estado Actual

### Fortalezas Existentes
- ✅ Sistema de autenticación funcional con Flask-Login
- ✅ Gestión de roles y permisos básica implementada
- ✅ Integración con Leaflet para mapas
- ✅ Sistema de invitaciones colaborativas
- ✅ Códigos únicos alfanuméricos para hallazgos
- ✅ Sistema de comentarios y timeline
- ✅ Gestión de fases del proyecto
- ✅ División en sectores geoespaciales
- ✅ Soporte para polígonos GeoJSON

### Debilidades Críticas a Resolver
- ❌ Monolito de 1,500+ líneas en un solo archivo
- ❌ SQLite no escalable para producción
- ❌ Sin separación de responsabilidades (SoC)
- ❌ Sin tests unitarios ni de integración
- ❌ Sin sistema de versionado de datos
- ❌ Sin procesamiento asíncrono
- ❌ Sin caché distribuido
- ❌ Sin API REST documentada
- ❌ Sin CI/CD pipeline
- ❌ Sin monitoreo ni logging centralizado

---

## 🎯 Objetivos Estratégicos

### Técnicos
1. **Escalabilidad**: Soportar 10,000+ usuarios concurrentes
2. **Rendimiento**: <200ms respuesta API, <1s carga páginas
3. **Confiabilidad**: 99.9% uptime, disaster recovery
4. **Mantenibilidad**: Código modular, documentado, testeable
5. **Seguridad**: OWASP Top 10, GDPR compliance

### Funcionales
1. **Sistema Institucional**: Cuentas organizacionales con jerarquías
2. **Colaboración Avanzada**: Real-time updates, versionado
3. **Gestión Científica**: Matriz de Harris, UE, planimetría
4. **Generación de Reportes**: PDFs profesionales, exportación datos
5. **Red Social Profesional**: Perfiles arqueólogos, proyectos públicos

---

## 📦 Versiones de Desarrollo

### **VERSIÓN 1.0 - FUNDAMENTOS (2-3 semanas)**
**Objetivo**: Refactorizar arquitectura sin cambiar funcionalidad

#### 1.1 Reestructuración Base
- **Blueprints Flask**: Separar por dominio
  ```
  app/
  ├── __init__.py
  ├── models/
  │   ├── __init__.py
  │   ├── user.py
  │   ├── yacimiento.py
  │   ├── hallazgo.py
  │   └── sector.py
  ├── blueprints/
  │   ├── auth/
  │   ├── yacimientos/
  │   ├── hallazgos/
  │   ├── sectores/
  │   └── api/
  ├── services/
  ├── utils/
  └── config.py
  ```

- **Migración a PostgreSQL + PostGIS**
  - Usar Alembic para migraciones
  - Script de migración de datos SQLite → PostgreSQL
  - Configurar índices geoespaciales

- **Sistema de Configuración por Entornos**
  ```python
  config/
  ├── __init__.py
  ├── development.py
  ├── testing.py
  ├── production.py
  └── .env.example
  ```

- **Logging Estructurado**
  - Python `structlog`
  - Niveles: DEBUG, INFO, WARNING, ERROR, CRITICAL
  - Rotación de logs

#### 1.2 Testing Base
- **pytest + fixtures**
- **Coverage >70%**
- Tests unitarios para modelos
- Tests de integración para rutas

#### 1.3 Docker Compose Development
```yaml
services:
  postgres:
    image: postgis/postgis:15-3.3
  redis:
    image: redis:7-alpine
  app:
    build: .
    volumes:
      - .:/app
```

**Entregables v1.0**:
- ✅ Código refactorizado en blueprints
- ✅ PostgreSQL + PostGIS configurado
- ✅ Tests >70% coverage
- ✅ Docker Compose funcional
- ✅ Documentación técnica básica

---

### **VERSIÓN 2.0 - INSTITUCIONALIZACIÓN (3-4 semanas)**
**Objetivo**: Sistema multi-tenant para instituciones

#### 2.1 Modelo Institucional
```python
class Institucion(db.Model):
    id = db.Column(UUID, primary_key=True)
    nombre = db.Column(String(200), unique=True, nullable=False)
    tipo = db.Column(Enum('universidad', 'museo', 'empresa', 'ong'))
    pais = db.Column(String(2))  # ISO 3166-1 alpha-2
    verificada = db.Column(Boolean, default=False)
    logo_url = db.Column(String(500))
    sitio_web = db.Column(String(200))
    
    # Multi-tenancy
    tenant_id = db.Column(UUID, unique=True, nullable=False)
    
    # Metadata
    fecha_fundacion = db.Column(Date)
    descripcion = db.Column(Text)
    especialidades = db.Column(ARRAY(String))  # PostgreSQL array
    
    # Relaciones
    usuarios = relationship("Usuario", secondary="usuario_institucion")
    yacimientos = relationship("Yacimiento", back_populates="institucion")
```

#### 2.2 Roles Institucionales
```python
ROLES_INSTITUCIONALES = {
    'director_general': ['*'],  # Todos los permisos
    'director_proyecto': ['read', 'create', 'update', 'delete_propio'],
    'arquelogo_senior': ['read', 'create', 'update'],
    'arquelogo_junior': ['read', 'create'],
    'tecnico_campo': ['read', 'create_hallazgo'],
    'restaurador': ['read', 'update_conservacion'],
    'investigador_externo': ['read'],
    'estudiante': ['read_limitado']
}
```

#### 2.3 Sistema de Campañas
```python
class Campana(db.Model):
    id = db.Column(UUID, primary_key=True)
    yacimiento_id = db.Column(UUID, ForeignKey('yacimientos.id'))
    nombre = db.Column(String(200))
    anio = db.Column(Integer)
    fecha_inicio = db.Column(Date)
    fecha_fin = db.Column(Date)
    presupuesto = db.Column(Numeric(10, 2))
    
    # Director de campaña
    director_id = db.Column(UUID, ForeignKey('usuarios.id'))
    
    # Equipo
    equipo = relationship("Usuario", secondary="campana_equipo")
    
    # Estadísticas
    hallazgos_count = db.Column(Integer, default=0)
    sectores_excavados = db.Column(ARRAY(UUID))
```

#### 2.4 Mejoras en Permisos
- **Row-Level Security (RLS)** en PostgreSQL
- **Permisos granulares** por recurso
- **Audit trail** completo

**Entregables v2.0**:
- ✅ Sistema multi-tenant funcional
- ✅ Instituciones con verificación
- ✅ Campañas arqueológicas
- ✅ Roles institucionales avanzados
- ✅ Dashboard institucional

---

### **VERSIÓN 3.0 - ARQUEOLOGÍA CIENTÍFICA (4-5 semanas)**
**Objetivo**: Herramientas científicas profesionales

#### 3.1 Unidades Estratigráficas (UE)
```python
class UnidadEstratigráfica(db.Model):
    id = db.Column(UUID, primary_key=True)
    yacimiento_id = db.Column(UUID, ForeignKey('yacimientos.id'))
    numero_ue = db.Column(Integer, nullable=False)
    tipo = db.Column(Enum('deposito', 'interfaz', 'corte'))
    
    # Descripción estratigráfica
    descripcion = db.Column(Text)
    color_munsell = db.Column(String(20))
    textura = db.Column(String(100))
    compactacion = db.Column(String(50))
    composicion = db.Column(Text)
    
    # Relaciones estratigráficas
    anterior_a = relationship("UnidadEstratigráfica", 
                            secondary="relaciones_ue",
                            primaryjoin="UnidadEstratigráfica.id==RelacionUE.ue_posterior_id",
                            secondaryjoin="UnidadEstratigráfica.id==RelacionUE.ue_anterior_id")
    
    # Materiales asociados
    hallazgos = relationship("Hallazgo", back_populates="unidad_estratigrafica")
    
    # Coordenadas
    geometria = db.Column(Geometry('POLYGON', srid=4326))
    cota_superior = db.Column(Numeric(10, 3))
    cota_inferior = db.Column(Numeric(10, 3))
```

#### 3.2 Matriz de Harris
- **Algoritmo de ordenación topológica**
- **Visualización interactiva** (D3.js)
- **Validación de relaciones** (detectar ciclos)
- **Exportación** a GraphML, DOT

```python
class MatrizHarris:
    def __init__(self, yacimiento_id: UUID):
        self.yacimiento_id = yacimiento_id
        self.unidades = self._cargar_unidades()
        self.grafo = self._construir_grafo()
    
    def validar_coherencia(self) -> List[str]:
        """Detecta inconsistencias en relaciones estratigráficas"""
        errores = []
        
        # Detectar ciclos
        if self._tiene_ciclos():
            errores.append("Se detectaron relaciones circulares")
        
        # Validar cotas
        for ue in self.unidades:
            if ue.cota_superior < ue.cota_inferior:
                errores.append(f"UE {ue.numero_ue}: cota superior < inferior")
        
        return errores
    
    def generar_secuencia(self) -> List[UnidadEstratigráfica]:
        """Genera secuencia cronológica de UEs"""
        return nx.topological_sort(self.grafo)
    
    def exportar_graphml(self) -> str:
        """Exporta matriz para software especializado"""
        return nx.write_graphml(self.grafo)
```

#### 3.3 Sistema de Muestras y Análisis
```python
class Muestra(db.Model):
    id = db.Column(UUID, primary_key=True)
    codigo = db.Column(String(50), unique=True)
    tipo = db.Column(Enum('c14', 'palinologia', 'antracologia', 'ceramica'))
    
    # Origen
    hallazgo_id = db.Column(UUID, ForeignKey('hallazgos.id'))
    ue_id = db.Column(UUID, ForeignKey('unidades_estratigraficas.id'))
    coordenadas = db.Column(Geometry('POINT', srid=4326))
    
    # Procesamiento
    fecha_recogida = db.Column(DateTime)
    fecha_envio_laboratorio = db.Column(DateTime)
    laboratorio = db.Column(String(200))
    
    # Resultados
    resultados = relationship("ResultadoAnalisis")
```

#### 3.4 Planimetría Avanzada
- **Capas vectoriales** para planimetrías
- **Importación DXF/DWG**
- **Generación de perfiles** automáticos
- **Sistema de coordenadas** configurable

**Entregables v3.0**:
- ✅ Sistema completo de UEs
- ✅ Matriz de Harris interactiva
- ✅ Gestión de muestras y análisis
- ✅ Herramientas de planimetría
- ✅ Exportación a formatos científicos

---

### **VERSIÓN 4.0 - RENDIMIENTO Y ESCALABILIDAD (3-4 semanas)**
**Objetivo**: Optimización para producción

#### 4.1 Procesamiento Asíncrono (Celery + Redis)
```python
# tasks.py
from celery import Celery

celery = Celery('arqueotrack', broker='redis://localhost:6379')

@celery.task
def generar_informe_pdf(yacimiento_id: UUID):
    """Genera informe PDF en background"""
    yacimiento = Yacimiento.query.get(yacimiento_id)
    pdf = PDFGenerator(yacimiento)
    pdf.generar()
    
    # Notificar al usuario
    notificar_usuario(yacimiento.user_id, "Informe PDF generado")

@celery.task
def procesar_imagen_hallazgo(hallazgo_id: UUID):
    """Genera thumbnails y optimiza imágenes"""
    hallazgo = Hallazgo.query.get(hallazgo_id)
    ImageProcessor.generar_thumbnails(hallazgo.foto)
    ImageProcessor.optimizar(hallazgo.foto)

@celery.task
def calcular_estadisticas_yacimiento(yacimiento_id: UUID):
    """Recalcula estadísticas complejas"""
    estadisticas = EstadisticasService.calcular(yacimiento_id)
    cache.set(f'stats_{yacimiento_id}', estadisticas, timeout=3600)
```

#### 4.2 Sistema de Caché (Redis)
```python
from flask_caching import Cache

cache = Cache(config={
    'CACHE_TYPE': 'RedisCache',
    'CACHE_REDIS_URL': 'redis://localhost:6379/1',
    'CACHE_DEFAULT_TIMEOUT': 300
})

# Decoradores de caché
@cache.cached(timeout=600, key_prefix='yacimientos_list')
def listar_yacimientos(user_id):
    return Yacimiento.query.filter_by(user_id=user_id).all()

@cache.memoize(timeout=3600)
def estadisticas_hallazgos(yacimiento_id):
    return {
        'total': Hallazgo.query.filter_by(yacimiento_id=yacimiento_id).count(),
        'por_tipo': db.session.query(
            Hallazgo.tipo, func.count(Hallazgo.id)
        ).group_by(Hallazgo.tipo).all()
    }
```

#### 4.3 Optimizaciones de Base de Datos
```sql
-- Índices geoespaciales
CREATE INDEX idx_hallazgos_coords ON hallazgos USING GIST(geometria);
CREATE INDEX idx_sectores_polygon ON sectores USING GIST(geometria);

-- Índices compuestos
CREATE INDEX idx_hallazgos_yacimiento_fecha ON hallazgos(yacimiento_id, fecha);
CREATE INDEX idx_eventos_yacimiento_tipo ON eventos(yacimiento_id, tipo);

-- Vistas materializadas
CREATE MATERIALIZED VIEW mv_estadisticas_yacimientos AS
SELECT 
    y.id,
    COUNT(DISTINCT h.id) as total_hallazgos,
    COUNT(DISTINCT s.id) as total_sectores,
    COUNT(DISTINCT f.id) as total_fases
FROM yacimientos y
LEFT JOIN hallazgos h ON h.yacimiento_id = y.id
LEFT JOIN sectores s ON s.yacimiento_id = y.id
LEFT JOIN fases_proyecto f ON f.yacimiento_id = y.id
GROUP BY y.id;

-- Refresh automático
CREATE INDEX ON mv_estadisticas_yacimientos(id);
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_estadisticas_yacimientos;
```

#### 4.4 CDN y Almacenamiento
- **AWS S3** / **MinIO** para archivos
- **CloudFront** / **Cloudflare** CDN
- **Image optimization** automática
- **Lazy loading** de imágenes

**Entregables v4.0**:
- ✅ Celery configurado para tareas pesadas
- ✅ Redis caché implementado
- ✅ Base de datos optimizada
- ✅ CDN configurado
- ✅ Rendimiento <200ms API

---

### **VERSIÓN 5.0 - VERSIONADO Y COLABORACIÓN (3-4 semanas)**
**Objetivo**: Sistema de versionado tipo Git para datos

#### 5.1 Sistema de Versionado
```python
class Version(db.Model):
    id = db.Column(UUID, primary_key=True)
    entidad_tipo = db.Column(String(50))  # 'hallazgo', 'sector', etc
    entidad_id = db.Column(UUID)
    version_numero = db.Column(Integer)
    
    # Datos versionados (JSONB para flexibilidad)
    datos = db.Column(JSONB)
    
    # Metadata
    usuario_id = db.Column(UUID, ForeignKey('usuarios.id'))
    fecha_creacion = db.Column(DateTime, default=datetime.utcnow)
    mensaje_commit = db.Column(Text)
    
    # Relaciones con versiones
    version_anterior_id = db.Column(UUID, ForeignKey('versiones.id'))
    
    # Diff
    cambios = db.Column(JSONB)  # {'campo': {'anterior': X, 'nuevo': Y}}

class VersionService:
    @staticmethod
    def crear_version(entidad, usuario, mensaje):
        """Crea nueva versión de una entidad"""
        ultima_version = Version.query.filter_by(
            entidad_tipo=entidad.__tablename__,
            entidad_id=entidad.id
        ).order_by(Version.version_numero.desc()).first()
        
        nueva_version = Version(
            entidad_tipo=entidad.__tablename__,
            entidad_id=entidad.id,
            version_numero=(ultima_version.version_numero + 1) if ultima_version else 1,
            datos=entidad.to_dict(),
            usuario_id=usuario.id,
            mensaje_commit=mensaje,
            version_anterior_id=ultima_version.id if ultima_version else None,
            cambios=VersionService._calcular_diff(ultima_version, entidad)
        )
        
        db.session.add(nueva_version)
        return nueva_version
    
    @staticmethod
    def revertir(entidad_id, version_numero):
        """Revierte entidad a versión específica"""
        version = Version.query.filter_by(
            entidad_id=entidad_id,
            version_numero=version_numero
        ).first()
        
        if not version:
            raise ValueError("Versión no encontrada")
        
        # Restaurar datos
        entidad = db.session.get(version.entidad_tipo, entidad_id)
        for campo, valor in version.datos.items():
            setattr(entidad, campo, valor)
        
        db.session.commit()
```

#### 5.2 Colaboración en Tiempo Real (WebSockets)
```python
from flask_socketio import SocketIO, emit, join_room

socketio = SocketIO(app, cors_allowed_origins="*")

@socketio.on('join_yacimiento')
def handle_join(data):
    yacimiento_id = data['yacimiento_id']
    join_room(f'yacimiento_{yacimiento_id}')
    emit('user_joined', {'user': current_user.nombre_usuario}, 
         room=f'yacimiento_{yacimiento_id}')

@socketio.on('hallazgo_actualizado')
def handle_hallazgo_update(data):
    yacimiento_id = data['yacimiento_id']
    emit('hallazgo_changed', data, 
         room=f'yacimiento_{yacimiento_id}', 
         include_self=False)
```

#### 5.3 Sistema de Conflictos
```python
class ConflictoEdicion(db.Model):
    id = db.Column(UUID, primary_key=True)
    entidad_tipo = db.Column(String(50))
    entidad_id = db.Column(UUID)
    
    # Usuarios en conflicto
    usuario1_id = db.Column(UUID)
    usuario2_id = db.Column(UUID)
    
    # Versiones en conflicto
    version1_id = db.Column(UUID)
    version2_id = db.Column(UUID)
    
    # Estado
    resuelto = db.Column(Boolean, default=False)
    resolucion = db.Column(JSONB)
    
    fecha_deteccion = db.Column(DateTime, default=datetime.utcnow)
```

**Entregables v5.0**:
- ✅ Sistema completo de versionado
- ✅ Undo/Redo funcional
- ✅ WebSockets para colaboración
- ✅ Detección de conflictos
- ✅ Historial de cambios completo

---

### **VERSIÓN 6.0 - INFORMES Y EXPORTACIÓN (2-3 semanas)**
**Objetivo**: Generación profesional de documentos

#### 6.1 Sistema de Plantillas de Informes
```python
class PlantillaInforme(db.Model):
    id = db.Column(UUID, primary_key=True)
    nombre = db.Column(String(200))
    tipo = db.Column(Enum('memoria', 'preliminar', 'inventario'))
    
    # Plantilla LaTeX/Jinja2
    template_content = db.Column(Text)
    
    # Secciones configurables
    secciones = db.Column(JSONB)  # ['intro', 'metodologia', 'hallazgos', ...]
    
    # Institución asociada
    institucion_id = db.Column(UUID, ForeignKey('instituciones.id'))
    
    # Metadata
    publica = db.Column(Boolean, default=False)
    usos_count = db.Column(Integer, default=0)
```

#### 6.2 Generador de PDFs Profesionales
```python
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors

class InformeGenerator:
    def __init__(self, yacimiento_id, plantilla_id=None):
        self.yacimiento = Yacimiento.query.get(yacimiento_id)
        self.plantilla = PlantillaInforme.query.get(plantilla_id) if plantilla_id else None
        self.story = []
        
    def generar(self) -> str:
        """Genera PDF completo"""
        filename = f"informe_{self.yacimiento.id}.pdf"
        doc = SimpleDocTemplate(filename, pagesize=A4)
        
        # Portada
        self._add_portada()
        
        # Índice
        self._add_indice()
        
        # Introducción
        self._add_introduccion()
        
        # Metodología
        self._add_metodologia()
        
        # Hallazgos
        self._add_catalogo_hallazgos()
        
        # Estratigrafía
        self._add_matriz_harris()
        
        # Conclusiones
        self._add_conclusiones()
        
        # Bibliografía
        self._add_bibliografia()
        
        # Anexos
        self._add_anexos()
        
        doc.build(self.story)
        return filename
    
    def _add_catalogo_hallazgos(self):
        """Genera catálogo detallado de hallazgos"""
        data = [['Código', 'Tipo', 'UE', 'Coordenadas', 'Estado']]
        
        for hallazgo in self.yacimiento.hallazgos:
            data.append([
                hallazgo.codigo_acceso,
                hallazgo.tipo,
                hallazgo.ue.numero_ue if hallazgo.ue else '-',
                f"{hallazgo.lat}, {hallazgo.lng}",
                hallazgo.estado_conservacion
            ])
        
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        self.story.append(table)
```

#### 6.3 Exportación de Datos
```python
class ExportService:
    @staticmethod
    def exportar_csv(yacimiento_id):
        """Exporta hallazgos a CSV"""
        hallazgos = Hallazgo.query.filter_by(yacimiento_id=yacimiento_id).all()
        
        df = pd.DataFrame([h.to_dict() for h in hallazgos])
        return df.to_csv(index=False)
    
    @staticmethod
    def exportar_geojson(yacimiento_id):
        """Exporta datos geoespaciales"""
        from geoalchemy2.shape import to_shape
        
        features = []
        for hallazgo in Hallazgo.query.filter_by(yacimiento_id=yacimiento_id).all():
            if hallazgo.geometria:
                features.append({
                    'type': 'Feature',
                    'geometry': mapping(to_shape(hallazgo.geometria)),
                    'properties': {
                        'codigo': hallazgo.codigo_acceso,
                        'tipo': hallazgo.tipo,
                        'fecha': str(hallazgo.fecha)
                    }
                })
        
        return {
            'type': 'FeatureCollection',
            'features': features
        }
    
    @staticmethod
    def exportar_shapefile(yacimiento_id):
        """Exporta a ESRI Shapefile"""
        # Implementar con fiona/geopandas
        pass
```

**Entregables v6.0**:
- ✅ Sistema de plantillas de informes
- ✅ Generación PDFs profesionales
- ✅ Exportación CSV, GeoJSON, Shapefile
- ✅ Configuración personalizada por institución
- ✅ Catálogos automatizados

---

### **VERSIÓN 7.0 - RED SOCIAL PROFESIONAL (4-5 semanas)**
**Objetivo**: LinkedIn para arqueólogos

#### 7.1 Perfiles Profesionales Enriquecidos
```python
class PerfilProfesional(db.Model):
    usuario_id = db.Column(UUID, ForeignKey('usuarios.id'), primary_key=True)
    
    # Información académica
    titulo_academico = db.Column(String(200))
    universidad = db.Column(String(200))
    anio_graduacion = db.Column(Integer)
    
    # Especialidades
    especialidades = db.Column(ARRAY(String))
    periodos = db.Column(ARRAY(String))  # ['romano', 'medieval', ...]
    tecnicas = db.Column(ARRAY(String))  # ['estratigrafia', 'ceramica', ...]
    
    # Experiencia
    anios_experiencia = db.Column(Integer)
    proyectos_participados = db.Column(Integer, default=0)
    publicaciones = relationship("Publicacion")
    
    # Certificaciones
    certificaciones = db.Column(JSONB)  # [{'nombre': 'X', 'entidad': 'Y', 'fecha': Z}]
    
    # Social
    linkedin_url = db.Column(String(200))
    orcid = db.Column(String(50))
    researchgate_url = db.Column(String(200))
    
    # Visibilidad
    perfil_publico = db.Column(Boolean, default=True)
    busqueda_empleo = db.Column(Boolean, default=False)
```

#### 7.2 Sistema de Publicaciones
```python
class Publicacion(db.Model):
    id = db.Column(UUID, primary_key=True)
    usuario_id = db.Column(UUID, ForeignKey('usuarios.id'))
    
    # Tipo
    tipo = db.Column(Enum('articulo', 'libro', 'comunicacion', 'tesis'))
    
    # Datos bibliográficos
    titulo = db.Column(String(500))
    autores = db.Column(ARRAY(String))
    revista = db.Column(String(200))
    doi = db.Column(String(100))
    isbn = db.Column(String(20))
    anio = db.Column(Integer)
    
    # Archivo
    pdf_url = db.Column(String(500))
    
    # Relación con proyectos
    yacimientos_relacionados = relationship("Yacimiento", secondary="publicacion_yacimiento")
```

#### 7.3 Sistema de Conexiones
```python
class Conexion(db.Model):
    id = db.Column(UUID, primary_key=True)
    usuario1_id = db.Column(UUID, ForeignKey('usuarios.id'))
    usuario2_id = db.Column(UUID, ForeignKey('usuarios.id'))
    
    estado = db.Column(Enum('pendiente', 'aceptada', 'rechazada'))
    fecha_solicitud = db.Column(DateTime, default=datetime.utcnow)
    fecha_respuesta = db.Column(DateTime)
    
    # Metadata
    mensaje_solicitud = db.Column(Text)
    origen = db.Column(String(50))  # 'busqueda', 'proyecto', 'sugerencia'
```

#### 7.4 Proyectos Públicos y Descubrimiento
```python
class YacimientoPublico(db.Model):
    yacimiento_id = db.Column(UUID, ForeignKey('yacimientos.id'), primary_key=True)
    
    # Visibilidad
    nivel_visibilidad = db.Column(Enum('privado', 'solo_red', 'publico'))
    
    # Información pública
    descripcion_publica = db.Column(Text)
    imagen_destacada = db.Column(String(500))
    
    # Tags para búsqueda
    tags = db.Column(ARRAY(String))
    periodo_cultural = db.Column(String(100))
    region = db.Column(String(100))
    
    # Métricas
    vistas_count = db.Column(Integer, default=0)
    likes_count = db.Column(Integer, default=0)
    compartidos_count = db.Column(Integer, default=0)
    
    # Búsqueda de colaboradores
    busca_colaboradores = db.Column(Boolean, default=False)
    roles_necesarios = db.Column(ARRAY(String))
```

**Entregables v7.0**:
- ✅ Perfiles profesionales completos
- ✅ Sistema de publicaciones
- ✅ Red de conexiones
- ✅ Proyectos públicos/descubribles
- ✅ Búsqueda avanzada de arqueólogos
- ✅ Feed de actividad

---

### **VERSIÓN 8.0 - QR Y MOVILIDAD (2-3 semanas)**
**Objetivo**: App móvil y códigos QR

#### 8.1 Generación de Códigos QR
```python
import qrcode
from io import BytesIO

class QRService:
    @staticmethod
    def generar_qr_hallazgo(hallazgo_id: UUID) -> BytesIO:
        """Genera QR que apunta a hallazgo"""
        hallazgo = Hallazgo.query.get(hallazgo_id)
        
        # URL directa al hallazgo
        url = f"https://arqueotrack.com/h/{hallazgo.codigo_acceso}"
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Agregar logo en el centro
        logo = Image.open('static/logo.png')
        logo = logo.resize((50, 50))
        
        img_w, img_h = img.size
        logo_w, logo_h = logo.size
        img.paste(logo, ((img_w - logo_w) // 2, (img_h - logo_h) // 2))
        
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return buffer
    
    @staticmethod
    def generar_etiqueta_imprimible(hallazgo_id: UUID) -> BytesIO:
        """Genera etiqueta PDF para imprimir"""
        from reportlab.lib.units import mm
        from reportlab.graphics.barcode import qr
        
        # Etiqueta 50x30mm
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=(50*mm, 30*mm))
        
        hallazgo = Hallazgo.query.get(hallazgo_id)
        
        # QR Code
        qr_code = qr.QrCodeWidget(f"https://arqueotrack.com/h/{hallazgo.codigo_acceso}")
        bounds = qr_code.getBounds()
        width = bounds[2] - bounds[0]
        height = bounds[3] - bounds[1]
        d = Drawing(45, 45, transform=[45./width,0,0,45./height,0,0])
        d.add(qr_code)
        renderPDF.draw(d, c, 2*mm, 15*mm)
        
        # Información textual
        c.setFont("Helvetica-Bold", 8)
        c.drawString(2*mm, 12*mm, hallazgo.codigo_acceso)
        c.setFont("Helvetica", 6)
        c.drawString(2*mm, 10*mm, hallazgo.tipo or '')
        c.drawString(2*mm, 8*mm, f"UE: {hallazgo.ue.numero_ue if hallazgo.ue else '-'}")
        
        c.save()
        buffer.seek(0)
        return buffer
```

#### 8.2 API REST Documentada (FastAPI opcional)
```python
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel

api = FastAPI(title="ArqueoTrack API", version="2.0")

class HallazgoResponse(BaseModel):
    id: UUID
    codigo_acceso: str
    tipo: str
    descripcion: Optional[str]
    coordenadas: dict
    
    class Config:
        orm_mode = True

@api.get("/api/v2/hallazgos/{codigo}", response_model=HallazgoResponse)
async def get_hallazgo_by_codigo(
    codigo: str,
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene hallazgo por código QR"""
    hallazgo = Hallazgo.query.filter_by(codigo_acceso=codigo).first()
    
    if not hallazgo:
        raise HTTPException(status_code=404, detail="Hallazgo no encontrado")
    
    # Verificar permisos
    if not verificar_acceso_yacimiento(hallazgo.yacimiento_id, current_user.id, 'read'):
        raise HTTPException(status_code=403, detail="Sin permiso de acceso")
    
    return hallazgo
```

**Entregables v8.0**:
- ✅ Generación QR para hallazgos
- ✅ Etiquetas imprimibles
- ✅ Lectura QR con cámara móvil
- ✅ API REST documentada
- ✅ App móvil PWA

---

### **VERSIÓN 9.0 - PRODUCCIÓN Y DEVOPS (3-4 semanas)**
**Objetivo**: Deployment profesional

#### 9.1 Infraestructura como Código (Terraform)
```hcl
# main.tf
provider "aws" {
  region = "eu-west-1"
}

# VPC
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  
  tags = {
    Name = "arqueotrack-vpc"
  }
}

# RDS PostgreSQL
resource "aws_db_instance" "postgres" {
  identifier           = "arqueotrack-db"
  engine              = "postgres"
  engine_version      = "15.3"
  instance_class      = "db.t3.medium"
  allocated_storage   = 100
  
  db_name  = "arqueotrack"
  username = var.db_username
  password = var.db_password
  
  vpc_security_group_ids = [aws_security_group.db.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name
  
  backup_retention_period = 7
  multi_az               = true
  
  tags = {
    Environment = "production"
  }
}

# ElastiCache Redis
resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "arqueotrack-cache"
  engine              = "redis"
  node_type           = "cache.t3.micro"
  num_cache_nodes     = 1
  parameter_group_name = "default.redis7"
  port                = 6379
}

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "arqueotrack-cluster"
}

# Load Balancer
resource "aws_lb" "main" {
  name               = "arqueotrack-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id
}
```

#### 9.2 CI/CD Pipeline (GitHub Actions)
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgis/postgis:15-3.3
        env:
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      
      - name: Run tests
        run: pytest --cov=app tests/
        env:
          DATABASE_URL: postgresql://postgres:test@localhost:5432/test
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  build:
    needs: test
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: eu-west-1
      
      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v1
      
      - name: Build and push Docker image
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          ECR_REPOSITORY: arqueotrack
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
      
      - name: Deploy to ECS
        run: |
          aws ecs update-service \
            --cluster arqueotrack-cluster \
            --service arqueotrack-service \
            --force-new-deployment
```

#### 9.3 Monitoreo (Prometheus + Grafana)
```python
# metrics.py
from prometheus_client import Counter, Histogram, Gauge
from flask import request
import time

# Métricas
request_count = Counter('arqueotrack_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
request_duration = Histogram('arqueotrack_request_duration_seconds', 'Request duration', ['endpoint'])
active_users = Gauge('arqueotrack_active_users', 'Currently active users')
hallazgos_count = Gauge('arqueotrack_hallazgos_total', 'Total hallazgos')

# Middleware
@app.before_request
def before_request():
    request.start_time = time.time()

@app.after_request
def after_request(response):
    request_duration.labels(endpoint=request.endpoint).observe(
        time.time() - request.start_time
    )
    request_count.labels(
        method=request.method,
        endpoint=request.endpoint,
        status=response.status_code
    ).inc()
    return response

# Actualización periódica de métricas
@celery.task
def actualizar_metricas():
    hallazgos_count.set(Hallazgo.query.count())
    active_users.set(Usuario.query.filter(
        Usuario.ultima_actividad > datetime.utcnow() - timedelta(minutes=5)
    ).count())
```

#### 9.4 Logging Centralizado (ELK Stack)
```python
# logging_config.py
import logging
from pythonjsonlogger import jsonlogger

def setup_logging(app):
    logHandler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        fmt='%(asctime)s %(levelname)s %(name)s %(message)s'
    )
    logHandler.setFormatter(formatter)
    
    app.logger.addHandler(logHandler)
    app.logger.setLevel(logging.INFO)
    
    # Contexto adicional
    @app.before_request
    def log_request():
        app.logger.info('Request started', extra={
            'method': request.method,
            'path': request.path,
            'ip': request.remote_addr,
            'user_id': current_user.id if current_user.is_authenticated else None
        })
```

**Entregables v9.0**:
- ✅ Infraestructura AWS/GCP automatizada
- ✅ CI/CD pipeline completo
- ✅ Monitoreo con dashboards
- ✅ Logging centralizado
- ✅ Backups automatizados
- ✅ Disaster recovery plan

---

## 🔧 Tecnologías Finales

### Backend
- **Framework**: Flask 3.x + Blueprints
- **Base de Datos**: PostgreSQL 15 + PostGIS
- **ORM**: SQLAlchemy 2.x + GeoAlchemy2
- **Migraciones**: Alembic
- **Cache**: Redis 7.x
- **Tasks**: Celery + Redis
- **API**: Flask-RESTX (Swagger docs)

### Frontend
- **Templates**: Jinja2 + Alpine.js
- **Maps**: Leaflet + Turf.js
- **Charts**: Chart.js + D3.js
- **Real-time**: Socket.IO

### DevOps
- **Containerización**: Docker + Docker Compose
- **Orquestación**: Kubernetes (opcional) / ECS
- **CI/CD**: GitHub Actions
- **IaC**: Terraform
- **Monitoreo**: Prometheus + Grafana
- **Logging**: ELK Stack

### Cloud
- **Primary**: AWS (RDS, ElastiCache, S3, CloudFront, ECS)
- **Alternative**: Neon (PostgreSQL) + Vercel + Cloudflare

---

## 📊 Métricas de Éxito

### Técnicas
- ✅ Code Coverage >80%
- ✅ API Response Time <200ms (p95)
- ✅ Page Load Time <1s
- ✅ Uptime >99.9%
- ✅ Zero data loss

### Funcionales
- ✅ 1,000+ instituciones registradas
- ✅ 10,000+ usuarios activos
- ✅ 100,000+ hallazgos catalogados
- ✅ 5,000+ proyectos activos
- ✅ Exportación de 10,000+ informes/mes

---

## 🚀 Roadmap de Implementación

### Mes 1-2: Fundamentos (v1.0)
- Semana 1-2: Blueprints + PostgreSQL
- Semana 3-4: Tests + Docker

### Mes 3-4: Institucionalización (v2.0)
- Semana 5-6: Modelo institucional
- Semana 7-8: Campañas + Roles

### Mes 5-7: Arqueología Científica (v3.0)
- Semana 9-11: UEs + Matriz Harris
- Semana 12-14: Muestras + Planimetría

### Mes 8-9: Rendimiento (v4.0)
- Semana 15-16: Celery + Redis
- Semana 17-18: Optimizaciones DB + CDN

### Mes 10-11: Versionado (v5.0)
- Semana 19-20: Sistema versionado
- Semana 21-22: WebSockets + Conflictos

### Mes 12: Informes (v6.0)
- Semana 23-24: PDFs + Exportación

### Mes 13-15: Red Social (v7.0)
- Semana 25-27: Perfiles + Publicaciones
- Semana 28-30: Conexiones + Proyectos públicos

### Mes 16: QR (v8.0)
- Semana 31-32: QR + API REST

### Mes 17-19: Producción (v9.0)
- Semana 33-35: IaC + CI/CD
- Semana 36-38: Monitoreo + Logging

---

## 💰 Estimación de Costos (Producción)

### Infraestructura AWS (Mensual)
- **RDS PostgreSQL**: $150 (db.t3.medium)
- **ElastiCache Redis**: $50 (cache.t3.micro)
- **ECS Fargate**: $100 (2 tasks)
- **S3 + CloudFront**: $50
- **Load Balancer**: $20
- **Backups**: $30
- **Total**: ~$400/mes

### Desarrollo (Por versión)
- **v1.0**: 160 horas @ $50/h = $8,000
- **v2.0**: 240 horas = $12,000
- **v3.0**: 320 horas = $16,000
- **v4.0**: 240 horas = $12,000
- **v5.0**: 240 horas = $12,000
- **v6.0**: 160 horas = $8,000
- **v7.0**: 320 horas = $16,000
- **v8.0**: 160 horas = $8,000
- **v9.0**: 240 horas = $12,000

**Total Desarrollo**: ~$104,000

---

## ✅ Checklist de Entrega por Versión

Cada versión debe incluir:

1. ✅ **Código refactorizado** y funcional
2. ✅ **Tests** con >70% coverage
3. ✅ **Documentación** técnica actualizada
4. ✅ **Changelog** detallado
5. ✅ **Scripts de migración** de datos
6. ✅ **Variables de entorno** documentadas
7. ✅ **Docker Compose** actualizado
8. ✅ **Demo deployada** en staging
9. ✅ **Performance benchmarks**
10. ✅ **Security audit** básico

---

## 📚 Documentación Requerida

### Por Versión
- **README.md**: Instrucciones de instalación
- **CHANGELOG.md**: Cambios detallados
- **MIGRATION.md**: Guía de migración
- **API.md**: Endpoints documentados

### Técnica
- **Arquitectura**: Diagramas C4
- **Base de Datos**: Schema ER
- **Deployment**: Runbook
- **Troubleshooting**: Guía de resolución

---

Este plan es **ambicioso pero realista**, con **entregas incrementales** que permiten validar cada fase antes de continuar. Cada versión es **deployable en producción**, garantizando valor continuo.

**¿Comenzamos con la v1.0?** 🚀
