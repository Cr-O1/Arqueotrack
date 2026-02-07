"""
Modelo de Invitación para ArqueoTrack
"""

from datetime import datetime
from app import db


class Invitacion(db.Model):
    """
    Modelo de invitación para colaborar en yacimientos
    """
    
    __tablename__ = 'invitaciones'
    
    # Identificación
    id = db.Column(db.Integer, primary_key=True)
    
    # Referencias
    yacimiento_id = db.Column(db.Integer, db.ForeignKey('yacimientos.id'), nullable=False, index=True)
    invitado_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False, index=True)
    invitado_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    
    # Información de la invitación
    email = db.Column(db.String(120), nullable=False)
    rol = db.Column(db.String(50), nullable=False)  # visualizador, editor, colaborador, asistente
    mensaje = db.Column(db.Text)
    estado = db.Column(db.String(20), default='pendiente', nullable=False)  # pendiente, aceptada, rechazada, cancelada
    
    # Fechas
    fecha_envio = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    fecha_respuesta = db.Column(db.DateTime)
    
    # Relaciones
    yacimiento = db.relationship(
        'Yacimiento',
        back_populates='invitaciones'
    )
    
    invitado = db.relationship(
        'Usuario',
        back_populates='invitaciones_recibidas',
        foreign_keys=[invitado_id]
    )
    
    invitado_por = db.relationship(
        'Usuario',
        back_populates='invitaciones_enviadas',
        foreign_keys=[invitado_por_id]
    )
    
    # Índices
    __table_args__ = (
        db.Index('idx_invitaciones_yacimiento_estado', 'yacimiento_id', 'estado'),
        db.Index('idx_invitaciones_invitado_estado', 'invitado_id', 'estado'),
    )
    
    def __repr__(self):
        return f'<Invitacion {self.email} para {self.yacimiento.nombre if self.yacimiento else "?"}>'
    
    @property
    def esta_pendiente(self):
        """Verifica si la invitación está pendiente"""
        return self.estado == 'pendiente'
    
    @property
    def esta_aceptada(self):
        """Verifica si la invitación fue aceptada"""
        return self.estado == 'aceptada'
    
    def aceptar(self):
        """Acepta la invitación"""
        self.estado = 'aceptada'
        self.fecha_respuesta = datetime.utcnow()
    
    def rechazar(self):
        """Rechaza la invitación"""
        self.estado = 'rechazada'
        self.fecha_respuesta = datetime.utcnow()
    
    def cancelar(self):
        """Cancela la invitación"""
        self.estado = 'cancelada'
        self.fecha_respuesta = datetime.utcnow()
    
    def to_dict(self, include_relations=False):
        """Serializa la invitación a diccionario"""
        data = {
            'id': self.id,
            'email': self.email,
            'rol': self.rol,
            'estado': self.estado,
            'fecha_envio': self.fecha_envio.isoformat(),
            'fecha_respuesta': self.fecha_respuesta.isoformat() if self.fecha_respuesta else None,
            'yacimiento_id': self.yacimiento_id,
            'invitado_id': self.invitado_id,
            'invitado_por_id': self.invitado_por_id
        }
        
        if include_relations:
            data.update({
                'yacimiento_nombre': self.yacimiento.nombre if self.yacimiento else None,
                'invitado_nombre': self.invitado.nombre_completo if self.invitado else None,
                'invitado_por_nombre': self.invitado_por.nombre_completo if self.invitado_por else None
            })
        
        return data
