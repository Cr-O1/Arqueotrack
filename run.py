import os
from dotenv import load_dotenv
from app import create_app, db
import click

load_dotenv()

app = create_app()


# Auto-setup para Replit (sin crear usuarios por defecto)
def setup_replit():
    """Configuración automática para Replit"""
    with app.app_context():
        # Crear directorio de uploads
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

        # Crear tablas si no existen
        db.create_all()


# Comandos CLI (para uso manual si es necesario)
@app.cli.command()
def init_db():
    """Inicializar base de datos"""
    with app.app_context():
        db.create_all()
        click.echo('Base de datos inicializada')


if __name__ == '__main__':
    # Auto-setup en Replit
    if os.getenv('REPL_ID'):  # Detectar si está en Replit
        print('Configurando ArqueoTrack...')
        setup_replit()

    # Obtener puerto
    port = int(os.getenv('PORT', 5000))

    print('=' * 60)
    print('ArqueoTrack')
    print('=' * 60)
    print(f'Servidor ejecutándose en puerto {port}')
    print('=' * 60)

    # Ejecutar aplicación
    app.run(
        host='0.0.0.0',
        port=port,
        debug=True
    )
