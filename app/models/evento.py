"""
Modelo de Evento para ArqueoTrack
"""

from datetime import datetime
from app import db


class Evento(db.Model):
    """
    Modelo de evento en la línea de tiempo del yacimiento
    """
    
    __tablename__ = 'eventos'
    
    # Identificación
    id = db.Column(db.Integer, primary_key=True)
    
    # Referencias
    yacimiento_id = db.Column(db.Integer, db.ForeignKey('yacimientos.id'), nullable=False, index=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    fase_id = db.Column(db.Integer, db.ForeignKey('fases_proyecto.id'))
    hallazgo_id = db.Column(db.Integer, db.ForeignKey('hallazgos.id'))
    sector_id = db.Column(db.Integer, db.ForeignKey('sectores.id'))
    
    # Información del evento
    tipo = db.Column(db.String(50), nullable=False)  # hallazgo, reunion, cambio_estado, analisis, decision, visita, entrega, otro
    titulo = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Detalles opcionales
    ubicacion = db.Column(db.String(200))
    participantes = db.Column(db.Text)
    resultados = db.Column(db.Text)
    prioridad = db.Column(db.String(20), default='media')  # baja, media, alta, urgente
    estado_evento = db.Column(db.String(20), default='pendiente')  # pendiente, en_progreso, completado, cancelado
    
    # Relaciones
    yacimiento = db.relationship(
        'Yacimiento',
        back_populates='eventos'
    )
    
    usuario = db.relationship(
        'Usuario',
        back_populates='eventos'
    )
    
    fase = db.relationship(
        'FaseProyecto',
        back_populates='eventos'
    )
    
    hallazgo = db.relationship(
        'Hallazgo',
        back_populates='eventos'
    )
    
    sector = db.relationship(
        'Sector',
        back_populates='eventos'
    )
    
    # Índices
    __table_args__ = (
        db.Index('idx_eventos_yacimiento_fecha', 'yacimiento_id', 'fecha'),
        db.Index('idx_eventos_tipo', 'tipo'),
    )
    
    def __repr__(self):
        return f'<Evento {self.titulo}>'
    
    def to_dict(self, include_relations=False):
        """Serializa el evento a diccionario"""
        data = {
            'id': self.id,
            'tipo': self.tipo,
            'titulo': self.titulo,
            'descripcion': self.descripcion,
            'fecha': self.fecha.isoformat(),
            'ubicacion': self.ubicacion,
            'prioridad': self.prioridad,
            'estado_evento': self.estado_evento,
            'yacimiento_id': self.yacimiento_id,
            'usuario_id': self.usuario_id,
            'fase_id': self.fase_id,
            'hallazgo_id': self.hallazgo_id,
            'sector_id': self.sector_id
        }
        
        if include_relations:
            data.update({
                'yacimiento_nombre': self.yacimiento.nombre if self.yacimiento else None,
                'usuario_nombre': self.usuario.nombre_completo if self.usuario else None,
                'fase_nombre': self.fase.nombre if self.fase else None,
                'hallazgo_codigo': self.hallazgo.codigo_acceso if self.hallazgo else None,
                'sector_nombre': self.sector.nombre if self.sector else None
            })
        
        return data
