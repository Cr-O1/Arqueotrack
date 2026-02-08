"""
Punto de entrada principal para Replit
ArqueoTrack - First Lego League 2026
"""

import os
from app import create_app

# Crear aplicación
app = create_app()

if __name__ == '__main__':
    # Obtener puerto de Replit
    port = int(os.getenv('PORT', 5000))

    print('=' * 50)
    print('🏛️  ArqueoTrack - First Lego League 2026')
    print('=' * 50)
    print(f'🌐 Servidor iniciado en puerto {port}')
    print('=' * 50)

    # Ejecutar servidor
    app.run(
        host='0.0.0.0',
        port=port,
        debug=True
    )
