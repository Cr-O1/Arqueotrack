from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app import db
from app.models import Invitacion, Yacimiento, Usuario
from app.forms import InvitacionForm

invitacion_bp = Blueprint('invitacion', __name__)

@invitacion_bp.route('/yacimiento/<int:yacimiento_id>/invitar', methods=['GET', 'POST'])
@login_required
def invitar(yacimiento_id):
    """Enviar invitación"""
    yacimiento = Yacimiento.query.get_or_404(yacimiento_id)
    if yacimiento.user_id != current_user.id:
        abort(403)

    form = InvitacionForm()
    if form.validate_on_submit():
        email = form.email.data
        usuario = Usuario.query.filter_by(email=email).first()
        if not usuario:
            flash('Usuario no encontrado.', 'error')
            return render_template('invitaciones/nueva.html', form=form, yacimiento=yacimiento)

        if Invitacion.query.filter_by(yacimiento_id=yacimiento_id, invitado_id=usuario.id).first():
            flash('Ya existe una invitación para este usuario.', 'error')
            return render_template('invitaciones/nueva.html', form=form, yacimiento=yacimiento)

        try:
            invitacion = Invitacion(
                yacimiento_id=yacimiento_id,
                invitado_id=usuario.id,
                invitado_por_id=current_user.id,
                email=email,
                rol=form.rol.data,
                mensaje=form.mensaje.data
            )
            db.session.add(invitacion)
            db.session.commit()
            flash('Invitación enviada.', 'success')
            return redirect(url_for('invitacion.gestionar', yacimiento_id=yacimiento_id))
        except:
            db.session.rollback()
            flash('Error al enviar.', 'error')
    return render_template('invitaciones/nueva.html', form=form, yacimiento=yacimiento)

@invitacion_bp.route('/yacimiento/<int:yacimiento_id>/invitaciones')
@login_required
def gestionar(yacimiento_id):
    """Gestionar invitaciones"""
    yacimiento = Yacimiento.query.get_or_404(yacimiento_id)
    if yacimiento.user_id != current_user.id:
        abort(403)

    invitaciones = Invitacion.query.filter_by(yacimiento_id=yacimiento_id).all()
    invitaciones_pendientes = [i for i in invitaciones if i.estado == 'pendiente']
    colaboradores = [i for i in invitaciones if i.estado == 'aceptada']

    return render_template(
        'invitaciones/gestionar.html',
        yacimiento=yacimiento,
        invitaciones=invitaciones,
        invitaciones_pendientes=invitaciones_pendientes,
        colaboradores=colaboradores
    )

@invitacion_bp.route('/mis_invitaciones')
@login_required
def mis_invitaciones():
    """Mis invitaciones pendientes"""
    invitaciones = Invitacion.query.filter_by(invitado_id=current_user.id, estado='pendiente').all()
    return render_template('invitaciones/mis_invitaciones.html', invitaciones=invitaciones)

@invitacion_bp.route('/aceptar_invitacion/<int:invitacion_id>', methods=['POST'])
@login_required
def aceptar(invitacion_id):
    """Aceptar invitación"""
    invitacion = Invitacion.query.get_or_404(invitacion_id)
    if invitacion.invitado_id != current_user.id:
        abort(403)
    invitacion.estado = 'aceptada'
    invitacion.fecha_respuesta = datetime.utcnow()
    db.session.commit()
    flash('Invitación aceptada.', 'success')
    return redirect(url_for('invitacion.mis_invitaciones'))

@invitacion_bp.route('/rechazar_invitacion/<int:invitacion_id>', methods=['POST'])
@login_required
def rechazar(invitacion_id):
    """Rechazar invitación"""
    invitacion = Invitacion.query.get_or_404(invitacion_id)
    if invitacion.invitado_id != current_user.id:
        abort(403)
    invitacion.estado = 'rechazada'
    invitacion.fecha_respuesta = datetime.utcnow()
    db.session.commit()
    flash('Invitación rechazada.', 'success')
    return redirect(url_for('invitacion.mis_invitaciones'))

@invitacion_bp.route('/revocar_invitacion/<int:invitacion_id>', methods=['POST'])
@login_required
def revocar(invitacion_id):
    """Revocar invitación"""
    invitacion = Invitacion.query.get_or_404(invitacion_id)
    if invitacion.invitado_por_id != current_user.id:
        abort(403)
    db.session.delete(invitacion)
    db.session.commit()
    flash('Invitación revocada.', 'success')
    return redirect(url_for('invitacion.gestionar', yacimiento_id=invitacion.yacimiento_id))
