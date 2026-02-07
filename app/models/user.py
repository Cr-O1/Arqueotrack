from datetime import datetime
from flask_login import UserMixin
from app import bcrypt, db


class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuarios'

    # Identificación
    id = db.Column(db.Integer, primary_key=True)
    nombre_usuario = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(200), nullable=False)

    # Información personal
    nombre = db.Column(db.String(100), nullable=False)
    apellidos = db.Column(db.String(100), nullable=False)
    fecha_nacimiento = db.Column(db.Date, nullable=False)
    ocupacion = db.Column(db.String(50))

    # Metadata
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    activo = db.Column(db.Boolean, default=True)
    rol = db.Column(db.String(20), default='arqueologo')

    # Relaciones
    yacimientos = db.relationship('Yacimiento', back_populates='propietario', lazy='dynamic')
    hallazgos = db.relationship('Hallazgo', back_populates='propietario', lazy='dynamic', foreign_keys='Hallazgo.user_id')
    hallazgos_encontrados = db.relationship('Hallazgo', back_populates='encontrado_por', lazy='dynamic', foreign_keys='Hallazgo.encontrado_por_id')
    eventos = db.relationship('Evento', back_populates='usuario', lazy='dynamic')
    comentarios = db.relationship('Comentario', back_populates='usuario', lazy='dynamic')
    fases_responsable = db.relationship('FaseProyecto', back_populates='responsable', lazy='dynamic')
    invitaciones_enviadas = db.relationship('Invitacion', back_populates='invitado_por', lazy='dynamic', foreign_keys='Invitacion.invitado_por_id')
    invitaciones_recibidas = db.relationship('Invitacion', back_populates='invitado', lazy='dynamic', foreign_keys='Invitacion.invitado_id')

    def set_password(self, password):
        """Hash de contraseña"""
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        """Verificar contraseña"""
        return bcrypt.check_password_hash(self.password_hash, password)

    @property
    def nombre_completo(self):
        """Nombre completo"""
        return f"{self.nombre} {self.apellidos}"

    def has_permission(self, yacimiento_id, permission):
        """Verificar permiso en yacimiento"""
        from app.models.invitacion import Invitacion
        from app.models.yacimiento import Yacimiento

        yacimiento = Yacimiento.query.get(yacimiento_id)
        if not yacimiento:
            return False, None

        if self.id == yacimiento.user_id:
            return True, 'propietario'

        invitacion = Invitacion.query.filter_by(
            yacimiento_id=yacimiento_id,
            invitado_id=self.id,
            estado='aceptada'
        ).first()

        if not invitacion:
            return False, None

        # Permisos por rol (definir según necesidades)
        ROLES_PERMISOS = {
            'visualizador': {'view'},
            'editor': {'view', 'edit'},
            'colaborador': {'view', 'edit', 'create'},
            'asistente': {'view', 'edit', 'create', 'manage'}
        }
        permisos = ROLES_PERMISOS.get(invitacion.rol, set())
        tiene_permiso = permission in permisos or 'manage' in permisos

        return tiene_permiso, invitacion.rol

    def to_dict(self):
        """Serializa el usuario a diccionario"""
        return {
            'id': self.id,
            'nombre_usuario': self.nombre_usuario,
            'email': self.email,
            'nombre': self.nombre,
            'apellidos': self.apellidos,
            'nombre_completo': self.nombre_completo,
            'ocupacion': self.ocupacion,
            'fecha_registro': self.fecha_registro.isoformat() if self.fecha_registro else None,
            'activo': self.activo,
            'rol': self.rol
        }
