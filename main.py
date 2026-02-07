"""
Punto de entrada principal para Replit
ArqueoTrack - First Lego League 2026
"""

import os
from app import create_app, db
from app.models import Usuario

# Crear aplicación
app = create_app()

# Auto-inicializar base de datos en Replit
with app.app_context():
    # Crear directorio de uploads si no existe
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Crear tablas si no existen
    db.create_all()

    # Crear usuario admin si no existe
    if not Usuario.query.filter_by(nombre_usuario='admin').first():
        from flask_bcrypt import Bcrypt
        bcrypt = Bcrypt(app)
        from datetime import datetime

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

if __name__ == '__main__':
    # Obtener puerto de Replit
    port = int(os.getenv('PORT', 5000))

    print('=' * 50)
    print('🏛️  ArqueoTrack - First Lego League 2026')
    print('=' * 50)
    print(f'🌐 Servidor iniciado en puerto {port}')
    print('📧 Email: admin@arqueotrack.com')
    print('🔑 Contraseña: admin12345')
    print('=' * 50)

    # Ejecutar servidor
    app.run(
        host='0.0.0.0',
        port=port,
        debug=True
    )