from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, DateField, SelectField, TextAreaField, FloatField, DateTimeField, BooleanField, FileField
from wtforms.validators import InputRequired, Length, Email, EqualTo, ValidationError, Optional
from app.models.user import Usuario

class RegistroForm(FlaskForm):
    nombre_usuario = StringField('Nombre de Usuario', validators=[InputRequired(), Length(min=4, max=20)])
    nombre = StringField('Nombre', validators=[InputRequired(), Length(max=100)])
    apellidos = StringField('Apellidos', validators=[InputRequired(), Length(max=100)])
    correo_electronico = StringField('Correo Electrónico', validators=[InputRequired(), Email(), Length(max=120)])
    fecha_nacimiento = DateField('Fecha de Nacimiento', validators=[InputRequired()])
    ocupacion = StringField('Ocupación', validators=[Optional(), Length(max=50)])
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
    tipo = StringField('Tipo', validators=[InputRequired()])
    material = StringField('Material')
    datacion = StringField('Datación')
    dimensiones = StringField('Dimensiones')
    peso = FloatField('Peso (g)', validators=[Optional()])
    estado_conservacion = SelectField('Estado Conservación', choices=[('bueno', 'Bueno'), ('regular', 'Regular'), ('malo', 'Malo')])
    descripcion = TextAreaField('Descripción')
    lat = FloatField('Latitud', validators=[Optional()])
    lng = FloatField('Longitud', validators=[Optional()])
    fecha = DateField('Fecha Hallazgo', validators=[Optional()])
    sector_id = SelectField('Sector', coerce=int)
    foto = FileField('Foto')
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
    nombre = StringField('Nombre', validators=[InputRequired()])
    descripcion = TextAreaField('Descripción')
    estado = SelectField('Estado', choices=[('planificada', 'Planificada'), ('en_curso', 'En Curso'), ('finalizada', 'Finalizada')])
    fecha_inicio = DateField('Fecha Inicio', validators=[Optional()])
    fecha_fin = DateField('Fecha Fin', validators=[Optional()])
    submit = SubmitField('Guardar')

class EventoForm(FlaskForm):
    tipo = SelectField('Tipo', choices=[('hallazgo', 'Hallazgo'), ('reunion', 'Reunión'), ('analisis', 'Análisis'), ('cambio_estado', 'Cambio Estado'), ('decision', 'Decisión'), ('visita', 'Visita'), ('entrega', 'Entrega'), ('otro', 'Otro')])
    titulo = StringField('Título', validators=[InputRequired()])
    descripcion = TextAreaField('Descripción')
    fecha = DateTimeField('Fecha', validators=[Optional()])
    fase_id = SelectField('Fase', coerce=int)
    hallazgo_id = SelectField('Hallazgo', coerce=int)
    sector_id = SelectField('Sector', coerce=int)
    submit = SubmitField('Guardar')

class InvitacionForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired(), Email()])
    rol = SelectField('Rol', choices=[('visualizador', 'Visualizador'), ('editor', 'Editor'), ('colaborador', 'Colaborador'), ('asistente', 'Asistente')])
    mensaje = TextAreaField('Mensaje')
    submit = SubmitField('Enviar')

class BuscarCodigoForm(FlaskForm):
    codigo = StringField('Código', validators=[InputRequired(), Length(min=10, max=10)])
    submit = SubmitField('Buscar')
