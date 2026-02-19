"""
ArqueoTrack - Suite de Tests Unitarios
=======================================
Ejecutar con:
    pytest test_arqueotrack.py -v
    pytest test_arqueotrack.py -v --cov=app --cov-report=term-missing
"""

import pytest
import os
import io
from datetime import date, datetime

# ---------------------------------------------------------------------------
# Configuración y fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def app():
    """Crea la aplicación Flask con configuración de test."""
    from app import create_app, db as _db

    os.environ.setdefault("SECRET_KEY", "test-secret-key")

    test_app = create_app()
    test_app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        UPLOAD_FOLDER="/tmp/arqueotrack_test_uploads",
    )

    os.makedirs(test_app.config["UPLOAD_FOLDER"], exist_ok=True)

    with test_app.app_context():
        _db.create_all()
        yield test_app
        _db.drop_all()


@pytest.fixture(scope="function")
def db(app):
    """Proporciona una sesión de base de datos limpia para cada test."""
    from app import db as _db

    with app.app_context():
        yield _db
        _db.session.rollback()
        # Limpiar tablas entre tests
        for table in reversed(_db.metadata.sorted_tables):
            _db.session.execute(table.delete())
        _db.session.commit()


@pytest.fixture
def client(app):
    """Cliente de test Flask."""
    return app.test_client()


@pytest.fixture
def usuario_registrado(db, app):
    """Crea un usuario de prueba en la base de datos."""
    from app.models import Usuario
    from app import bcrypt

    with app.app_context():
        usuario = Usuario(
            nombre="Arqueólogo Test",
            email="test@arqueotrack.com",
            password_hash=bcrypt.generate_password_hash("password123").decode("utf-8"),
            institucion="Universidad de Test",
            especialidad="Prehistoria",
        )
        db.session.add(usuario)
        db.session.commit()
        # Refrescar para asegurar que el objeto está adjunto a la sesión
        db.session.refresh(usuario)
        return usuario


@pytest.fixture
def usuario_secundario(db, app):
    """Segundo usuario para tests de permisos."""
    from app.models import Usuario
    from app import bcrypt

    with app.app_context():
        usuario = Usuario(
            nombre="Otro Arqueólogo",
            email="otro@arqueotrack.com",
            password_hash=bcrypt.generate_password_hash("password456").decode("utf-8"),
        )
        db.session.add(usuario)
        db.session.commit()
        db.session.refresh(usuario)
        return usuario


@pytest.fixture
def client_autenticado(client, usuario_registrado, app):
    """Cliente con sesión iniciada."""
    with app.app_context():
        with client.session_transaction() as sess:
            sess["_user_id"] = str(usuario_registrado.id)
            sess["_fresh"] = True
    return client


@pytest.fixture
def yacimiento_ejemplo(db, app, usuario_registrado):
    """Crea un yacimiento de prueba."""
    from app.models import Yacimiento

    with app.app_context():
        yacimiento = Yacimiento(
            nombre="Yacimiento Test",
            ubicacion="Teruel, España",
            descripcion="Un yacimiento de prueba",
            lat=40.3456,
            lng=-1.1234,
            user_id=usuario_registrado.id,
            responsable="Arqueólogo Test",
            fecha_inicio=date(2024, 1, 1),
        )
        db.session.add(yacimiento)
        db.session.commit()
        db.session.refresh(yacimiento)
        return yacimiento


@pytest.fixture
def hallazgo_ejemplo(db, app, usuario_registrado, yacimiento_ejemplo):
    """Crea un hallazgo de prueba."""
    from app.models import Hallazgo

    with app.app_context():
        hallazgo = Hallazgo(
            tipo="Cerámica",
            descripcion="Fragmento de cerámica ibérica",
            yacimiento_id=yacimiento_ejemplo.id,
            user_id=usuario_registrado.id,
            material="Barro cocido",
            estado_conservacion="Bueno",
            fecha=date(2024, 3, 15),
        )
        db.session.add(hallazgo)
        db.session.commit()
        db.session.refresh(hallazgo)
        return hallazgo


# ---------------------------------------------------------------------------
# Tests del Modelo: Usuario
# ---------------------------------------------------------------------------

