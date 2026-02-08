from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db, bcrypt
from app.models.user import Usuario
from app.forms import RegistroForm, LoginForm
from app.utils import is_safe_url
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/registro', methods=['GET', 'POST'])
def registro():
    """Página de registro de nuevos usuarios"""
    if current_user.is_authenticated:
        return redirect(url_for('main.inicio'))

    form = RegistroForm()
    if form.validate_on_submit():
        print("DEBUG: Form validated successfully")
        try:
            nuevo_usuario = Usuario(
                nombre_usuario=form.nombre_usuario.data,
                nombre=form.nombre.data,
                apellidos=form.apellidos.data,
                email=form.correo_electronico.data,
                fecha_nacimiento=form.fecha_nacimiento.data,
                ocupacion=form.ocupacion.data
            )
            nuevo_usuario.set_password(form.contraseña.data)
            db.session.add(nuevo_usuario)
            db.session.commit()
            flash('¡Cuenta creada exitosamente! Por favor inicia sesión.', 'success')
            return redirect(url_for('auth.iniciar_sesion'))
        except Exception as e:
            print(f"DEBUG: Exception during registration: {e}")
            db.session.rollback()
            flash(f'Error al registrar: {str(e)}', 'error')
    else:
        if request.method == 'POST':
            # print(f"DEBUG: Form validation failed. Errors: {form.errors}")
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"Error en {getattr(form, field).label.text}: {error}", 'error')
    return render_template('registro.html', formulario=form)

@auth_bp.route('/iniciar-sesion', methods=['GET', 'POST'])
def iniciar_sesion():
    """Página de inicio de sesión"""
    if current_user.is_authenticated:
        return redirect(url_for('main.inicio'))

    form = LoginForm()
    if form.validate_on_submit():
        usuario = Usuario.query.filter_by(email=form.correo_electronico.data).first()
        if usuario and usuario.check_password(form.contraseña.data):
            login_user(usuario)
            next_page = request.args.get('next')
            if next_page and is_safe_url(next_page):
                return redirect(next_page)
            return redirect(url_for('main.inicio'))
        flash('Credenciales inválidas', 'error')
    return render_template('iniciar_sesion.html', formulario=form)

@auth_bp.route('/cerrar-sesion')
@login_required
def cerrar_sesion():
    """Cierre de sesión"""
    logout_user()
    flash('Has cerrado sesión correctamente', 'success')
    return redirect(url_for('main.portada'))