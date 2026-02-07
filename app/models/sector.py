"""
Modelo de Sector para ArqueoTrack - SQLite Version
"""

from datetime import datetime
from app import db


class Sector(db.Model):
    """
    Modelo de sector dentro de un yacimiento
    Los sectores permiten dividir un yacimiento en áreas específicas
    """

    __tablename__ = 'sectores'

    # Identificación
    id = db.Column(db.Integer, primary_key=True)
    yacimiento_id = db.Column(db.Integer, db.ForeignKey('yacimientos.id'), nullable=False, index=True)

    # Información básica
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    color = db.Column(db.String(20), default='#6366F1')

    # Ubicación (sin geometría PostGIS)
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    polygon_geojson = db.Column(db.Text)  # GeoJSON del polígono del sector (almacenado como texto)
    area = db.Column(db.Float)  # Área en m²

    # Metadata
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relaciones
    yacimiento = db.relationship(
        'Yacimiento',
        back_populates='sectores'
    )

    hallazgos = db.relationship(
        'Hallazgo',
        back_populates='sector',
        cascade='all, delete-orphan',
        lazy='dynamic'
    )

    eventos = db.relationship(
        'Evento',
        back_populates='sector',
        lazy='dynamic'
    )

    # Índices
    __table_args__ = (
        db.Index('idx_sectores_yacimiento', 'yacimiento_id'),
    )

    def __repr__(self):
        return f'<Sector {self.nombre}>'

    @property
    def total_hallazgos(self):
        """Retorna el total de hallazgos en este sector"""
        return self.hallazgos.count()

    def to_dict(self, include_relations=False):
        """Serializa el sector a diccionario"""
        data = {
            'id': self.id,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'color': self.color,
            'lat': self.lat,
            'lng': self.lng,
            'area': self.area,
            'yacimiento_id': self.yacimiento_id,
            'fecha_creacion': self.fecha_creacion.isoformat()
        }

        if include_relations:
            data.update({
                'total_hallazgos': self.total_hallazgos,
                'yacimiento_nombre': self.yacimiento.nombre if self.yacimiento else None
            })

        return data