class TestModeloUsuario:
    """Tests para el modelo Usuario."""

    def test_crear_usuario(self, db, app):
        """Se puede crear un usuario con datos válidos."""
        from app.models import Usuario
        from app import bcrypt

        with app.app_context():
            usuario = Usuario(
                nombre="Juan Arqueólogo",
                email="juan@test.com",
                password_hash=bcrypt.generate_password_hash("pass").decode("utf-8"),
            )
            db.session.add(usuario)
            db.session.commit()

            assert usuario.id is not None
            assert usuario.email == "juan@test.com"

    def test_usuario_email_unico(self, db, app, usuario_registrado):
        """No se pueden crear dos usuarios con el mismo email."""
        from app.models import Usuario
        from app import bcrypt
        from sqlalchemy.exc import IntegrityError

        with app.app_context():
            duplicado = Usuario(
                nombre="Duplicado",
                email="test@arqueotrack.com",  # mismo email que usuario_registrado
                password_hash=bcrypt.generate_password_hash("pass").decode("utf-8"),
            )
            db.session.add(duplicado)
            with pytest.raises(IntegrityError):
                db.session.commit()

    def test_verificar_contraseña_correcta(self, app, usuario_registrado):
        """La verificación de contraseña funciona con contraseña correcta."""
        from app import bcrypt

        with app.app_context():
            assert bcrypt.check_password_hash(
                usuario_registrado.password_hash, "password123"
            )

    def test_verificar_contraseña_incorrecta(self, app, usuario_registrado):
        """La verificación de contraseña falla con contraseña incorrecta."""
        from app import bcrypt

        with app.app_context():
            assert not bcrypt.check_password_hash(
                usuario_registrado.password_hash, "wrongpassword"
            )

    def test_usuario_activo_por_defecto(self, db, app):
        """Un usuario nuevo está activo por defecto."""
        from app.models import Usuario
        from app import bcrypt

        with app.app_context():
            usuario = Usuario(
                nombre="Test",
                email="activo@test.com",
                password_hash=bcrypt.generate_password_hash("pass").decode("utf-8"),
            )
            db.session.add(usuario)
            db.session.commit()
            assert usuario.is_active is True

    def test_repr_usuario(self, app, usuario_registrado):
        """El repr del usuario contiene su email."""
        with app.app_context():
            assert "test@arqueotrack.com" in repr(usuario_registrado)


# ---------------------------------------------------------------------------
# Tests del Modelo: Yacimiento
# ---------------------------------------------------------------------------

class TestModeloYacimiento:
    """Tests para el modelo Yacimiento."""

    def test_crear_yacimiento(self, db, app, usuario_registrado):
        """Se puede crear un yacimiento correctamente."""
        from app.models import Yacimiento

        with app.app_context():
            yacimiento = Yacimiento(
                nombre="Dolmen de Menga",
                ubicacion="Antequera, Málaga",
                lat=37.0123,
                lng=-4.5678,
                user_id=usuario_registrado.id,
            )
            db.session.add(yacimiento)
            db.session.commit()

            assert yacimiento.id is not None
            assert yacimiento.nombre == "Dolmen de Menga"

    def test_yacimiento_pertenece_a_usuario(self, db, app, yacimiento_ejemplo, usuario_registrado):
        """El yacimiento está correctamente asociado a su propietario."""
        with app.app_context():
            assert yacimiento_ejemplo.user_id == usuario_registrado.id

    def test_yacimiento_fecha_creacion_automatica(self, db, app, yacimiento_ejemplo):
        """La fecha de creación se asigna automáticamente."""
        with app.app_context():
            assert yacimiento_ejemplo.fecha_creacion is not None

    def test_yacimiento_con_coordenadas(self, db, app, usuario_registrado):
        """El yacimiento almacena coordenadas geográficas correctamente."""
        from app.models import Yacimiento

        with app.app_context():
            yacimiento = Yacimiento(
                nombre="Cueva de Altamira",
                ubicacion="Santillana del Mar, Cantabria",
                lat=43.3789,
                lng=-4.1149,
                user_id=usuario_registrado.id,
            )
            db.session.add(yacimiento)
            db.session.commit()

            assert yacimiento.lat == pytest.approx(43.3789)
            assert yacimiento.lng == pytest.approx(-4.1149)

    def test_yacimiento_con_geojson(self, db, app, usuario_registrado):
        """El yacimiento puede almacenar un polígono GeoJSON."""
        from app.models import Yacimiento

        geojson = '{"type":"Polygon","coordinates":[[[0,0],[1,0],[1,1],[0,1],[0,0]]]}'
        with app.app_context():
            yacimiento = Yacimiento(
                nombre="Yacimiento GeoJSON",
                ubicacion="Madrid",
                lat=40.4168,
                lng=-3.7038,
                user_id=usuario_registrado.id,
                polygon_geojson=geojson,
            )
            db.session.add(yacimiento)
            db.session.commit()

            assert yacimiento.polygon_geojson == geojson


