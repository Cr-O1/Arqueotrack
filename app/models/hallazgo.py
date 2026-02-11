"""
Modelo de Hallazgo para ArqueoTrack - SQLite Version
"""

from datetime import datetime
from app import db


class Hallazgo(db.Model):
    """
    Modelo de hallazgo arqueológico
    """

    __tablename__ = 'hallazgos'

    # Identificación
    id = db.Column(db.Integer, primary_key=True)
    codigo_acceso = db.Column(db.String(10), unique=True, nullable=False, index=True)

    # Referencias
    user_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False, index=True)
    yacimiento_id = db.Column(db.Integer, db.ForeignKey('yacimientos.id'), index=True)
    sector_id = db.Column(db.Integer, db.ForeignKey('sectores.id'), index=True)
    encontrado_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))

    # Clasificación
    tipo = db.Column(db.String(100))
    material = db.Column(db.String(100))
    datacion = db.Column(db.String(100))

    # Descripción
    descripcion = db.Column(db.Text)
    notas = db.Column(db.Text)

    # Ubicación (sin geometría PostGIS)
    ubicacion = db.Column(db.String(200))
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    altitud = db.Column(db.Float)

    # Características físicas
    dimensiones = db.Column(db.String(100))
    peso = db.Column(db.Float)  # En gramos
    estado_conservacion = db.Column(db.String(50))

    # Documentación
    foto = db.Column(db.String(200))
    fecha = db.Column(db.Date)

    # Procesamiento
    proceso_extraccion = db.Column(db.Text)
    destino = db.Column(db.String(200))

    # Metadata
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    propietario = db.relationship(
        'Usuario',
        back_populates='hallazgos',
        foreign_keys=[user_id]
    )

    encontrado_por = db.relationship(
        'Usuario',
        back_populates='hallazgos_encontrados',
        foreign_keys=[encontrado_por_id]
    )

    yacimiento = db.relationship(
        'Yacimiento',
        back_populates='hallazgos'
    )

    sector = db.relationship(
        'Sector',
        back_populates='hallazgos'
    )

    comentarios = db.relationship(
        'Comentario',
        back_populates='hallazgo',
        cascade='all, delete-orphan',
        lazy='dynamic',
        order_by='Comentario.fecha.desc()'
    )

    eventos = db.relationship(
        'Evento',
        back_populates='hallazgo',
        lazy='dynamic'
    )

    # Índices
    __table_args__ = (
        db.Index('idx_hallazgos_yacimiento_fecha', 'yacimiento_id', 'fecha'),
        db.Index('idx_hallazgos_tipo', 'tipo'),
    )

    def __repr__(self):
        return f'<Hallazgo {self.codigo_acceso}>'

    @property
    def total_comentarios(self):
        """Retorna el total de comentarios del hallazgo"""
        return self.comentarios.count()

    @property
    def tiene_foto(self):
        """Verifica si el hallazgo tiene foto"""
        return self.foto is not None and self.foto != ''

    def to_dict(self, include_relations=False):
        """
        Serializa el hallazgo a diccionario

        Args:
            include_relations: Si True, incluye comentarios, etc.
        """
        data = {
            'id': self.id,
            'codigo_acceso': self.codigo_acceso,
            'tipo': self.tipo,
            'material': self.material,
            'datacion': self.datacion,
            'descripcion': self.descripcion,
            'ubicacion': self.ubicacion,
            'lat': self.lat,
            'lng': self.lng,
            'altitud': self.altitud,
            'dimensiones': self.dimensiones,
            'peso': self.peso,
            'estado_conservacion': self.estado_conservacion,
            'proceso_extraccion': self.proceso_extraccion,
            'destino': self.destino,
            'notas': self.notas,
            'fecha': self.fecha.isoformat() if self.fecha else None,
            'tiene_foto': self.tiene_foto,
            'foto_url': f'/uploads/{self.foto}' if self.foto else None,
            'yacimiento_id': self.yacimiento_id,
            'sector_id': self.sector_id,
            'fecha_registro': self.fecha_registro.isoformat()
        }

        if include_relations:
            data.update({
                'total_comentarios': self.total_comentarios,
                'yacimiento_nombre': self.yacimiento.nombre if self.yacimiento else None,
                'sector_nombre': self.sector.nombre if self.sector else None,
                'encontrado_por': self.encontrado_por.nombre_completo if self.encontrado_por else None
            })

        return data