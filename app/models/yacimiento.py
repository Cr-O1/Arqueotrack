"""
Modelo de Yacimiento para ArqueoTrack - SQLite Version
"""

from datetime import datetime
from app import db


class Yacimiento(db.Model):
    """
    Modelo de yacimiento arqueológico
    """

    __tablename__ = 'yacimientos'

    # Identificación
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False, index=True)

    # Información básica
    nombre = db.Column(db.String(200), nullable=False)
    ubicacion = db.Column(db.String(300))
    descripcion = db.Column(db.Text)

    # Coordenadas (sin geometría PostGIS)
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    polygon_geojson = db.Column(db.Text)  # GeoJSON del polígono (almacenado como texto)
    area_m2 = db.Column(db.Float)  # Área en metros cuadrados
    altitud_media = db.Column(db.Float)

    # Gestión del proyecto
    responsable = db.Column(db.String(100))
    fecha_inicio = db.Column(db.Date)
    fecha_fin = db.Column(db.Date)

    # Metadata
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    propietario = db.relationship(
        'Usuario',
        back_populates='yacimientos'
    )

    hallazgos = db.relationship(
        'Hallazgo',
        back_populates='yacimiento',
        cascade='all, delete-orphan',
        lazy='dynamic'
    )

    sectores = db.relationship(
        'Sector',
        back_populates='yacimiento',
        cascade='all, delete-orphan',
        lazy='dynamic'
    )

    fases = db.relationship(
        'FaseProyecto',
        back_populates='yacimiento',
        cascade='all, delete-orphan',
        lazy='dynamic',
        order_by='FaseProyecto.orden'
    )

    eventos = db.relationship(
        'Evento',
        back_populates='yacimiento',
        cascade='all, delete-orphan',
        lazy='dynamic',
        order_by='Evento.fecha.desc()'
    )

    invitaciones = db.relationship(
        'Invitacion',
        back_populates='yacimiento',
        cascade='all, delete-orphan',
        lazy='dynamic'
    )

    # Índices
    __table_args__ = (
        db.Index('idx_yacimientos_user_fecha', 'user_id', 'fecha_creacion'),
    )

    def __repr__(self):
        return f'<Yacimiento {self.nombre}>'

    @property
    def esta_activo(self):
        """Verifica si el yacimiento está actualmente en excavación"""
        return self.fecha_fin is None

    @property
    def total_hallazgos(self):
        """Retorna el total de hallazgos del yacimiento"""
        return self.hallazgos.count()

    @property
    def hallazgos_con_foto(self):
        """Retorna el total de hallazgos con foto"""
        from app.models.hallazgo import Hallazgo
        return self.hallazgos.filter(Hallazgo.foto != None, Hallazgo.foto != '').count()

    @property
    def total_sectores(self):
        """Retorna el total de sectores del yacimiento"""
        return self.sectores.count()

    @property
    def total_fases(self):
        """Retorna el total de fases del yacimiento"""
        return self.fases.count()

    def obtener_rol_usuario(self, user_id):
        """
        Obtiene el rol de un usuario en este yacimiento

        Args:
            user_id: ID del usuario

        Returns:
            str: Rol del usuario ('propietario', 'colaborador', etc.) o None
        """
        if self.user_id == user_id:
            return 'propietario'

        from app.models.invitacion import Invitacion
        invitacion = Invitacion.query.filter_by(
            yacimiento_id=self.id,
            invitado_id=user_id,
            estado='aceptada'
        ).first()

        return invitacion.rol if invitacion else None

    def to_dict(self, include_relations=False):
        """
        Serializa el yacimiento a diccionario

        Args:
            include_relations: Si True, incluye hallazgos, sectores, etc.
        """
        data = {
            'id': self.id,
            'nombre': self.nombre,
            'ubicacion': self.ubicacion,
            'descripcion': self.descripcion,
            'lat': self.lat,
            'lng': self.lng,
            'area_m2': self.area_m2,
            'altitud_media': self.altitud_media,
            'responsable': self.responsable,
            'fecha_inicio': self.fecha_inicio.isoformat() if self.fecha_inicio else None,
            'fecha_fin': self.fecha_fin.isoformat() if self.fecha_fin else None,
            'esta_activo': self.esta_activo,
            'fecha_creacion': self.fecha_creacion.isoformat(),
            'propietario_id': self.user_id
        }

        if include_relations:
            data.update({
                'total_hallazgos': self.total_hallazgos,
                'total_sectores': self.total_sectores,
                'total_fases': self.total_fases
            })

        return data