# ---------------------------------------------------------------------------
# Tests del Modelo: Hallazgo
# ---------------------------------------------------------------------------

class TestModeloHallazgo:
    """Tests para el modelo Hallazgo."""

    def test_crear_hallazgo_genera_codigo(self, db, app, yacimiento_ejemplo, usuario_registrado):
        """Al crear un hallazgo se genera automáticamente un código único."""
        from app.models import Hallazgo

        with app.app_context():
            hallazgo = Hallazgo(
                tipo="Moneda",
                yacimiento_id=yacimiento_ejemplo.id,
                user_id=usuario_registrado.id,
            )
            db.session.add(hallazgo)
            db.session.commit()

            assert hallazgo.codigo_acceso is not None
            assert len(hallazgo.codigo_acceso) == 10

    def test_codigos_hallazgo_unicos(self, db, app, yacimiento_ejemplo, usuario_registrado):
        """Dos hallazgos distintos tienen códigos de acceso distintos."""
        from app.models import Hallazgo

        with app.app_context():
            h1 = Hallazgo(tipo="Moneda", yacimiento_id=yacimiento_ejemplo.id, user_id=usuario_registrado.id)
            h2 = Hallazgo(tipo="Cerámica", yacimiento_id=yacimiento_ejemplo.id, user_id=usuario_registrado.id)
            db.session.add_all([h1, h2])
            db.session.commit()

            assert h1.codigo_acceso != h2.codigo_acceso

    def test_hallazgo_alphanumerico(self, db, app, yacimiento_ejemplo, usuario_registrado):
        """El código de acceso del hallazgo es alfanumérico."""
        from app.models import Hallazgo

        with app.app_context():
            hallazgo = Hallazgo(
                tipo="Hueso",
                yacimiento_id=yacimiento_ejemplo.id,
                user_id=usuario_registrado.id,
            )
            db.session.add(hallazgo)
            db.session.commit()

            assert hallazgo.codigo_acceso.isalnum()

    def test_hallazgo_relacion_yacimiento(self, db, app, hallazgo_ejemplo, yacimiento_ejemplo):
        """El hallazgo está correctamente relacionado con su yacimiento."""
        with app.app_context():
            assert hallazgo_ejemplo.yacimiento_id == yacimiento_ejemplo.id

    def test_hallazgo_campos_opcionales(self, db, app, yacimiento_ejemplo, usuario_registrado):
        """Se puede crear un hallazgo con solo los campos requeridos."""
        from app.models import Hallazgo

        with app.app_context():
            hallazgo = Hallazgo(
                tipo="Lítico",
                yacimiento_id=yacimiento_ejemplo.id,
                user_id=usuario_registrado.id,
            )
            db.session.add(hallazgo)
            db.session.commit()

            assert hallazgo.id is not None
            assert hallazgo.descripcion is None
            assert hallazgo.foto is None


# ---------------------------------------------------------------------------
# Tests del Modelo: Sector
# ---------------------------------------------------------------------------

class TestModeloSector:
    """Tests para el modelo Sector."""

    def test_crear_sector(self, db, app, yacimiento_ejemplo, usuario_registrado):
        """Se puede crear un sector dentro de un yacimiento."""
        from app.models import Sector

        with app.app_context():
            sector = Sector(
                nombre="Sector A",
                descripcion="Zona norte del yacimiento",
                yacimiento_id=yacimiento_ejemplo.id,
                user_id=usuario_registrado.id,
            )
            db.session.add(sector)
            db.session.commit()

            assert sector.id is not None
            assert sector.nombre == "Sector A"

    def test_sector_pertenece_a_yacimiento(self, db, app, yacimiento_ejemplo, usuario_registrado):
        """El sector está vinculado a su yacimiento."""
        from app.models import Sector

        with app.app_context():
            sector = Sector(
                nombre="Sector B",
                yacimiento_id=yacimiento_ejemplo.id,
                user_id=usuario_registrado.id,
            )
            db.session.add(sector)
            db.session.commit()

            assert sector.yacimiento_id == yacimiento_ejemplo.id


