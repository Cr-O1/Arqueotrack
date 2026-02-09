import os
import string
import random
import logging
from datetime import datetime
from functools import wraps
from flask import send_from_directory, Flask, request, render_template, redirect, url_for, flash, abort, jsonify
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from flask_login import login_user, UserMixin, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from wtforms import StringField, PasswordField, SubmitField, DateField, SelectField, TextAreaField, FloatField, DateTimeField
from wtforms.validators import InputRequired, Length, ValidationError, Email, Optional
from flask_bcrypt import Bcrypt
from sqlalchemy.orm import joinedload
from dotenv import load_dotenv
from urllib.parse import urlparse, urljoin

load_dotenv()

#CONFIGURACION

class Config:
    DEBUG = os.getenv("FLASK_DEBUG", False)
    SECRET_KEY = os.getenv("SECRET_KEY")
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY debe estar establecida en las variables de entorno")
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.getenv('SQLITE_DATABASE_PATH', 'database.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = "uploads/"
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ITEMS_PER_PAGE = 20

app = Flask(__name__)
app.config.from_object(Config)
if app.config["SECRET_KEY"] == "dev-secret-key-change-in-production":
    logging.warning("âš ï¸ Using default SECRET_KEY. Change in production!")

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

#EXTENSIONES

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
csrf = CSRFProtect(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "iniciar_sesion"
login_manager.login_message = "Por favor, inicia sesión para acceder a esta página."


#LOGGING

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

#OCUPACIONES, TIPOS, ESTADOS Y ROLES

OCUPACIONES = [
    ("arqueologo", "Arqueólogo"), ("restaurador", "Restaurador"),
    ("topografo", "Topógrafo"), ("geologo", "Geólogo"),
    ("antropologo", "Antropólogo"), ("historiador", "Historiador"),
    ("fotografo", "Fotógrafo"), ("dibujante", "Dibujante Técnico"),
    ("peon", "Peón"), ("estudiante", "Estudiante"),
    ("voluntario", "Voluntario"), ("admin", "Administrador"),
    ("otro", "Otro"),
]

TIPOS_HALLAZGO = [
    ("ceramica", "Cerámica"), ("hueso", "Hueso"), ("metal", "Metal"),
    ("piedra", "Piedra"), ("estructura", "Estructura"), ("moneda", "Moneda"),
    ("herramienta", "Herramienta"), ("joya", "Joya"), ("textil", "Textil"),
    ("vidrio", "Vidrio"), ("organico", "Material Orgánico"), ("otro", "Otro"),
]

TIPOS_EVENTO = [
    ("hallazgo", "Hallazgo"), ("reunion", "Reunión"),
    ("cambio_estado", "Cambio de Estado"), ("analisis", "Análisis"),
    ("decision", "Decisión"), ("visita", "Visita"),
    ("entrega", "Entrega"), ("otro", "Otro"),
]

ESTADOS_CONSERVACION = [
    ("excelente", "Excelente"), ("bueno", "Bueno"),
    ("regular", "Regular"), ("malo", "Malo"),
    ("muy_malo", "Muy Malo"), ("fragmentado", "Fragmentado"),
]

FASES_PREDEFINIDAS = [
    ("valoracion", "Valoración Inicial"),
    ("planificacion", "Planificación"),
    ("excavacion", "Excavación"),
    ("analisis", "Análisis"),
    ("conservacion", "Conservación"),
    ("documentacion", "Documentación"),
    ("restauracion", "Restauración"),
    ("exposicion", "Exposición"),
    ("cierre", "Cierre del Proyecto"),
]

ROLES_PERMISOS = {
    "visualizador": {"read"},
    "editor": {"read", "edit"},
    "colaborador": {"read", "edit", "create"},
    "asistente": {"read", "edit", "create", "delete"},
    "propietario": {"read", "edit", "create", "delete", "manage"}
}

#HELPERS

def archivo_permitido(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]

def generar_codigo_acceso() -> str:
    caracteres = string.ascii_uppercase + string.digits
    while True:
        codigo = "".join(random.choices(caracteres, k=8))
        if not Hallazgo.query.filter_by(codigo_acceso=codigo).first():
            return codigo

def obtener_rol_usuario(yacimiento_id: int, user_id: int) -> str:
    yacimiento = db.session.get(Yacimiento, yacimiento_id)
    if not yacimiento:
        return None
    if yacimiento.user_id == user_id:
        return "propietario"

    invitacion = Invitacion.query.filter_by(
        yacimiento_id=yacimiento_id, invitado_id=user_id, estado="aceptada"
    ).first()
    return invitacion.rol if invitacion else None

def verificar_acceso_yacimiento(yacimiento_id: int, permission: str = "read") -> tuple:
    if not current_user.is_authenticated:
        return False, None

    rol = obtener_rol_usuario(yacimiento_id, current_user.id)
    if not rol:
        return False, None

    permisos = ROLES_PERMISOS.get(rol, set())
    tiene_permiso = permission in permisos or "manage" in permisos
    return tiene_permiso, rol

def obtener_yacimiento_con_acceso(yacimiento_id: int, permission: str = "read"):
    yacimiento = db.session.get(Yacimiento, yacimiento_id)
    if not yacimiento:
        abort(404)

    tiene_acceso, rol = verificar_acceso_yacimiento(yacimiento_id, permission)
    if not tiene_acceso:
        abort(403)

    return yacimiento, rol

#MODELOS

class Usuario(db.Model, UserMixin):
    __tablename__ = "usuario"

    id = db.Column(db.Integer, primary_key=True)
    nombre_usuario = db.Column(db.String(80), nullable=False, unique=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellidos = db.Column(db.String(100), nullable=False)
    correo_electronico = db.Column(db.String(120), nullable=False, unique=True)
    fecha_nacimiento = db.Column(db.Date, nullable=False)
    ocupacion = db.Column(db.String(50))
    contraseña = db.Column(db.String(200), nullable=False)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)

    yacimientos = db.relationship("Yacimiento", backref="propietario", cascade="all, delete-orphan")
    hallazgos = db.relationship("Hallazgo", backref="propietario", cascade="all, delete-orphan", foreign_keys="Hallazgo.user_id")
    comentarios = db.relationship("Comentario", backref="usuario", cascade="all, delete-orphan")
    invitaciones_recibidas = db.relationship("Invitacion", backref="invitado", foreign_keys="Invitacion.invitado_id")

class Yacimiento(db.Model):
    __tablename__ = "yacimientos"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    nombre = db.Column(db.String(200), nullable=False)
    ubicacion = db.Column(db.String(300))
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    altitud_media = db.Column(db.Float)
    responsable = db.Column(db.String(100))
    fecha_inicio = db.Column(db.Date)
    fecha_fin = db.Column(db.Date)
    descripcion = db.Column(db.Text)
    polygon_geojson = db.Column(db.Text)
    hallazgos = db.relationship("Hallazgo", backref="yacimiento", cascade="all, delete-orphan")
    fases = db.relationship("FaseProyecto", backref="yacimiento", cascade="all, delete-orphan")
    sectores = db.relationship("Sector", backref="yacimiento", cascade="all, delete-orphan")
    eventos = db.relationship("Evento", backref="yacimiento", cascade="all, delete-orphan")
    invitaciones = db.relationship("Invitacion", backref="yacimiento", cascade="all, delete-orphan")
    area_m2 = db.Column(db.Float)

class Sector(db.Model):
    __tablename__ = "sectores"

    id = db.Column(db.Integer, primary_key=True)
    yacimiento_id = db.Column(db.Integer, db.ForeignKey("yacimientos.id"), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    area = db.Column(db.Float)
    color = db.Column(db.String(20), default="#6366F1")
    polygon_geojson = db.Column(db.Text)
    hallazgos = db.relationship("Hallazgo", backref="sector", cascade="all, delete-orphan")
    eventos = db.relationship("Evento", backref="sector", cascade="all, delete-orphan")


class FaseProyecto(db.Model):
    __tablename__ = "fases_proyecto"

    id = db.Column(db.Integer, primary_key=True)
    yacimiento_id = db.Column(db.Integer, db.ForeignKey("yacimientos.id"), nullable=False)
    responsable_id = db.Column(db.Integer, db.ForeignKey("usuario.id"))
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    fecha_inicio = db.Column(db.Date)
    fecha_fin = db.Column(db.Date)
    estado = db.Column(db.String(50), default="planificada")
    objetivos = db.Column(db.Text)
    metodologia = db.Column(db.Text)
    recursos_necesarios = db.Column(db.Text)
    resultados_esperados = db.Column(db.Text)
    presupuesto = db.Column(db.Float)
    equipo_participante = db.Column(db.Text)
    notas = db.Column(db.Text)
    orden = db.Column(db.Integer, default=0)

    responsable = db.relationship("Usuario", backref="fases_responsable")
    eventos = db.relationship("Evento", backref="fase", cascade="all, delete-orphan")

class Evento(db.Model):
    __tablename__ = "eventos"

    id = db.Column(db.Integer, primary_key=True)
    yacimiento_id = db.Column(db.Integer, db.ForeignKey("yacimientos.id"), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    fase_id = db.Column(db.Integer, db.ForeignKey("fases_proyecto.id"))
    hallazgo_id = db.Column(db.Integer, db.ForeignKey("hallazgos.id"))
    sector_id = db.Column(db.Integer, db.ForeignKey("sectores.id"))
    tipo = db.Column(db.String(50), nullable=False)
    titulo = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    ubicacion = db.Column(db.String(200))
    participantes = db.Column(db.Text)
    resultados = db.Column(db.Text)
    prioridad = db.Column(db.String(20), default="media")
    estado_evento = db.Column(db.String(20), default="pendiente")

    usuario = db.relationship("Usuario", backref="eventos_usuario")
    hallazgo = db.relationship("Hallazgo", backref="eventos")

class Hallazgo(db.Model):
    __tablename__ = "hallazgos"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    yacimiento_id = db.Column(db.Integer, db.ForeignKey("yacimientos.id"))
    sector_id = db.Column(db.Integer, db.ForeignKey("sectores.id"))
    tipo = db.Column(db.String(100))
    descripcion = db.Column(db.Text)
    ubicacion = db.Column(db.String(200))
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    altitud = db.Column(db.Float)
    foto = db.Column(db.String(200))
    notas = db.Column(db.Text)
    fecha = db.Column(db.Date)
    estado_conservacion = db.Column(db.String(50))
    codigo_acceso = db.Column(db.String(10), unique=True, nullable=False)
    proceso_extraccion = db.Column(db.Text)
    destino = db.Column(db.String(200))
    datacion = db.Column(db.String(100))
    material = db.Column(db.String(100))
    dimensiones = db.Column(db.String(100))
    peso = db.Column(db.Float)
    encontrado_por_id = db.Column(db.Integer, db.ForeignKey("usuario.id"))

    comentarios = db.relationship("Comentario", backref="hallazgo", cascade="all, delete-orphan")
    encontrado_por = db.relationship("Usuario", foreign_keys=[encontrado_por_id], backref="hallazgos_encontrados")

class Comentario(db.Model):
    __tablename__ = "comentarios"

    id = db.Column(db.Integer, primary_key=True)
    hallazgo_id = db.Column(db.Integer, db.ForeignKey("hallazgos.id"), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    texto = db.Column(db.Text, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

class Invitacion(db.Model):
    __tablename__ = "invitaciones"

    id = db.Column(db.Integer, primary_key=True)
    yacimiento_id = db.Column(db.Integer, db.ForeignKey("yacimientos.id"), nullable=False)
    invitado_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    invitado_por_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    rol = db.Column(db.String(50), nullable=False)
    mensaje = db.Column(db.Text)
    estado = db.Column(db.String(20), default="pendiente")
    fecha_envio = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_respuesta = db.Column(db.DateTime)

    invitado_por = db.relationship("Usuario", foreign_keys=[invitado_por_id], backref="invitaciones_enviadas")

#FLASKFORMS

class FormularioRegistro(FlaskForm):
    nombre = StringField("Nombre", validators=[InputRequired()])
    apellidos = StringField("Apellidos", validators=[InputRequired()])
    nombre_usuario = StringField("Nombre de Usuario", validators=[InputRequired(), Length(min=4, max=20)])
    correo_electronico = StringField("Correo", validators=[InputRequired(), Email()])
    fecha_nacimiento = DateField("Fecha de Nacimiento", validators=[InputRequired()])
    ocupacion = SelectField("Ocupación", validators=[InputRequired()], choices=OCUPACIONES)
    contraseña = PasswordField("Contraseña", validators=[InputRequired(), Length(min=10)])
    enviar = SubmitField("Registrar")

    def validate_nombre_usuario(self, nombre_usuario):
        if Usuario.query.filter_by(nombre_usuario=nombre_usuario.data).first():
            raise ValidationError("Ese nombre de usuario ya existe")

    def validate_correo_electronico(self, correo_electronico):
        if Usuario.query.filter_by(correo_electronico=correo_electronico.data).first():
            raise ValidationError("Ya existe una cuenta con ese correo")

class FormularioInicioSesion(FlaskForm):
    correo_electronico = StringField("Correo", validators=[InputRequired()])
    contraseña = PasswordField("Contraseña", validators=[InputRequired()])
    enviar = SubmitField("Iniciar sesión")

class FormularioYacimiento(FlaskForm):
    nombre = StringField("Nombre del Yacimiento", validators=[InputRequired()])
    ubicacion = StringField("Ubicación")
    descripcion = TextAreaField("Descripción")
    lat = FloatField("Latitud", validators=[Optional()])
    lng = FloatField("Longitud", validators=[Optional()])
    altitud_media = FloatField("Altitud Media (m)", validators=[Optional()])
    responsable = StringField("Responsable")
    fecha_inicio = DateField("Fecha de Inicio", validators=[Optional()])
    fecha_fin = DateField("Fecha de Fin", validators=[Optional()])
    enviar = SubmitField("Guardar Yacimiento")
    def validate_fecha_fin(self, fecha_fin):
        if fecha_fin.data and self.fecha_inicio.data:
            if fecha_fin.data < self.fecha_inicio.data:
                raise ValidationError("La fecha de fin no puede ser anterior a la de inicio")

class FormularioHallazgo(FlaskForm):
    tipo = SelectField("Tipo de Hallazgo", validators=[InputRequired()], choices=TIPOS_HALLAZGO)
    descripcion = TextAreaField("Descripción")
    ubicacion = StringField("Ubicación Específica")
    sector_id = SelectField("Sector", coerce=int, validators=[Optional()])
    lat = FloatField("Latitud", validators=[Optional()])
    lng = FloatField("Longitud", validators=[Optional()])
    altitud = FloatField("Altitud (m)", validators=[Optional()])
    fecha = DateField("Fecha del Descubrimiento", validators=[Optional()])
    estado_conservacion = SelectField("Estado de Conservación", validators=[Optional()], choices=ESTADOS_CONSERVACION)
    material = StringField("Material Principal")
    dimensiones = StringField("Dimensiones")
    peso = FloatField("Peso (gramos)", validators=[Optional()])
    datacion = StringField("Datación/Periodo")
    proceso_extraccion = TextAreaField("Proceso de Extracción")
    destino = StringField("Destino o Uso Posterior")
    notas = TextAreaField("Notas Adicionales")
    enviar = SubmitField("Guardar Hallazgo")

class FormularioEvento(FlaskForm):
    tipo = SelectField("Tipo de Evento", validators=[InputRequired()], choices=TIPOS_EVENTO)
    titulo = StringField("Título", validators=[InputRequired()])
    descripcion = TextAreaField("Descripción", validators=[InputRequired()])
    fecha = DateTimeField("Fecha y Hora", format="%Y-%m-%dT%H:%M", validators=[InputRequired()])
    ubicacion = StringField("Ubicación del Evento")
    participantes = TextAreaField("Participantes")
    resultados = TextAreaField("Resultados Obtenidos")
    prioridad = SelectField("Prioridad", choices=[("baja", "Baja"), ("media", "Media"), ("alta", "Alta"), ("urgente", "Urgente")])
    estado_evento = SelectField("Estado", choices=[("pendiente", "Pendiente"), ("en_progreso", "En Progreso"), ("completado", "Completado"), ("cancelado", "Cancelado")])
    fase_id = SelectField("Fase Relacionada", coerce=int, validators=[Optional()])
    hallazgo_id = SelectField("Hallazgo Relacionado", coerce=int, validators=[Optional()])
    sector_id = SelectField("Sector Relacionado", coerce=int, validators=[Optional()])
    enviar = SubmitField("Registrar Evento")

class FormularioSector(FlaskForm):
    nombre = StringField("Código/Nombre del Sector", validators=[InputRequired()])
    descripcion = TextAreaField("Descripción")
    lat = FloatField("Latitud Central", validators=[Optional()])
    lng = FloatField("Longitud Central", validators=[Optional()])
    area = FloatField("Ãrea (mÂ²)", validators=[Optional()])
    color = StringField("Color en Mapa")
    enviar = SubmitField("Guardar Sector")

class FormularioFase(FlaskForm):
    nombre = SelectField("Nombre de la Fase", validators=[InputRequired()], choices=FASES_PREDEFINIDAS)
    descripcion = TextAreaField("Descripción de la Fase")
    fecha_inicio = DateField("Fecha de Inicio", validators=[Optional()])
    fecha_fin = DateField("Fecha de Fin", validators=[Optional()])
    estado = SelectField("Estado", choices=[("planificada", "Planificada"), ("en_curso", "En Curso"), ("finalizada", "Finalizada")])
    objetivos = TextAreaField("Objetivos Específicos")
    metodologia = TextAreaField("Metodología")
    recursos_necesarios = TextAreaField("Recursos Necesarios")
    resultados_esperados = TextAreaField("Resultados Esperados")
    presupuesto = FloatField("Presupuesto Estimado (â‚¬)", validators=[Optional()])
    equipo_participante = TextAreaField("Equipo Participante")
    notas = TextAreaField("Notas Adicionales")
    enviar = SubmitField("Guardar Fase")

class FormularioInvitacion(FlaskForm):
    email = StringField("Correo Electrónico", validators=[InputRequired(), Email()])
    rol = SelectField("Rol en el Proyecto", validators=[InputRequired()], 
                     choices=[("visualizador", "Visualizador"), ("editor", "Editor"), 
                             ("colaborador", "Colaborador"), ("asistente", "Asistente")])
    mensaje = TextAreaField("Mensaje Personalizado")
    enviar = SubmitField("Enviar Invitación")

    def validate_email(self, email):
        usuario = Usuario.query.filter_by(correo_electronico=email.data).first()
        if not usuario:
            raise ValidationError("No existe un usuario con ese correo")

class FormularioComentario(FlaskForm):
    texto = TextAreaField("Comentario", validators=[InputRequired()])
    enviar = SubmitField("Publicar Comentario")

#RUTAS AUTH

@login_manager.user_loader
def cargar_usuario(id):
    return db.session.get(Usuario, int(id))

@app.route("/")
def portada():
    if current_user.is_authenticated:
        return redirect(url_for("inicio"))
    return render_template("portada.html")

@app.route("/registro", methods=["GET", "POST"])
def registro():
    if current_user.is_authenticated:
        return redirect(url_for("inicio"))

    formulario = FormularioRegistro()
    if formulario.validate_on_submit():
        contraseña_hash = bcrypt.generate_password_hash(formulario.contraseña.data).decode("utf-8")
        nuevo_usuario = Usuario(
            nombre_usuario=formulario.nombre_usuario.data,
            nombre=formulario.nombre.data,
            apellidos=formulario.apellidos.data,
            correo_electronico=formulario.correo_electronico.data,
            fecha_nacimiento=formulario.fecha_nacimiento.data,
            ocupacion=formulario.ocupacion.data,
            contraseña=contraseña_hash
        )
        db.session.add(nuevo_usuario)
        db.session.commit()
        logger.info(f"Nuevo usuario: {nuevo_usuario.nombre_usuario}")
        flash("Â¡Cuenta creada exitosamente!", "success")
        return redirect(url_for("iniciar_sesion"))

    return render_template("registro.html", formulario=formulario)

@app.route("/iniciar-sesion", methods=["GET", "POST"])
def iniciar_sesion():
    if current_user.is_authenticated:
        return redirect(url_for("inicio"))

    formulario = FormularioInicioSesion()
    if formulario.validate_on_submit():
        usuario = Usuario.query.filter_by(correo_electronico=formulario.correo_electronico.data).first()

        if usuario and bcrypt.check_password_hash(usuario.contraseña, formulario.contraseña.data):
            login_user(usuario)
            logger.info(f"Login: {usuario.nombre_usuario}")
            def is_safe_url(target):
                ref_url = urlparse(request.host_url)
                test_url = urlparse(urljoin(request.host_url, target))
                return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc
            next_page = request.args.get("next")
            if next_page and is_safe_url(next_page):
                return redirect(next_page)
            return redirect(next_page or url_for("inicio"))

        flash("Credenciales inválidas", "error")

    return render_template("iniciar_sesion.html", formulario=formulario)

@app.route("/cerrar-sesion")
@login_required
def cerrar_sesion():
    logger.info(f"Logout: {current_user.nombre_usuario}")
    logout_user()
    flash("Has cerrado sesión correctamente", "success")
    return redirect(url_for("portada"))

#RUTAS INICIO Y PERFIL

@app.route("/inicio")
@login_required
def inicio():
    yacimientos_propios = Yacimiento.query.filter_by(user_id=current_user.id).all()
    invitaciones = Invitacion.query.filter_by(
        invitado_id=current_user.id, estado="aceptada"
    ).options(joinedload(Invitacion.yacimiento)).all()

    yacimientos_colaborando = [inv.yacimiento for inv in invitaciones]
    todos = yacimientos_propios + yacimientos_colaborando

    stats = {
        "total_hallazgos": sum(len(y.hallazgos) for y in todos),
        "yacimientos_activos": sum(1 for y in yacimientos_propios if not y.fecha_fin),
        "yacimientos_finalizados": sum(1 for y in yacimientos_propios if y.fecha_fin)
    }

    yacimientos_json = [
        {
            'id': y.id,
            'nombre': y.nombre,
            'ubicacion': y.ubicacion,
            'lat': y.lat,
            'lng': y.lng
        }
        for y in todos if y.lat and y.lng
    ]

    return render_template("inicio.html", yacimientos=yacimientos_propios,
                          yacimientos_colaborando=yacimientos_colaborando,
                          yacimientos_json=yacimientos_json,
                          **stats)

@app.route("/perfil")
@login_required
def perfil():
    stats = {
        "total_yacimientos": Yacimiento.query.filter_by(user_id=current_user.id).count(),
        "total_hallazgos": Hallazgo.query.filter_by(user_id=current_user.id).count(),
        "total_comentarios": Comentario.query.filter_by(usuario_id=current_user.id).count(),
        "hallazgos_encontrados": Hallazgo.query.filter_by(encontrado_por_id=current_user.id).count()
    }
    return render_template("perfil.html", usuario=current_user, **stats)

@app.route("/eliminar_cuenta", methods=["POST"])
@login_required
def eliminar_cuenta():
    usuario = db.session.get(Usuario, current_user.id)
    if usuario:
        logger.info(f"Cuenta eliminada: {usuario.nombre_usuario}")
        logout_user()
        db.session.delete(usuario)
        db.session.commit()
        flash("Tu cuenta ha sido eliminada", "success")
        return redirect(url_for("portada"))

    flash("Error al eliminar la cuenta", "error")
    return redirect(url_for("perfil"))

#RUTAS YACIMIENTOS

@app.route("/nuevo_yacimiento", methods=["GET", "POST"])
@login_required
def nuevo_yacimiento():
    formulario = FormularioYacimiento()
    if formulario.validate_on_submit():
        polygon_geojson = request.form.get('polygon_geojson')
        area_m2 = request.form.get('area_m2')

        yac = Yacimiento(
            user_id=current_user.id,
            nombre=formulario.nombre.data,
            ubicacion=formulario.ubicacion.data,
            descripcion=formulario.descripcion.data,
            lat=formulario.lat.data,
            lng=formulario.lng.data,
            altitud_media=formulario.altitud_media.data,
            responsable=formulario.responsable.data,
            fecha_inicio=formulario.fecha_inicio.data,
            fecha_fin=formulario.fecha_fin.data,
            polygon_geojson=polygon_geojson if polygon_geojson else None,
            area_m2=float(area_m2) if area_m2 else None
        )
        db.session.add(yac)
        db.session.flush()

        evento = Evento(
            tipo="decision", titulo=f'Yacimiento "{yac.nombre}" creado',
            descripcion=f"Registrado en el sistema",
            yacimiento_id=yac.id, usuario_id=current_user.id
        )
        db.session.add(evento)
        db.session.commit()

        logger.info(f"Yacimiento: {yac.nombre}")
        flash("Â¡Yacimiento registrado!", "success")
        return redirect(url_for("detalle_yacimiento", id=yac.id))

    return render_template("yacimientos/nuevo.html", formulario=formulario)

@app.route("/yacimiento/<int:id>")
@login_required
def detalle_yacimiento(id):
    yacimiento, rol = obtener_yacimiento_con_acceso(id, "read")
    permisos = ROLES_PERMISOS.get(rol, set())

    stats = {
        "total_hallazgos": len(yacimiento.hallazgos),
        "hallazgos_con_foto": sum(1 for h in yacimiento.hallazgos if h.foto),
        "total_sectores": len(yacimiento.sectores),
        "total_fases": len(yacimiento.fases),
        "rol_usuario": rol,
        "es_propietario": rol == "propietario",
        "puede_editar": "edit" in permisos,
        "puede_crear": "create" in permisos,
        "puede_eliminar": "delete" in permisos,
        "puede_gestionar": "manage" in permisos
    }

    return render_template("yacimientos/detalle.html", yacimiento=yacimiento, **stats)

@app.route("/editar_yacimiento/<int:id>", methods=["GET", "POST"])
@login_required
def editar_yacimiento(id):
    yacimiento, _ = obtener_yacimiento_con_acceso(id, "edit")

    formulario = FormularioYacimiento()
    if formulario.validate_on_submit():
        # Obtener datos del polígono y área si existen
        polygon_geojson = request.form.get('polygon_geojson')
        area_m2 = request.form.get('area_m2')

        yacimiento.nombre = formulario.nombre.data
        yacimiento.ubicacion = formulario.ubicacion.data
        yacimiento.descripcion = formulario.descripcion.data
        yacimiento.lat = formulario.lat.data
        yacimiento.lng = formulario.lng.data
        yacimiento.altitud_media = formulario.altitud_media.data
        yacimiento.responsable = formulario.responsable.data
        yacimiento.fecha_inicio = formulario.fecha_inicio.data
        yacimiento.fecha_fin = formulario.fecha_fin.data
        yacimiento.polygon_geojson = polygon_geojson if polygon_geojson else None
        yacimiento.area_m2 = float(area_m2) if area_m2 else None

        db.session.commit()
        logger.info(f"Yacimiento actualizado: {yacimiento.nombre}")
        flash("Actualizado correctamente", "success")
        return redirect(url_for("detalle_yacimiento", id=id))

    if request.method == "GET":
        formulario.nombre.data = yacimiento.nombre
        formulario.ubicacion.data = yacimiento.ubicacion
        formulario.descripcion.data = yacimiento.descripcion
        formulario.lat.data = yacimiento.lat
        formulario.lng.data = yacimiento.lng
        formulario.altitud_media.data = yacimiento.altitud_media
        formulario.responsable.data = yacimiento.responsable
        formulario.fecha_inicio.data = yacimiento.fecha_inicio
        formulario.fecha_fin.data = yacimiento.fecha_fin

    return render_template("yacimientos/editar.html", formulario=formulario, yacimiento=yacimiento)

@app.route("/eliminar_yacimiento/<int:id>", methods=["POST"])
@login_required
def eliminar_yacimiento(id):
    yacimiento, _ = obtener_yacimiento_con_acceso(id, "delete")
    db.session.delete(yacimiento)
    db.session.commit()
    logger.info(f"Yacimiento eliminado: {yacimiento.nombre}")
    flash("Eliminado correctamente", "success")
    return redirect(url_for("inicio"))

# CORREGIDO: Nueva ruta para proceso del yacimiento
@app.route("/proceso_yacimiento/<int:id>")
@login_required
def proceso_yacimiento(id):
    yacimiento, rol = obtener_yacimiento_con_acceso(id, "read")
    fases = FaseProyecto.query.filter_by(yacimiento_id=id).order_by(FaseProyecto.orden).all()

    permisos = ROLES_PERMISOS.get(rol, set())
    hallazgos_con_foto = sum(1 for h in yacimiento.hallazgos if h.foto)

    return render_template("yacimientos/proceso.html",
                          yacimiento=yacimiento,
                          fases=fases,
                          hallazgos_con_foto=hallazgos_con_foto,
                          puede_editar="edit" in permisos,
                          puede_crear="create" in permisos)

# CORREGIDO: Nueva ruta para editar proceso
@app.route("/editar_proceso_yacimiento/<int:id>", methods=["GET", "POST"])
@login_required
def editar_proceso_yacimiento(id):
    yacimiento, _ = obtener_yacimiento_con_acceso(id, "edit")

    if request.method == "POST":
        yacimiento.responsable = request.form.get("responsable")
        fecha_inicio = request.form.get("fecha_inicio")
        fecha_fin = request.form.get("fecha_fin")

        if fecha_inicio:
            yacimiento.fecha_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
        if fecha_fin:
            yacimiento.fecha_fin = datetime.strptime(fecha_fin, "%Y-%m-%d").date()

        db.session.commit()
        flash("Proceso actualizado correctamente", "success")
        return redirect(url_for("proceso_yacimiento", id=id))

    return render_template("yacimientos/editar_proceso.html", yacimiento=yacimiento)

#RUTAS HALLAZGOS

@app.route("/nuevo_hallazgo/<int:yacimiento_id>", methods=["GET", "POST"])
@login_required
def nuevo_hallazgo(yacimiento_id):
    yacimiento, _ = obtener_yacimiento_con_acceso(yacimiento_id, "create")

    formulario = FormularioHallazgo()
    sectores = Sector.query.filter_by(yacimiento_id=yacimiento_id).all()
    formulario.sector_id.choices = [(0, "Sin sector")] + [(s.id, s.nombre) for s in sectores]

    if formulario.validate_on_submit():
        foto_filename = None
        if "foto" in request.files:
            foto = request.files["foto"]
            if foto.filename and archivo_permitido(foto.filename):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                nombre = secure_filename(foto.filename)
                foto_filename = f"{timestamp}_{nombre}"
                foto.save(os.path.join(app.config["UPLOAD_FOLDER"], foto_filename))

        hallazgo = Hallazgo(
            user_id=current_user.id,
            yacimiento_id=yacimiento_id,
            sector_id=formulario.sector_id.data if formulario.sector_id.data != 0 else None,
            tipo=formulario.tipo.data,
            descripcion=formulario.descripcion.data,
            ubicacion=formulario.ubicacion.data,
            lat=formulario.lat.data,
            lng=formulario.lng.data,
            altitud=formulario.altitud.data,
            foto=foto_filename,
            notas=formulario.notas.data,
            fecha=formulario.fecha.data,
            estado_conservacion=formulario.estado_conservacion.data,
            material=formulario.material.data,
            dimensiones=formulario.dimensiones.data,
            peso=formulario.peso.data,
            datacion=formulario.datacion.data,
            proceso_extraccion=formulario.proceso_extraccion.data,
            destino=formulario.destino.data,
            encontrado_por_id=current_user.id,
            codigo_acceso=generar_codigo_acceso()
        )
        db.session.add(hallazgo)
        db.session.flush()

        evento = Evento(
            tipo="hallazgo", titulo=f"Nuevo: {hallazgo.tipo}",
            descripcion=f"Código: {hallazgo.codigo_acceso}",
            yacimiento_id=yacimiento_id, usuario_id=current_user.id,
            hallazgo_id=hallazgo.id, sector_id=hallazgo.sector_id
        )
        db.session.add(evento)
        db.session.commit()

        logger.info(f"Hallazgo: {hallazgo.codigo_acceso}")
        flash(f"Â¡Código: {hallazgo.codigo_acceso}!", "success")
        return redirect(url_for("detalle_hallazgo", id=hallazgo.id))

    return render_template("hallazgos/nuevo.html", formulario=formulario, yacimiento=yacimiento)

@app.route("/hallazgo/<int:id>")
@login_required
def detalle_hallazgo(id):
    hallazgo = db.session.get(Hallazgo, id)
    if not hallazgo:
        abort(404)

    yacimiento, _ = obtener_yacimiento_con_acceso(hallazgo.yacimiento_id, "read")

    comentarios = Comentario.query.filter_by(hallazgo_id=id).order_by(Comentario.fecha.desc()).all()
    formulario = FormularioComentario()

    return render_template("hallazgos/detalle.html", hallazgo=hallazgo,
                          comentarios=comentarios, formulario_comentario=formulario)

@app.route("/editar_hallazgo/<int:id>", methods=["GET", "POST"])
@login_required
def editar_hallazgo(id):
    hallazgo = db.session.get(Hallazgo, id)
    if not hallazgo:
        abort(404)

    yacimiento, _ = obtener_yacimiento_con_acceso(hallazgo.yacimiento_id, "edit")

    formulario = FormularioHallazgo()
    sectores = Sector.query.filter_by(yacimiento_id=hallazgo.yacimiento_id).all()
    formulario.sector_id.choices = [(0, "Sin sector")] + [(s.id, s.nombre) for s in sectores]

    if formulario.validate_on_submit():
        if "foto" in request.files:
            foto = request.files["foto"]
            if foto.filename and archivo_permitido(foto.filename):
                if hallazgo.foto:
                    old = os.path.join(app.config["UPLOAD_FOLDER"], hallazgo.foto)
                    if os.path.exists(old):
                        os.remove(old)

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                nombre = secure_filename(foto.filename)
                hallazgo.foto = f"{timestamp}_{nombre}"
                foto.save(os.path.join(app.config["UPLOAD_FOLDER"], hallazgo.foto))

        hallazgo.tipo = formulario.tipo.data
        hallazgo.descripcion = formulario.descripcion.data
        hallazgo.ubicacion = formulario.ubicacion.data
        hallazgo.sector_id = formulario.sector_id.data if formulario.sector_id.data != 0 else None
        hallazgo.lat = formulario.lat.data
        hallazgo.lng = formulario.lng.data
        hallazgo.altitud = formulario.altitud.data
        hallazgo.fecha = formulario.fecha.data
        hallazgo.estado_conservacion = formulario.estado_conservacion.data
        hallazgo.material = formulario.material.data
        hallazgo.dimensiones = formulario.dimensiones.data
        hallazgo.peso = formulario.peso.data
        hallazgo.datacion = formulario.datacion.data
        hallazgo.proceso_extraccion = formulario.proceso_extraccion.data
        hallazgo.destino = formulario.destino.data
        hallazgo.notas = formulario.notas.data

        db.session.commit()
        logger.info(f"Hallazgo actualizado: {hallazgo.codigo_acceso}")
        flash("Actualizado correctamente", "success")
        return redirect(url_for("detalle_hallazgo", id=id))

    if request.method == "GET":
        formulario.tipo.data = hallazgo.tipo
        formulario.descripcion.data = hallazgo.descripcion
        formulario.ubicacion.data = hallazgo.ubicacion
        formulario.sector_id.data = hallazgo.sector_id or 0
        formulario.lat.data = hallazgo.lat
        formulario.lng.data = hallazgo.lng
        formulario.altitud.data = hallazgo.altitud
        formulario.fecha.data = hallazgo.fecha
        formulario.estado_conservacion.data = hallazgo.estado_conservacion
        formulario.material.data = hallazgo.material
        formulario.dimensiones.data = hallazgo.dimensiones
        formulario.peso.data = hallazgo.peso
        formulario.datacion.data = hallazgo.datacion
        formulario.proceso_extraccion.data = hallazgo.proceso_extraccion
        formulario.destino.data = hallazgo.destino
        formulario.notas.data = hallazgo.notas

    return render_template("hallazgos/editar.html", formulario=formulario, hallazgo=hallazgo)

@app.route("/eliminar_hallazgo/<int:id>", methods=["POST"])
@login_required
def eliminar_hallazgo(id):
    hallazgo = db.session.get(Hallazgo, id)
    if not hallazgo:
        abort(404)

    yacimiento, _ = obtener_yacimiento_con_acceso(hallazgo.yacimiento_id, "delete")

    if hallazgo.foto:
        ruta = os.path.join(app.config["UPLOAD_FOLDER"], hallazgo.foto)
        if os.path.exists(ruta):
            os.remove(ruta)

    db.session.delete(hallazgo)
    db.session.commit()
    logger.info(f"Hallazgo eliminado: {hallazgo.codigo_acceso}")
    flash("Eliminado correctamente", "success")
    return redirect(url_for("detalle_yacimiento", id=hallazgo.yacimiento_id))

# RUTAS COMENTARIOS

@app.route("/agregar_comentario/<int:hallazgo_id>", methods=["POST"])
@login_required
def agregar_comentario(hallazgo_id):
    hallazgo = db.session.get(Hallazgo, hallazgo_id)
    if not hallazgo:
        abort(404)

    tiene_acceso, _ = verificar_acceso_yacimiento(hallazgo.yacimiento_id, "read")
    if not tiene_acceso:
        abort(403)

    formulario = FormularioComentario()
    if formulario.validate_on_submit():
        comentario = Comentario(
            hallazgo_id=hallazgo_id,
            usuario_id=current_user.id,
            texto=formulario.texto.data
        )
        db.session.add(comentario)
        db.session.commit()
        logger.info(f"Comentario: {hallazgo.codigo_acceso}")
        flash("Comentario agregado", "success")

    return redirect(url_for("detalle_hallazgo", id=hallazgo_id))

@app.route("/eliminar_comentario/<int:comentario_id>", methods=["POST"])
@login_required
def eliminar_comentario(comentario_id):
    comentario = db.session.get(Comentario, comentario_id)
    if not comentario:
        abort(404)

    if comentario.usuario_id != current_user.id and comentario.hallazgo.user_id != current_user.id:
        abort(403)

    hallazgo_id = comentario.hallazgo_id
    db.session.delete(comentario)
    db.session.commit()
    flash("Eliminado", "success")
    return redirect(url_for("detalle_hallazgo", id=hallazgo_id))

#RUTAS SECTORES

@app.route("/yacimiento/<int:yacimiento_id>/sectores")
@login_required
def listar_sectores(yacimiento_id):
    yacimiento, rol = obtener_yacimiento_con_acceso(yacimiento_id, "read")
    sectores = Sector.query.filter_by(yacimiento_id=yacimiento_id).all()

    # CORREGIDO: Agregar permisos y sectores_json
    permisos = ROLES_PERMISOS.get(rol, set())

    sectores_json = [
        {
            'id': s.id,
            'nombre': s.nombre,
            'lat': s.lat,
            'lng': s.lng,
            'color': s.color or '#6366F1',
            'area': s.area,
            'polygon_geojson': s.polygon_geojson,
            'hallazgos_count': len(s.hallazgos)
        }
        for s in sectores if s.lat and s.lng
    ]

    return render_template("sectores/listar.html", 
                          yacimiento=yacimiento, 
                          sectores=sectores,
                          sectores_json=sectores_json,
                          puede_crear="create" in permisos,
                          puede_editar="edit" in permisos,
                          puede_eliminar="delete" in permisos)

# CORREGIDO: Nueva ruta para mapa de sectores
@app.route("/yacimiento/<int:yacimiento_id>/mapa_sectores")
@login_required
def mapa_sectores(yacimiento_id):
    yacimiento, _ = obtener_yacimiento_con_acceso(yacimiento_id, "read")
    sectores = Sector.query.filter_by(yacimiento_id=yacimiento_id).all()
    hallazgos = Hallazgo.query.filter_by(yacimiento_id=yacimiento_id).all()

    sectores_json = [
        {
            'id': s.id,
            'nombre': s.nombre,
            'lat': s.lat,
            'lng': s.lng,
            'color': s.color or '#6366F1',
            'area': s.area,
            'polygon_geojson': s.polygon_geojson,
            'hallazgos_count': len(s.hallazgos)
        }
        for s in sectores
    ]

    hallazgos_json = [
        {
            'id': h.id,
            'tipo': h.tipo,
            'codigo': h.codigo_acceso,
            'lat': h.lat,
            'lng': h.lng,
            'sector_id': h.sector_id
        }
        for h in hallazgos if h.lat and h.lng
    ]

    return render_template("sectores/mapa_sectores.html",
                          yacimiento=yacimiento,
                          sectores_json=sectores_json,
                          hallazgos_json=hallazgos_json)

@app.route("/yacimiento/<int:yacimiento_id>/sectores/nuevo", methods=["GET", "POST"])
@login_required
def nuevo_sector(yacimiento_id):
    yacimiento, _ = obtener_yacimiento_con_acceso(yacimiento_id, "create")

    formulario = FormularioSector()
    if formulario.validate_on_submit():
        # Obtener datos del polígono si existe
        polygon_geojson = request.form.get('polygon_geojson')

        sector = Sector(
            yacimiento_id=yacimiento_id,
            nombre=formulario.nombre.data,
            descripcion=formulario.descripcion.data,
            lat=formulario.lat.data,
            lng=formulario.lng.data,
            area=formulario.area.data,
            color=formulario.color.data or "#6366F1",
            polygon_geojson=polygon_geojson if polygon_geojson else None
        )
        db.session.add(sector)
        db.session.flush()

        evento = Evento(
            tipo="decision", titulo=f"Sector: {sector.nombre}",
            descripcion=f"Creado en {yacimiento.nombre}",
            yacimiento_id=yacimiento_id, usuario_id=current_user.id, sector_id=sector.id
        )
        db.session.add(evento)
        db.session.commit()

        logger.info(f"Sector: {sector.nombre}")
        flash("Sector creado", "success")
        return redirect(url_for("listar_sectores", yacimiento_id=yacimiento_id))

    return render_template("sectores/nuevo.html", formulario=formulario, yacimiento=yacimiento)

@app.route("/sector/<int:sector_id>")
@login_required
def detalle_sector(sector_id):
    sector = db.session.get(Sector, sector_id)
    if not sector:
        abort(404)

    yacimiento, _ = obtener_yacimiento_con_acceso(sector.yacimiento_id, "read")
    hallazgos = Hallazgo.query.filter_by(sector_id=sector_id).all()

    return render_template("sectores/detalle.html", sector=sector, hallazgos=hallazgos)

@app.route("/sector/<int:sector_id>/editar", methods=["GET", "POST"])
@login_required
def editar_sector(sector_id):
    sector = db.session.get(Sector, sector_id)
    if not sector:
        abort(404)

    yacimiento, _ = obtener_yacimiento_con_acceso(sector.yacimiento_id, "edit")

    formulario = FormularioSector()
    if formulario.validate_on_submit():
        # Obtener datos del polígono si existe
        polygon_geojson = request.form.get('polygon_geojson')

        sector.nombre = formulario.nombre.data
        sector.descripcion = formulario.descripcion.data
        sector.lat = formulario.lat.data
        sector.lng = formulario.lng.data
        sector.area = formulario.area.data
        sector.color = formulario.color.data or "#6366F1"
        sector.polygon_geojson = polygon_geojson if polygon_geojson else None

        db.session.commit()
        logger.info(f"Sector actualizado: {sector.nombre}")
        flash("Actualizado", "success")
        return redirect(url_for("listar_sectores", yacimiento_id=sector.yacimiento_id))

    if request.method == "GET":
        formulario.nombre.data = sector.nombre
        formulario.descripcion.data = sector.descripcion
        formulario.lat.data = sector.lat
        formulario.lng.data = sector.lng
        formulario.area.data = sector.area
        formulario.color.data = sector.color

    return render_template("sectores/editar.html", formulario=formulario, sector=sector)

@app.route("/sector/<int:sector_id>/eliminar", methods=["POST"])
@login_required
def eliminar_sector(sector_id):
    sector = db.session.get(Sector, sector_id)
    if not sector:
        abort(404)

    yacimiento, _ = obtener_yacimiento_con_acceso(sector.yacimiento_id, "delete")

    if sector.hallazgos:
        flash("No se puede eliminar. Reasigna los hallazgos primero", "error")
        return redirect(url_for("listar_sectores", yacimiento_id=sector.yacimiento_id))

    evento = Evento(
        tipo="decision", titulo=f"Sector eliminado: {sector.nombre}",
        descripcion=f"Eliminado de {yacimiento.nombre}",
        yacimiento_id=sector.yacimiento_id, usuario_id=current_user.id
    )
    db.session.add(evento)
    db.session.delete(sector)
    db.session.commit()

    logger.info(f"Sector eliminado: {sector.nombre}")
    flash("Eliminado", "success")
    return redirect(url_for("listar_sectores", yacimiento_id=sector.yacimiento_id))

#RUTAS FASES

@app.route("/yacimiento/<int:yacimiento_id>/fases")
@login_required
def listar_fases(yacimiento_id):
    yacimiento, _ = obtener_yacimiento_con_acceso(yacimiento_id, "read")
    fases = FaseProyecto.query.filter_by(yacimiento_id=yacimiento_id).order_by(FaseProyecto.orden).all()
    return render_template("fases/listar.html", yacimiento=yacimiento, fases=fases)

@app.route("/yacimiento/<int:yacimiento_id>/fases/nueva", methods=["GET", "POST"])
@login_required
def nueva_fase(yacimiento_id):
    yacimiento, _ = obtener_yacimiento_con_acceso(yacimiento_id, "create")

    formulario = FormularioFase()
    if formulario.validate_on_submit():
        max_orden = db.session.query(db.func.max(FaseProyecto.orden)).filter_by(yacimiento_id=yacimiento_id).scalar() or 0

        fase = FaseProyecto(
            yacimiento_id=yacimiento_id,
            nombre=formulario.nombre.data,
            descripcion=formulario.descripcion.data,
            fecha_inicio=formulario.fecha_inicio.data,
            fecha_fin=formulario.fecha_fin.data,
            estado=formulario.estado.data,
            objetivos=formulario.objetivos.data,
            metodologia=formulario.metodologia.data,
            recursos_necesarios=formulario.recursos_necesarios.data,
            resultados_esperados=formulario.resultados_esperados.data,
            presupuesto=formulario.presupuesto.data,
            equipo_participante=formulario.equipo_participante.data,
            notas=formulario.notas.data,
            responsable_id=current_user.id,
            orden=max_orden + 1
        )
        db.session.add(fase)
        db.session.flush()

        evento = Evento(
            tipo="cambio_estado", titulo=f"Fase: {fase.nombre}",
            descripcion=f"Estado: {fase.estado}",
            yacimiento_id=yacimiento_id, usuario_id=current_user.id, fase_id=fase.id
        )
        db.session.add(evento)
        db.session.commit()

        logger.info(f"Fase: {fase.nombre}")
        flash("Fase creada", "success")
        return redirect(url_for("listar_fases", yacimiento_id=yacimiento_id))

    return render_template("fases/nueva.html", formulario=formulario, yacimiento=yacimiento)

@app.route("/fase/<int:fase_id>")
@login_required
def detalle_fase(fase_id):
    fase = db.session.get(FaseProyecto, fase_id)
    if not fase:
        abort(404)

    yacimiento, _ = obtener_yacimiento_con_acceso(fase.yacimiento_id, "read")
    eventos = Evento.query.filter_by(fase_id=fase_id).order_by(Evento.fecha.desc()).all()

    return render_template("fases/detalle.html", fase=fase, eventos=eventos)

@app.route("/fase/<int:fase_id>/editar", methods=["GET", "POST"])
@login_required
def editar_fase(fase_id):
    fase = db.session.get(FaseProyecto, fase_id)
    if not fase:
        abort(404)

    yacimiento, _ = obtener_yacimiento_con_acceso(fase.yacimiento_id, "edit")

    formulario = FormularioFase()
    if formulario.validate_on_submit():
        estado_anterior = fase.estado

        fase.nombre = formulario.nombre.data
        fase.descripcion = formulario.descripcion.data
        fase.fecha_inicio = formulario.fecha_inicio.data
        fase.fecha_fin = formulario.fecha_fin.data
        fase.estado = formulario.estado.data
        fase.objetivos = formulario.objetivos.data
        fase.metodologia = formulario.metodologia.data
        fase.recursos_necesarios = formulario.recursos_necesarios.data
        fase.resultados_esperados = formulario.resultados_esperados.data
        fase.presupuesto = formulario.presupuesto.data
        fase.equipo_participante = formulario.equipo_participante.data
        fase.notas = formulario.notas.data

        db.session.commit()

        if estado_anterior != fase.estado:
            evento = Evento(
                tipo="cambio_estado", 
                titulo=f"Cambio en fase: {fase.nombre}",
                descripcion=f"De {estado_anterior} a {fase.estado}",
                yacimiento_id=fase.yacimiento_id, usuario_id=current_user.id, fase_id=fase.id
            )
            db.session.add(evento)
            db.session.commit()

        logger.info(f"Fase actualizada: {fase.nombre}")
        flash("Actualizada", "success")
        return redirect(url_for("listar_fases", yacimiento_id=fase.yacimiento_id))

    if request.method == "GET":
        formulario.nombre.data = fase.nombre
        formulario.descripcion.data = fase.descripcion
        formulario.fecha_inicio.data = fase.fecha_inicio
        formulario.fecha_fin.data = fase.fecha_fin
        formulario.estado.data = fase.estado
        formulario.objetivos.data = fase.objetivos
        formulario.metodologia.data = fase.metodologia
        formulario.recursos_necesarios.data = fase.recursos_necesarios
        formulario.resultados_esperados.data = fase.resultados_esperados
        formulario.presupuesto.data = fase.presupuesto
        formulario.equipo_participante.data = fase.equipo_participante
        formulario.notas.data = fase.notas

    return render_template("fases/editar.html", formulario=formulario, fase=fase)

@app.route("/fase/<int:fase_id>/eliminar", methods=["POST"])
@login_required
def eliminar_fase(fase_id):
    fase = db.session.get(FaseProyecto, fase_id)
    if not fase:
        abort(404)

    yacimiento, _ = obtener_yacimiento_con_acceso(fase.yacimiento_id, "delete")
    yac_id = fase.yacimiento_id

    db.session.delete(fase)
    db.session.commit()

    logger.info(f"Fase eliminada: {fase.nombre}")
    flash("Eliminada", "success")
    return redirect(url_for("listar_fases", yacimiento_id=yac_id))

@app.route("/fase/<int:fase_id>/cambiar_orden/<string:direccion>", methods=["POST"])
@login_required
def cambiar_orden_fase(fase_id, direccion):
    fase = db.session.get(FaseProyecto, fase_id)
    if not fase:
        abort(404)

    yacimiento, _ = obtener_yacimiento_con_acceso(fase.yacimiento_id, "edit")
    yac_id = fase.yacimiento_id

    if direccion == "arriba":
        otra = FaseProyecto.query.filter(
            FaseProyecto.yacimiento_id == yac_id,
            FaseProyecto.orden < fase.orden
        ).order_by(FaseProyecto.orden.desc()).first()

        if otra:
            fase.orden, otra.orden = otra.orden, fase.orden

    elif direccion == "abajo":
        otra = FaseProyecto.query.filter(
            FaseProyecto.yacimiento_id == yac_id,
            FaseProyecto.orden > fase.orden
        ).order_by(FaseProyecto.orden.asc()).first()

        if otra:
            fase.orden, otra.orden = otra.orden, fase.orden

    db.session.commit()
    return redirect(url_for("listar_fases", yacimiento_id=yac_id))

# RUTAS EVENTOS

@app.route("/yacimiento/<int:yacimiento_id>/timeline")
@login_required
def timeline(yacimiento_id):
    yacimiento, _ = obtener_yacimiento_con_acceso(yacimiento_id, "read")

    eventos = Evento.query.filter_by(yacimiento_id=yacimiento_id).order_by(Evento.fecha.desc()).all()
    tipo_filtro = request.args.get("tipo")

    if tipo_filtro:
        eventos = [e for e in eventos if e.tipo == tipo_filtro]

    stats = {
        "total_eventos": len(eventos),
        "por_tipo": {}
    }

    for evento in Evento.query.filter_by(yacimiento_id=yacimiento_id).all():
        stats["por_tipo"][evento.tipo] = stats["por_tipo"].get(evento.tipo, 0) + 1

    return render_template("eventos/timeline.html", yacimiento=yacimiento,
                          eventos=eventos, tipo_filtro=tipo_filtro, **stats)


@app.route("/yacimiento/<int:yacimiento_id>/evento/nuevo", methods=["GET", "POST"])
@login_required
def nuevo_evento(yacimiento_id):
    yacimiento, _ = obtener_yacimiento_con_acceso(yacimiento_id, "create")

    formulario = FormularioEvento()
    fases = FaseProyecto.query.filter_by(yacimiento_id=yacimiento_id).all()
    hallazgos = Hallazgo.query.filter_by(yacimiento_id=yacimiento_id).all()
    sectores = Sector.query.filter_by(yacimiento_id=yacimiento_id).all()

    formulario.fase_id.choices = [(0, "Ninguna")] + [(f.id, f.nombre) for f in fases]
    formulario.hallazgo_id.choices = [(0, "Ninguno")] + [(h.id, h.codigo_acceso) for h in hallazgos]
    formulario.sector_id.choices = [(0, "Ninguno")] + [(s.id, s.nombre) for s in sectores]

    if formulario.validate_on_submit():
        evento = Evento(
            yacimiento_id=yacimiento_id,
            usuario_id=current_user.id,
            tipo=formulario.tipo.data,
            titulo=formulario.titulo.data,
            descripcion=formulario.descripcion.data,
            fecha=formulario.fecha.data,
            ubicacion=formulario.ubicacion.data,
            participantes=formulario.participantes.data,
            resultados=formulario.resultados.data,
            prioridad=formulario.prioridad.data,
            estado_evento=formulario.estado_evento.data,
            fase_id=formulario.fase_id.data if formulario.fase_id.data != 0 else None,
            hallazgo_id=formulario.hallazgo_id.data if formulario.hallazgo_id.data != 0 else None,
            sector_id=formulario.sector_id.data if formulario.sector_id.data != 0 else None
        )
        db.session.add(evento)
        db.session.commit()

        logger.info(f"Evento: {evento.titulo}")
        flash("Evento registrado", "success")
        return redirect(url_for("timeline", yacimiento_id=yacimiento_id))

    return render_template("eventos/nuevo.html", formulario=formulario, yacimiento=yacimiento)

@app.route("/evento/<int:evento_id>/editar", methods=["GET", "POST"])
@login_required
def editar_evento(evento_id):
    evento = db.session.get(Evento, evento_id)
    if not evento:
        abort(404)

    yacimiento, _ = obtener_yacimiento_con_acceso(evento.yacimiento_id, "edit")

    formulario = FormularioEvento()
    fases = FaseProyecto.query.filter_by(yacimiento_id=evento.yacimiento_id).all()
    hallazgos = Hallazgo.query.filter_by(yacimiento_id=evento.yacimiento_id).all()
    sectores = Sector.query.filter_by(yacimiento_id=evento.yacimiento_id).all()

    formulario.fase_id.choices = [(0, "Ninguna")] + [(f.id, f.nombre) for f in fases]
    formulario.hallazgo_id.choices = [(0, "Ninguno")] + [(h.id, h.codigo_acceso) for h in hallazgos]
    formulario.sector_id.choices = [(0, "Ninguno")] + [(s.id, s.nombre) for s in sectores]

    if formulario.validate_on_submit():
        evento.tipo = formulario.tipo.data
        evento.titulo = formulario.titulo.data
        evento.descripcion = formulario.descripcion.data
        evento.fecha = formulario.fecha.data
        evento.ubicacion = formulario.ubicacion.data
        evento.participantes = formulario.participantes.data
        evento.resultados = formulario.resultados.data
        evento.prioridad = formulario.prioridad.data
        evento.estado_evento = formulario.estado_evento.data
        evento.fase_id = formulario.fase_id.data if formulario.fase_id.data != 0 else None
        evento.hallazgo_id = formulario.hallazgo_id.data if formulario.hallazgo_id.data != 0 else None
        evento.sector_id = formulario.sector_id.data if formulario.sector_id.data != 0 else None

        db.session.commit()
        logger.info(f"Evento actualizado: {evento.titulo}")
        flash("Actualizado", "success")
        return redirect(url_for("timeline", yacimiento_id=evento.yacimiento_id))

    if request.method == "GET":
        formulario.tipo.data = evento.tipo
        formulario.titulo.data = evento.titulo
        formulario.descripcion.data = evento.descripcion
        formulario.fecha.data = evento.fecha
        formulario.ubicacion.data = evento.ubicacion
        formulario.participantes.data = evento.participantes
        formulario.resultados.data = evento.resultados
        formulario.prioridad.data = evento.prioridad
        formulario.estado_evento.data = evento.estado_evento
        formulario.fase_id.data = evento.fase_id or 0
        formulario.hallazgo_id.data = evento.hallazgo_id or 0
        formulario.sector_id.data = evento.sector_id or 0

    return render_template("eventos/editar.html", formulario=formulario, evento=evento)

@app.route("/evento/<int:evento_id>/eliminar", methods=["POST"])
@login_required
def eliminar_evento(evento_id):
    evento = db.session.get(Evento, evento_id)
    if not evento:
        abort(404)

    yacimiento, _ = obtener_yacimiento_con_acceso(evento.yacimiento_id, "delete")
    yac_id = evento.yacimiento_id

    db.session.delete(evento)
    db.session.commit()

    logger.info(f"Evento eliminado: {evento.titulo}")
    flash("Eliminado", "success")
    return redirect(url_for("timeline", yacimiento_id=yac_id))

#RUTAS INVITACIONES

@app.route("/yacimiento/<int:yacimiento_id>/invitaciones")
@login_required
def gestionar_invitaciones(yacimiento_id):
    yacimiento, _ = obtener_yacimiento_con_acceso(yacimiento_id, "manage")

    invitaciones = Invitacion.query.filter_by(yacimiento_id=yacimiento_id).order_by(Invitacion.fecha_envio.desc()).all()
    return render_template("invitaciones/gestionar.html", yacimiento=yacimiento, invitaciones=invitaciones)

@app.route("/yacimiento/<int:yacimiento_id>/invitar", methods=["GET", "POST"])
@login_required
def enviar_invitacion(yacimiento_id):
    yacimiento, _ = obtener_yacimiento_con_acceso(yacimiento_id, "manage")

    formulario = FormularioInvitacion()
    if formulario.validate_on_submit():
        usuario = Usuario.query.filter_by(correo_electronico=formulario.email.data).first()

        invitacion = Invitacion(
            yacimiento_id=yacimiento_id,
            invitado_id=usuario.id,
            invitado_por_id=current_user.id, 
            email=formulario.email.data,
            rol=formulario.rol.data,
            mensaje=formulario.mensaje.data,
            estado="pendiente"
        )
        db.session.add(invitacion)
        db.session.commit()

        logger.info(f"Invitación: {usuario.nombre_usuario} a {yacimiento.nombre}")
        flash("Invitación enviada", "success")
        return redirect(url_for("gestionar_invitaciones", yacimiento_id=yacimiento_id))

    return render_template("invitaciones/nueva.html", formulario=formulario, yacimiento=yacimiento)

@app.route("/mis-invitaciones")
@login_required
def mis_invitaciones():
    invitaciones = Invitacion.query.filter_by(invitado_id=current_user.id).order_by(Invitacion.fecha_envio.desc()).all()
    return render_template("invitaciones/mis_invitaciones.html", invitaciones=invitaciones)

@app.route("/invitacion/<int:invitacion_id>/aceptar", methods=["POST"])
@login_required
def aceptar_invitacion(invitacion_id):
    invitacion = db.session.get(Invitacion, invitacion_id)
    if not invitacion or invitacion.invitado_id != current_user.id:
        abort(404)

    invitacion.estado = "aceptada"
    invitacion.fecha_respuesta = datetime.utcnow()
    db.session.commit()

    logger.info(f"Invitación aceptada: {current_user.nombre_usuario}")
    flash("Â¡Invitación aceptada!", "success")
    return redirect(url_for("mis_invitaciones"))

@app.route("/invitacion/<int:invitacion_id>/rechazar", methods=["POST"])
@login_required
def rechazar_invitacion(invitacion_id):
    invitacion = db.session.get(Invitacion, invitacion_id)
    if not invitacion or invitacion.invitado_id != current_user.id:
        abort(404)

    invitacion.estado = "rechazada"
    invitacion.fecha_respuesta = datetime.utcnow()
    db.session.commit()

    logger.info(f"Invitación rechazada: {current_user.nombre_usuario}")
    flash("Invitación rechazada", "info")
    return redirect(url_for("mis_invitaciones"))

@app.route("/invitacion/<int:invitacion_id>/cancelar", methods=["POST"])
@login_required
def cancelar_invitacion(invitacion_id):
    invitacion = db.session.get(Invitacion, invitacion_id)
    if not invitacion:
        abort(404)

    yacimiento, _ = obtener_yacimiento_con_acceso(invitacion.yacimiento_id, "manage")

    invitacion.estado = "cancelada"
    invitacion.fecha_respuesta = datetime.utcnow()
    db.session.commit()

    logger.info(f"Invitación cancelada por {current_user.nombre_usuario}")
    flash("Cancelada", "info")
    return redirect(url_for("gestionar_invitaciones", yacimiento_id=invitacion.yacimiento_id))

#RUTAS BÃšSQUEDA

@app.route("/yacimiento/<int:yacimiento_id>/informe")
@login_required
def generar_informe(yacimiento_id):
    """Genera un informe PDF del yacimiento (placeholder - implementar con ReportLab)"""
    yacimiento, _ = obtener_yacimiento_con_acceso(yacimiento_id, "read")

    # TODO: Implementar generación de PDF con ReportLab
    # Por ahora, retornar mensaje
    flash("Funcionalidad de generación de PDF en desarrollo", "info")
    return redirect(url_for("detalle_yacimiento", id=yacimiento_id))

@app.route("/buscar-codigo", methods=["GET", "POST"])
@login_required
def buscar_codigo():
    if request.method == "POST":
        codigo = request.form.get("codigo", "").strip().upper()
        hallazgo = Hallazgo.query.filter_by(codigo_acceso=codigo).first()

        if hallazgo:
            tiene_acceso, _ = verificar_acceso_yacimiento(hallazgo.yacimiento_id, "read")
            if tiene_acceso:
                return redirect(url_for("detalle_hallazgo", id=hallazgo.id))
            flash("Sin acceso", "error")
        else:
            flash("No encontrado", "error")

    return render_template("buscar_codigo.html")

@app.route("/api/buscar-hallazgo", methods=["POST"])
@login_required
def api_buscar_hallazgo():
    data = request.get_json()
    codigo = data.get("codigo", "").strip().upper()

    hallazgo = Hallazgo.query.filter_by(codigo_acceso=codigo).first()
    if not hallazgo:
        return jsonify({"success": False}), 404

    tiene_acceso, _ = verificar_acceso_yacimiento(hallazgo.yacimiento_id, "read")
    if not tiene_acceso:
        return jsonify({"success": False}), 403

    return jsonify({
        "success": True,
        "hallazgo": {
            "id": hallazgo.id,
            "codigo": hallazgo.codigo_acceso,
            "tipo": hallazgo.tipo,
            "yacimiento": hallazgo.yacimiento.nombre if hallazgo.yacimiento else None
        }
    })

@app.route("/api/yacimiento/<int:yacimiento_id>/estadisticas")
@login_required
def api_estadisticas(yacimiento_id):
    yacimiento, _ = obtener_yacimiento_con_acceso(yacimiento_id, "read")

    return jsonify({
        "yacimiento_id": yacimiento_id,
        "total_hallazgos": Hallazgo.query.filter_by(yacimiento_id=yacimiento_id).count(),
        "total_sectores": Sector.query.filter_by(yacimiento_id=yacimiento_id).count(),
        "total_fases": FaseProyecto.query.filter_by(yacimiento_id=yacimiento_id).count(),
        "total_eventos": Evento.query.filter_by(yacimiento_id=yacimiento_id).count()
    })

# RUTA ARCHIVOS

@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

#ERRORHANDLERS

@app.errorhandler(404)
def pagina_no_encontrada(e):
    return render_template("errores/404.html"), 404

@app.errorhandler(403)
def acceso_prohibido(e):
    return render_template("errores/403.html"), 403

@app.errorhandler(500)
def error_interno(e):
    db.session.rollback()
    logger.error(f"Error 500: {str(e)}", exc_info=True)
    return render_template("errores/500.html"), 500

#JINJAFILTERS

@app.template_filter("fecha_es")
def fecha_es_filter(fecha):
    if isinstance(fecha, str):
        try:
            fecha = datetime.strptime(fecha, "%Y-%m-%d")
        except ValueError:
            return fecha

    if isinstance(fecha, datetime):
        meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
                "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
        return f"{fecha.day} de {meses[fecha.month - 1]} de {fecha.year}"

    return fecha

@app.template_filter("tiempo_relativo")
def tiempo_relativo_filter(fecha):
    if isinstance(fecha, str):
        try:
            fecha = datetime.strptime(fecha, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return fecha

    if isinstance(fecha, datetime):
        ahora = datetime.utcnow()
        diff = ahora - fecha

        if diff.days > 365:
            return f"Hace {diff.days // 365} año(s)"
        elif diff.days > 30:
            return f"Hace {diff.days // 30} mes(es)"
        elif diff.days > 0:
            return f"Hace {diff.days} día(s)"
        elif diff.seconds > 3600:
            return f"Hace {diff.seconds // 3600} hora(s)"
        elif diff.seconds > 60:
            return f"Hace {diff.seconds // 60} minuto(s)"
        else:
            return "Hace unos segundos"

    return fecha

#__INIT__

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=app.config["DEBUG"], host="0.0.0.0", port=5000)