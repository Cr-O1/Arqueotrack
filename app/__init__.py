import os
from flask import Flask, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect

# Inicializar extensiones
db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()
csrf = CSRFProtect()


def create_app(config_name='development'):
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    app = Flask(
        __name__,
        template_folder=os.path.join(project_root, 'templates'),
        static_folder=os.path.join(project_root, 'static')
    )

    # Cargar configuración
    from config import get_config
    app_config = get_config(config_name)
    app.config.from_object(app_config)

    # Crear directorio de uploads si no existe
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Inicializar extensiones
    db.init_app(app)
    
    with app.app_context():
        # Crear tablas si no existen
        db.create_all()

    login_manager.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)

    # Configurar login
    login_manager.login_view = 'auth.iniciar_sesion'
    login_manager.login_message_category = 'info'
    login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'

    from app.models.user import Usuario

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(Usuario, int(user_id))

    # Registrar blueprints
    from app.blueprints.auth import auth_bp
    app.register_blueprint(auth_bp)

    from app.blueprints.main import main_bp
    app.register_blueprint(main_bp)

    from app.blueprints.yacimiento import yacimiento_bp
    app.register_blueprint(yacimiento_bp)

    from app.blueprints.hallazgo import hallazgo_bp
    app.register_blueprint(hallazgo_bp)

    from app.blueprints.sector import sector_bp
    app.register_blueprint(sector_bp)

    from app.blueprints.fase import fase_bp
    app.register_blueprint(fase_bp)

    from app.blueprints.evento import evento_bp
    app.register_blueprint(evento_bp)

    from app.blueprints.invitacion import invitacion_bp
    app.register_blueprint(invitacion_bp)

    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        """Servir archivos subidos por los usuarios."""
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    # Configurar manejo de errores
    @app.errorhandler(404)
    def not_found(error):
        from flask import render_template
        return render_template('errores/404.html'), 404

    @app.errorhandler(403)
    def forbidden(error):
        from flask import render_template
        return render_template('errores/403.html'), 403

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        from flask import render_template
        return render_template('errores/500.html'), 500

    return app