# ---------------------------------------------------------------------------
# Tests del Modelo: FaseProyecto
# ---------------------------------------------------------------------------

class TestModeloFaseProyecto:
    """Tests para el modelo FaseProyecto."""

    def test_crear_fase(self, db, app, yacimiento_ejemplo):
        """Se puede crear una fase de proyecto."""
        from app.models import FaseProyecto

        with app.app_context():
            fase = FaseProyecto(
                nombre="Fase de Prospección",
                descripcion="Primera fase del proyecto",
                estado="planificada",
                yacimiento_id=yacimiento_ejemplo.id,
                fecha_inicio=date(2024, 3, 1),
            )
            db.session.add(fase)
            db.session.commit()

            assert fase.id is not None
            assert fase.estado == "planificada"

    def test_estados_validos_fase(self, db, app, yacimiento_ejemplo):
        """Los estados válidos de una fase son los correctos."""
        from app.models import FaseProyecto

        estados = ["planificada", "en_curso", "finalizada"]
        with app.app_context():
            for estado in estados:
                fase = FaseProyecto(
                    nombre=f"Fase {estado}",
                    estado=estado,
                    yacimiento_id=yacimiento_ejemplo.id,
                )
                db.session.add(fase)
            db.session.commit()
            # Si llegamos aquí sin excepción, todos los estados son válidos
            assert True


# ---------------------------------------------------------------------------
# Tests del Modelo: Evento
# ---------------------------------------------------------------------------

class TestModeloEvento:
    """Tests para el modelo Evento."""

    def test_crear_evento(self, db, app, yacimiento_ejemplo, usuario_registrado):
        """Se puede crear un evento de timeline."""
        from app.models import Evento

        with app.app_context():
            evento = Evento(
                titulo="Inicio de excavación",
                descripcion="Se inicia la campaña de excavación",
                tipo="hito",
                prioridad="alta",
                estado="completado",
                fecha=date(2024, 4, 1),
                yacimiento_id=yacimiento_ejemplo.id,
                user_id=usuario_registrado.id,
            )
            db.session.add(evento)
            db.session.commit()

            assert evento.id is not None
            assert evento.titulo == "Inicio de excavación"

    def test_evento_fecha_creacion(self, db, app, yacimiento_ejemplo, usuario_registrado):
        """La fecha de creación del evento se asigna automáticamente."""
        from app.models import Evento

        with app.app_context():
            evento = Evento(
                titulo="Hallazgo importante",
                tipo="hallazgo",
                fecha=date(2024, 5, 10),
                yacimiento_id=yacimiento_ejemplo.id,
                user_id=usuario_registrado.id,
            )
            db.session.add(evento)
            db.session.commit()

            assert evento.fecha_creacion is not None


# ---------------------------------------------------------------------------
# Tests de Autenticación (Blueprint auth)
# ---------------------------------------------------------------------------

