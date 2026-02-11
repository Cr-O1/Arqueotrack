from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, DateField, SelectField, TextAreaField, FloatField, DateTimeField, BooleanField, FileField
from wtforms.validators import InputRequired, Length, Email, EqualTo, ValidationError, Optional, DataRequired
from app.models.user import Usuario
from app.utils import (
    ESTADOS_CONSERVACION,
    FASES_PREDEFINIDAS,
    OCUPACIONES,
    TIPOS_EVENTO,
    TIPOS_HALLAZGO,
)

class RegistroForm(FlaskForm):
    nombre_usuario = StringField('Nombre de Usuario', validators=[InputRequired(), Length(min=4, max=20)])
    nombre = StringField('Nombre', validators=[InputRequired(), Length(max=100)])
    apellidos = StringField('Apellidos', validators=[InputRequired(), Length(max=100)])
    correo_electronico = StringField('Correo Electrónico', validators=[InputRequired(), Email(), Length(max=120)])
    fecha_nacimiento = DateField('Fecha de Nacimiento', validators=[InputRequired()])
    ocupacion = SelectField('Ocupación', choices=OCUPACIONES, validators=[Optional()])
    contraseña = PasswordField('Contraseña', validators=[InputRequired(), Length(min=10)])
    confirmar_contraseña = PasswordField('Confirmar Contraseña', validators=[InputRequired(), EqualTo('contraseña')])
    enviar = SubmitField('Registrarse')

    def validate_nombre_usuario(self, nombre_usuario):
        usuario = Usuario.query.filter_by(nombre_usuario=nombre_usuario.data).first()
        if usuario:
            raise ValidationError('Nombre de usuario ya existe.')

    def validate_correo_electronico(self, correo_electronico):
        usuario = Usuario.query.filter_by(email=correo_electronico.data).first()
        if usuario:
            raise ValidationError('Correo electrónico ya registrado.')

class LoginForm(FlaskForm):
    correo_electronico = StringField('Correo Electrónico', validators=[InputRequired(), Email()])
    contraseña = PasswordField('Contraseña', validators=[InputRequired()])
    enviar = SubmitField('Iniciar Sesión')

class YacimientoForm(FlaskForm):
    nombre = StringField('Nombre', validators=[InputRequired()])
    ubicacion = StringField('Ubicación')
    descripcion = TextAreaField('Descripción')
    fecha_inicio = DateField('Fecha Inicio', validators=[Optional()])
    fecha_fin = DateField('Fecha Fin', validators=[Optional()])
    altitud_media = FloatField('Altitud Media (m)', validators=[Optional()])
    lat = FloatField('Latitud', validators=[Optional()])
    lng = FloatField('Longitud', validators=[Optional()])
    polygon_geojson = TextAreaField('GeoJSON Polígono', validators=[Optional()])
    area = FloatField('Área (m²)', validators=[Optional()])
    responsable = StringField('Responsable', validators=[Optional()])
    submit = SubmitField('Guardar')

class EditarProcesoYacimientoForm(FlaskForm):
    responsable = StringField('Responsable')
    fecha_inicio = DateField('Fecha Inicio', validators=[Optional()])
    fecha_fin = DateField('Fecha Fin', validators=[Optional()])
    esta_activo = BooleanField('Activo')
    submit = SubmitField('Guardar')

class HallazgoForm(FlaskForm):
    tipo = SelectField('Tipo', choices=TIPOS_HALLAZGO, validators=[InputRequired()])
    material = StringField('Material')
    datacion = StringField('Datación')
    dimensiones = StringField('Dimensiones')
    peso = FloatField('Peso (g)', validators=[Optional()])
    estado_conservacion = SelectField('Estado Conservación', choices=ESTADOS_CONSERVACION)
    proceso_extraccion = TextAreaField('Proceso de Extracción', validators=[Optional()], render_kw={'rows': 4, 'placeholder': 'Describe el método de extracción...'})
    destino = StringField('Destino/Repositorio',  validators=[Optional()], render_kw={'placeholder': 'Ej: Museo Arqueológico, Laboratorio...'})
    descripcion = TextAreaField('Descripción')
    lat = FloatField('Latitud', validators=[Optional()])
    lng = FloatField('Longitud', validators=[Optional()])
    fecha = DateField('Fecha Hallazgo', validators=[Optional()])
    notas = TextAreaField('Notas', validators=[Optional()], render_kw={'rows': 3})
    sector_id = SelectField('Sector', coerce=int)
    foto = FileField('Foto')
    ubicacion = StringField('Ubicación/Referencia', validators=[Optional(), Length(max=200)], render_kw={'placeholder': 'Ej: "Sector A, cuadrícula 5x10" o coordenadas'})
    altitud = FloatField('Altitud (m s.n.m.)', validators=[Optional()], render_kw={'step': '0.1', 'placeholder': 'Ej: 650.5'})
    submit = SubmitField('Guardar')

