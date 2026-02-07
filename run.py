import os
from datetime import datetime
from dotenv import load_dotenv
from app import create_app, db
from app.models.user import Usuario
from flask_bcrypt import Bcrypt
import click

load_dotenv()

app = create_app()
bcrypt = Bcrypt(app)

# Auto-setup para Replit
def setup_replit():
    """Configuración automática para Replit"""
    with app.app_context():
        # Crear directorio de uploads
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

        # Crear tablas si no existen
        db.create_all()

        # Crear usuario admin si no existe
        if not Usuario.query.filter_by(nombre_usuario='admin').first():
            admin = Usuario(
                nombre_usuario='admin',
                nombre='Administrador',
                apellidos='Sistema',
                email='admin@arqueotrack.com',
                fecha_nacimiento=datetime.strptime('1990-01-01', '%Y-%m-%d').date(),
                ocupacion='admin',
                password_hash=bcrypt.generate_password_hash('admin12345').decode('utf-8')
            )
            db.session.add(admin)
            db.session.commit()
            print('✅ Usuario admin creado: admin@arqueotrack.com / admin12345')

# Comandos CLI (para uso manual si es necesario)
@app.cli.command()
def init_db():
    """Inicializar base de datos"""
    with app.app_context():
        db.create_all()
        click.echo('✅ Base de datos inicializada')

@app.cli.command()
def seed_db():
    """Crear usuario admin"""
    with app.app_context():
        if not Usuario.query.filter_by(nombre_usuario='admin').first():
            admin = Usuario(
                nombre_usuario='admin',
                nombre='Administrador',
                apellidos='Sistema',
                email='admin@arqueotrack.com',
                fecha_nacimiento=datetime.strptime('1990-01-01', '%Y-%m-%d').date(),
                ocupacion='admin',
                password_hash=bcrypt.generate_password_hash('admin12345').decode('utf-8')
            )
            db.session.add(admin)
            db.session.commit()
            click.echo('✅ Usuario admin creado: admin/admin12345')
        else:
            click.echo('ℹ️  Usuario admin ya existe')

if __name__ == '__main__':
    # Auto-setup en Replit
    if os.getenv('REPL_ID'):  # Detectar si está en Replit
        print('🔧 Configurando ArqueoTrack para Replit...')
        setup_replit()

    # Obtener puerto
    port = int(os.getenv('PORT', 5000))

    print('=' * 60)
    print('🏛️  ArqueoTrack - First Lego League 2026')
    print('=' * 60)
    print(f'🌐 Servidor ejecutándose en puerto {port}')
    print('📧 Email: admin@arqueotrack.com')
    print('🔑 Contraseña: admin12345')
    print('=' * 60)

    # Ejecutar aplicación
    app.run(
        host='0.0.0.0',
        port=port,
        debug=True
    )