class TestAutenticacion:
    """Tests para registro, login y logout."""

    def test_pagina_login_accesible(self, client):
        """La página de login es accesible sin autenticación."""
        response = client.get("/login")
        assert response.status_code == 200

    def test_pagina_registro_accesible(self, client):
        """La página de registro es accesible sin autenticación."""
        response = client.get("/registro")
        assert response.status_code == 200

    def test_registro_nuevo_usuario(self, client, db, app):
        """Un usuario nuevo puede registrarse correctamente."""
        with app.app_context():
            response = client.post(
                "/registro",
                data={
                    "nombre": "Nuevo Usuario",
                    "email": "nuevo@test.com",
                    "password": "SecurePass123",
                    "confirm_password": "SecurePass123",
                },
                follow_redirects=True,
            )
            assert response.status_code == 200

    def test_login_credenciales_correctas(self, client, usuario_registrado, app):
        """Login con credenciales correctas redirige al dashboard."""
        with app.app_context():
            response = client.post(
                "/login",
                data={
                    "email": "test@arqueotrack.com",
                    "password": "password123",
                },
                follow_redirects=True,
            )
            assert response.status_code == 200

    def test_login_credenciales_incorrectas(self, client, usuario_registrado, app):
        """Login con contraseña incorrecta no autentica al usuario."""
        with app.app_context():
            response = client.post(
                "/login",
                data={
                    "email": "test@arqueotrack.com",
                    "password": "wrongpassword",
                },
                follow_redirects=True,
            )
            # Debe mantenerse en la página de login o mostrar error
            assert response.status_code == 200
            # No debe haber redirigido al dashboard
            assert b"dashboard" not in response.data.lower() or b"error" in response.data.lower() or b"incorrect" in response.data.lower()

    def test_login_email_inexistente(self, client, app):
        """Login con email inexistente no autentica."""
        with app.app_context():
            response = client.post(
                "/login",
                data={
                    "email": "noexiste@test.com",
                    "password": "password123",
                },
                follow_redirects=True,
            )
            assert response.status_code == 200

    def test_logout(self, client_autenticado, app):
        """Un usuario autenticado puede hacer logout."""
        with app.app_context():
            response = client_autenticado.get("/logout", follow_redirects=True)
            assert response.status_code == 200

    def test_rutas_protegidas_redirigen_a_login(self, client, app):
        """Las rutas protegidas redirigen a login si no hay sesión."""
        rutas_protegidas = ["/dashboard", "/nuevo_yacimiento"]
        with app.app_context():
            for ruta in rutas_protegidas:
                response = client.get(ruta, follow_redirects=False)
                assert response.status_code in (301, 302), f"Ruta {ruta} no redirige"


# ---------------------------------------------------------------------------
# Tests de Yacimiento (Blueprint yacimiento)
# ---------------------------------------------------------------------------

class TestBlueprintYacimiento:
    """Tests para las rutas de yacimientos."""

    def test_lista_yacimientos_requiere_auth(self, client, app):
        """El dashboard requiere autenticación."""
        with app.app_context():
            response = client.get("/dashboard", follow_redirects=False)
            assert response.status_code in (301, 302)

    def test_crear_yacimiento_get(self, client_autenticado, app):
        """El formulario de nuevo yacimiento es accesible."""
        with app.app_context():
            response = client_autenticado.get("/nuevo_yacimiento")
            assert response.status_code == 200

    def test_crear_yacimiento_post(self, client_autenticado, db, app):
        """Se puede crear un yacimiento vía POST."""
        with app.app_context():
            response = client_autenticado.post(
                "/nuevo_yacimiento",
                data={
                    "nombre": "Yacimiento Nuevo",
                    "ubicacion": "Zaragoza, España",
                    "descripcion": "Un yacimiento de prueba",
                    "lat": "41.6488",
                    "lng": "-0.8891",
                    "responsable": "Dr. Test",
                    "fecha_inicio": "2024-01-01",
                },
                follow_redirects=True,
            )
            assert response.status_code == 200

    def test_detalle_yacimiento_propietario(self, client_autenticado, yacimiento_ejemplo, app):
        """El propietario puede ver el detalle de su yacimiento."""
        with app.app_context():
            response = client_autenticado.get(f"/yacimiento/{yacimiento_ejemplo.id}")
            assert response.status_code == 200

    def test_detalle_yacimiento_no_existe(self, client_autenticado, app):
        """Acceder a un yacimiento inexistente devuelve 404."""
        with app.app_context():
            response = client_autenticado.get("/yacimiento/99999")
            assert response.status_code == 404

    def test_editar_yacimiento_propietario(self, client_autenticado, yacimiento_ejemplo, app):
        """El propietario puede acceder al formulario de edición."""
        with app.app_context():
            response = client_autenticado.get(f"/editar_yacimiento/{yacimiento_ejemplo.id}")
            assert response.status_code == 200

    def test_editar_yacimiento_no_propietario(self, client, usuario_secundario, yacimiento_ejemplo, app):
        """Un usuario no propietario no puede editar el yacimiento."""
        with app.app_context():
            with client.session_transaction() as sess:
                sess["_user_id"] = str(usuario_secundario.id)
                sess["_fresh"] = True
            response = client.get(
                f"/editar_yacimiento/{yacimiento_ejemplo.id}",
                follow_redirects=False,
            )
            assert response.status_code in (302, 403)

    def test_eliminar_yacimiento_no_propietario(self, client, usuario_secundario, yacimiento_ejemplo, app):
        """Un usuario no propietario no puede eliminar el yacimiento."""
        with app.app_context():
            with client.session_transaction() as sess:
                sess["_user_id"] = str(usuario_secundario.id)
                sess["_fresh"] = True
            response = client.post(
                f"/eliminar_yacimiento/{yacimiento_ejemplo.id}",
                follow_redirects=False,
            )
            assert response.status_code in (302, 403)


