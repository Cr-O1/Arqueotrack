"""
Modelo de Comentario para ArqueoTrack
"""

from datetime import datetime
from app import db


class Comentario(db.Model):
    """
    Modelo de comentario en hallazgos
    """
    
    __tablename__ = 'comentarios'
    
    # Identificación
    id = db.Column(db.Integer, primary_key=True)
    
    # Referencias
    hallazgo_id = db.Column(db.Integer, db.ForeignKey('hallazgos.id'), nullable=False, index=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    
    # Contenido
    texto = db.Column(db.Text, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relaciones
    hallazgo = db.relationship(
        'Hallazgo',
        back_populates='comentarios'
    )
    
    usuario = db.relationship(
        'Usuario',
        back_populates='comentarios'
    )
    
    # Índices
    __table_args__ = (
        db.Index('idx_comentarios_hallazgo_fecha', 'hallazgo_id', 'fecha'),
    )
    
    def __repr__(self):
        return f'<Comentario #{self.id} en Hallazgo #{self.hallazgo_id}>'
    
    def to_dict(self, include_relations=False):
        """Serializa el comentario a diccionario"""
        data = {
            'id': self.id,
            'texto': self.texto,
            'fecha': self.fecha.isoformat(),
            'hallazgo_id': self.hallazgo_id,
            'usuario_id': self.usuario_id
        }
        
        if include_relations:
            data.update({
                'usuario_nombre': self.usuario.nombre_completo if self.usuario else None,
                'hallazgo_codigo': self.hallazgo.codigo_acceso if self.hallazgo else None
            })
        
        return data
