"""
Modelo de Fase de Proyecto para ArqueoTrack
"""

from datetime import datetime
from app import db


class FaseProyecto(db.Model):
    """
    Modelo de fase en el proceso de excavación arqueológica
    """
    
    __tablename__ = 'fases_proyecto'
    
    # Identificación
    id = db.Column(db.Integer, primary_key=True)
    yacimiento_id = db.Column(db.Integer, db.ForeignKey('yacimientos.id'), nullable=False, index=True)
    responsable_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    
    # Información básica
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    estado = db.Column(db.String(50), default='planificada')  # planificada, en_curso, finalizada
    orden = db.Column(db.Integer, default=0)
    
    # Fechas
    fecha_inicio = db.Column(db.Date)
    fecha_fin = db.Column(db.Date)
    
    # Detalles de planificación
    objetivos = db.Column(db.Text)
    metodologia = db.Column(db.Text)
    recursos_necesarios = db.Column(db.Text)
    resultados_esperados = db.Column(db.Text)
    presupuesto = db.Column(db.Float)
    equipo_participante = db.Column(db.Text)
    notas = db.Column(db.Text)
    
    # Metadata
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relaciones
    yacimiento = db.relationship(
        'Yacimiento',
        back_populates='fases'
    )
    
    responsable = db.relationship(
        'Usuario',
        back_populates='fases_responsable',
        foreign_keys=[responsable_id]
    )
    
    eventos = db.relationship(
        'Evento',
        back_populates='fase',
        cascade='all, delete-orphan',
        lazy='dynamic'
    )
    
    # Índices
    __table_args__ = (
        db.Index('idx_fases_yacimiento_orden', 'yacimiento_id', 'orden'),
    )
    
    def __repr__(self):
        return f'<FaseProyecto {self.nombre}>'
    
    @property
    def esta_activa(self):
        """Verifica si la fase está actualmente en curso"""
        return self.estado == 'en_curso'
    
    @property
    def esta_completada(self):
        """Verifica si la fase está finalizada"""
        return self.estado == 'finalizada'
    
    def to_dict(self, include_relations=False):
        """Serializa la fase a diccionario"""
        data = {
            'id': self.id,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'estado': self.estado,
            'orden': self.orden,
            'fecha_inicio': self.fecha_inicio.isoformat() if self.fecha_inicio else None,
            'fecha_fin': self.fecha_fin.isoformat() if self.fecha_fin else None,
            'presupuesto': self.presupuesto,
            'yacimiento_id': self.yacimiento_id,
            'responsable_id': self.responsable_id
        }
        
        if include_relations:
            data.update({
                'yacimiento_nombre': self.yacimiento.nombre if self.yacimiento else None,
                'responsable_nombre': self.responsable.nombre_completo if self.responsable else None
            })
        
        return data