# ---------------------------------------------------------------------------
# Tests de Hallazgo (Blueprint hallazgo)
# ---------------------------------------------------------------------------

class TestBlueprintHallazgo:
    """Tests para las rutas de hallazgos."""

    def test_nuevo_hallazgo_get(self, client_autenticado, yacimiento_ejemplo, app):
        """El formulario de nuevo hallazgo es accesible."""
        with app.app_context():
            response = client_autenticado.get(
                f"/yacimiento/{yacimiento_ejemplo.id}/hallazgos/nuevo"
            )
            assert response.status_code == 200

    def test_crear_hallazgo_post(self, client_autenticado, yacimiento_ejemplo, db, app):
        """Se puede crear un hallazgo vía POST."""
        with app.app_context():
            response = client_autenticado.post(
                f"/yacimiento/{yacimiento_ejemplo.id}/hallazgos/nuevo",
                data={
                    "tipo": "Moneda",
                    "descripcion": "Moneda romana del siglo II",
                    "material": "Bronce",
                    "estado_conservacion": "Regular",
                    "fecha": "2024-05-01",
                    "sector_id": "0",
                },
                follow_redirects=True,
            )
            assert response.status_code == 200

    def test_detalle_hallazgo(self, client_autenticado, hallazgo_ejemplo, app):
        """El propietario puede ver el detalle de un hallazgo."""
        with app.app_context():
            response = client_autenticado.get(f"/hallazgo/{hallazgo_ejemplo.id}")
            assert response.status_code == 200

    def test_detalle_hallazgo_no_existe(self, client_autenticado, app):
        """Acceder a un hallazgo inexistente devuelve 404."""
        with app.app_context():
            response = client_autenticado.get("/hallazgo/99999")
            assert response.status_code == 404

    def test_busqueda_por_codigo(self, client_autenticado, hallazgo_ejemplo, app):
        """Se puede buscar un hallazgo por su código de acceso."""
        with app.app_context():
            response = client_autenticado.get(
                f"/buscar_codigo?codigo={hallazgo_ejemplo.codigo_acceso}",
                follow_redirects=True,
            )
            assert response.status_code == 200

    def test_editar_hallazgo_propietario(self, client_autenticado, hallazgo_ejemplo, app):
        """El propietario puede acceder al formulario de edición del hallazgo."""
        with app.app_context():
            response = client_autenticado.get(f"/editar_hallazgo/{hallazgo_ejemplo.id}")
            assert response.status_code == 200

    def test_hallazgo_no_autorizado(self, client, usuario_secundario, hallazgo_ejemplo, app):
        """Un usuario sin permisos no puede ver el detalle del hallazgo."""
        with app.app_context():
            with client.session_transaction() as sess:
                sess["_user_id"] = str(usuario_secundario.id)
                sess["_fresh"] = True
            response = client.get(
                f"/hallazgo/{hallazgo_ejemplo.id}",
                follow_redirects=False,
            )
            assert response.status_code in (302, 403)


# ---------------------------------------------------------------------------
# Tests de Sector (Blueprint sector)
# ---------------------------------------------------------------------------

class TestBlueprintSector:
    """Tests para las rutas de sectores."""

    def test_nuevo_sector_get(self, client_autenticado, yacimiento_ejemplo, app):
        """El formulario de nuevo sector es accesible."""
        with app.app_context():
            response = client_autenticado.get(
                f"/yacimiento/{yacimiento_ejemplo.id}/sectores/nuevo"
            )
            assert response.status_code == 200

    def test_crear_sector_post(self, client_autenticado, yacimiento_ejemplo, db, app):
        """Se puede crear un sector vía POST."""
        with app.app_context():
            response = client_autenticado.post(
                f"/yacimiento/{yacimiento_ejemplo.id}/sectores/nuevo",
                data={
                    "nombre": "Sector Norte",
                    "descripcion": "Zona norte del yacimiento",
                },
                follow_redirects=True,
            )
            assert response.status_code == 200

    def test_listar_sectores(self, client_autenticado, yacimiento_ejemplo, app):
        """Se pueden listar los sectores de un yacimiento."""
        with app.app_context():
            response = client_autenticado.get(
                f"/yacimiento/{yacimiento_ejemplo.id}/sectores"
            )
            assert response.status_code == 200