class SectorForm(FlaskForm):
    nombre = StringField('Nombre', validators=[InputRequired()])
    descripcion = TextAreaField('Descripción')
    color = StringField('Color', default='#6366F1')
    lat = FloatField('Latitud', validators=[Optional()])
    lng = FloatField('Longitud', validators=[Optional()])
    polygon_geojson = TextAreaField('GeoJSON Polígono', validators=[Optional()])
    area = FloatField('Área (m²)', validators=[Optional()])
    submit = SubmitField('Guardar')

class FaseForm(FlaskForm):
    nombre = SelectField('Nombre', choices=FASES_PREDEFINIDAS, validators=[InputRequired()])
    descripcion = TextAreaField('Descripción')
    estado = SelectField('Estado', choices=[('planificada', 'Planificada'), ('en_curso', 'En Curso'), ('finalizada', 'Finalizada')])
    fecha_inicio = DateField('Fecha Inicio', validators=[Optional()])
    fecha_fin = DateField('Fecha Fin', validators=[Optional()])
    objetivos = TextAreaField('Objetivos', validators=[Optional()], render_kw={'rows': 3})
    metodologia = TextAreaField('Metodología', validators=[Optional()], render_kw={'rows': 3})
    recursos_necesarios = TextAreaField('Recursos Necesarios', validators=[Optional()], render_kw={'rows': 3})
    resultados_esperados = TextAreaField('Resultados Esperados', validators=[Optional()], render_kw={'rows': 3})
    presupuesto = FloatField('Presupuesto', validators=[Optional()])
    equipo_participante = TextAreaField('Equipo Participante', validators=[Optional()], render_kw={'rows': 3})
    notas = TextAreaField('Notas', validators=[Optional()], render_kw={'rows': 3})

    submit = SubmitField('Guardar')

class EventoForm(FlaskForm):
    tipo = SelectField('Tipo', choices=TIPOS_EVENTO)
    titulo = StringField('Título', validators=[InputRequired()])
    descripcion = TextAreaField('Descripción', validators=[InputRequired()])
    fecha = DateTimeField(
        'Fecha',
        validators=[DataRequired()],
        format='%Y-%m-%dT%H:%M'
    )
    fase_id = SelectField('Fase', coerce=int)
    hallazgo_id = SelectField('Hallazgo', coerce=int)
    sector_id = SelectField('Sector', coerce=int)
    prioridad = SelectField('Prioridad', choices=[('baja', 'Baja'), ('media', 'Media'), ('alta', 'Alta'), ('urgente', 'Urgente')])
    estado_evento = SelectField('Estado', choices=[('pendiente', 'Pendiente'), ('en_progreso', 'En Progreso'), ('completado', 'Completado'), ('cancelado', 'Cancelado')])
    participantes = TextAreaField('Participantes', validators=[Optional()], render_kw={'rows': 3})
    resultados = TextAreaField('Resultados', validators=[Optional()], render_kw={'rows': 3})
    submit = SubmitField('Guardar')

class InvitacionForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired(), Email()])
    rol = SelectField('Rol', choices=[('visualizador', 'Visualizador'), ('editor', 'Editor'), ('colaborador', 'Colaborador'), ('asistente', 'Asistente')])
    mensaje = TextAreaField('Mensaje')
    submit = SubmitField('Enviar')

class BuscarCodigoForm(FlaskForm):
    codigo = StringField('Código', validators=[InputRequired(), Length(min=10, max=10)])
    submit = SubmitField('Buscar')