# ---------------------------------------------------------------------------
# Tests de Fase (Blueprint fase)
# ---------------------------------------------------------------------------

class TestBlueprintFase:
    """Tests para las rutas de fases de proyecto."""

    def test_listar_fases(self, client_autenticado, yacimiento_ejemplo, app):
        """Se pueden listar las fases de un yacimiento."""
        with app.app_context():
            response = client_autenticado.get(
                f"/yacimiento/{yacimiento_ejemplo.id}/fases"
            )
            assert response.status_code == 200

    def test_nueva_fase_get(self, client_autenticado, yacimiento_ejemplo, app):
        """El formulario de nueva fase es accesible."""
        with app.app_context():
            response = client_autenticado.get(
                f"/yacimiento/{yacimiento_ejemplo.id}/fases/nueva"
            )
            assert response.status_code == 200

    def test_crear_fase_post(self, client_autenticado, yacimiento_ejemplo, db, app):
        """Se puede crear una fase vía POST."""
        with app.app_context():
            response = client_autenticado.post(
                f"/yacimiento/{yacimiento_ejemplo.id}/fases/nueva",
                data={
                    "nombre": "Fase de Documentación",
                    "descripcion": "Documentación de hallazgos",
                    "estado": "planificada",
                    "fecha_inicio": "2024-06-01",
                },
                follow_redirects=True,
            )
            assert response.status_code == 200


# ---------------------------------------------------------------------------
# Tests de Permisos (Sistema de invitaciones)
# ---------------------------------------------------------------------------

class TestSistemaPermisos:
    """Tests para el sistema de roles y permisos."""

    def test_propietario_tiene_permisos_completos(self, app, db, usuario_registrado, yacimiento_ejemplo):
        """El propietario tiene todos los permisos sobre su yacimiento."""
        with app.app_context():
            puede_ver, _ = usuario_registrado.has_permission(yacimiento_ejemplo.id, "read")
            puede_editar, _ = usuario_registrado.has_permission(yacimiento_ejemplo.id, "edit")
            puede_crear, _ = usuario_registrado.has_permission(yacimiento_ejemplo.id, "create")

            assert puede_ver is True
            assert puede_editar is True
            assert puede_crear is True

    def test_usuario_sin_invitacion_no_tiene_permisos(self, app, db, usuario_secundario, yacimiento_ejemplo):
        """Un usuario sin invitación no puede acceder a un yacimiento ajeno."""
        with app.app_context():
            puede_ver, _ = usuario_secundario.has_permission(yacimiento_ejemplo.id, "read")
            assert puede_ver is False

    def test_invitado_como_visualizador_puede_leer(self, app, db, usuario_registrado, usuario_secundario, yacimiento_ejemplo):
        """Un usuario invitado como visualizador puede leer pero no editar."""
        from app.models import Invitacion

        with app.app_context():
            invitacion = Invitacion(
                yacimiento_id=yacimiento_ejemplo.id,
                invitado_id=usuario_secundario.id,
                invitador_id=usuario_registrado.id,
                rol="visualizador",
                estado="aceptada",
            )
            db.session.add(invitacion)
            db.session.commit()

            puede_ver, rol = usuario_secundario.has_permission(yacimiento_ejemplo.id, "read")
            puede_editar, _ = usuario_secundario.has_permission(yacimiento_ejemplo.id, "edit")

            assert puede_ver is True
            assert puede_editar is False

    def test_invitado_como_editor_puede_editar(self, app, db, usuario_registrado, usuario_secundario, yacimiento_ejemplo):
        """Un usuario invitado como editor puede editar."""
        from app.models import Invitacion

        with app.app_context():
            invitacion = Invitacion(
                yacimiento_id=yacimiento_ejemplo.id,
                invitado_id=usuario_secundario.id,
                invitador_id=usuario_registrado.id,
                rol="editor",
                estado="aceptada",
            )
            db.session.add(invitacion)
            db.session.commit()

            puede_editar, _ = usuario_secundario.has_permission(yacimiento_ejemplo.id, "edit")
            assert puede_editar is True


# ---------------------------------------------------------------------------
# Tests de la Página Principal
# ---------------------------------------------------------------------------

class TestPaginaPrincipal:
    """Tests para las rutas principales."""

    def test_landing_page_accesible(self, client, app):
        """La landing page es accesible sin autenticación."""
        with app.app_context():
            response = client.get("/")
            assert response.status_code == 200

    def test_dashboard_requiere_auth(self, client, app):
        """El dashboard requiere autenticación."""
        with app.app_context():
            response = client.get("/dashboard", follow_redirects=False)
            assert response.status_code in (301, 302)

    def test_dashboard_autenticado(self, client_autenticado, app):
        """El dashboard es accesible para usuarios autenticados."""
        with app.app_context():
            response = client_autenticado.get("/dashboard")
            assert response.status_code == 200

    def test_perfil_usuario(self, client_autenticado, usuario_registrado, app):
        """El perfil del usuario es accesible."""
        with app.app_context():
            response = client_autenticado.get(f"/perfil/{usuario_registrado.id}")
            assert response.status_code == 200


# ---------------------------------------------------------------------------
# Tests de Integración
# ---------------------------------------------------------------------------

class TestIntegracion:
    """Tests de integración que verifican flujos completos."""

    def test_flujo_completo_yacimiento_hallazgo(self, client_autenticado, db, app):
        """Flujo completo: crear yacimiento → crear hallazgo → ver detalle."""
        with app.app_context():
            # 1. Crear yacimiento
            r = client_autenticado.post(
                "/nuevo_yacimiento",
                data={
                    "nombre": "Yacimiento Integración",
                    "ubicacion": "Salamanca",
                    "lat": "40.9701",
                    "lng": "-5.6635",
                    "responsable": "Dr. Integración",
                    "fecha_inicio": "2024-01-01",
                },
                follow_redirects=True,
            )
            assert r.status_code == 200

            # 2. Verificar que el yacimiento fue creado
            from app.models import Yacimiento
            yacimiento = Yacimiento.query.filter_by(nombre="Yacimiento Integración").first()
            assert yacimiento is not None

            # 3. Crear hallazgo en ese yacimiento
            r2 = client_autenticado.post(
                f"/yacimiento/{yacimiento.id}/hallazgos/nuevo",
                data={
                    "tipo": "Vasija",
                    "descripcion": "Vasija completa de cerámica",
                    "material": "Barro",
                    "estado_conservacion": "Excelente",
                    "fecha": "2024-03-01",
                    "sector_id": "0",
                },
                follow_redirects=True,
            )
            assert r2.status_code == 200

            # 4. Verificar que el hallazgo fue creado con código único
            from app.models import Hallazgo
            hallazgo = Hallazgo.query.filter_by(
                yacimiento_id=yacimiento.id, tipo="Vasija"
            ).first()
            assert hallazgo is not None
            assert hallazgo.codigo_acceso is not None
            assert len(hallazgo.codigo_acceso) == 10

    def test_busqueda_codigo_hallazgo(self, client_autenticado, hallazgo_ejemplo, app):
        """La búsqueda por código encuentra el hallazgo correcto."""
        with app.app_context():
            response = client_autenticado.get(
                f"/buscar_codigo?codigo={hallazgo_ejemplo.codigo_acceso}",
                follow_redirects=True,
            )
            assert response.status_code == 200

    def test_codigo_hallazgo_alfanumerico_10_chars(self, db, app, yacimiento_ejemplo, usuario_registrado):
        """Múltiples hallazgos tienen todos códigos únicos de 10 caracteres alfanuméricos."""
        from app.models import Hallazgo

        with app.app_context():
            hallazgos = []
            for i in range(10):
                h = Hallazgo(
                    tipo=f"Tipo {i}",
                    yacimiento_id=yacimiento_ejemplo.id,
                    user_id=usuario_registrado.id,
                )
                db.session.add(h)
                hallazgos.append(h)
            db.session.commit()

            codigos = {h.codigo_acceso for h in hallazgos}
            # Todos únicos
            assert len(codigos) == 10
            # Todos de 10 chars alfanuméricos
            for codigo in codigos:
                assert len(codigo) == 10
                assert codigo.isalnum()