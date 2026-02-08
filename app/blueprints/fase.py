from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app import db
from app.models import FaseProyecto, Yacimiento, Evento, Invitacion
from app.forms import FaseForm
from app.utils import time_ago

fase_bp = Blueprint('fase', __name__)

@fase_bp.route('/yacimiento/<int:yacimiento_id>/fases/nueva', methods=['GET', 'POST'])
@login_required
def nueva(yacimiento_id):
    """Crear nueva fase"""
    yacimiento = Yacimiento.query.get_or_404(yacimiento_id)

    if yacimiento.user_id != current_user.id and not Invitacion.query.filter_by(
        yacimiento_id=yacimiento_id,
        invitado_id=current_user.id,
        estado='aceptada'
    ).filter(Invitacion.rol.in_(['colaborador', 'asistente'])).first():
        abort(403)

    form = FaseForm()
    if form.validate_on_submit():
        try:
            fase = FaseProyecto(
                yacimiento_id=yacimiento_id,
                nombre=form.nombre.data,
                descripcion=form.descripcion.data,
                estado=form.estado.data,
                fecha_inicio=form.fecha_inicio.data,
                fecha_fin=form.fecha_fin.data
            )
            db.session.add(fase)
            db.session.commit()
            flash('Fase creada.', 'success')
            return redirect(url_for('fase.listar', yacimiento_id=yacimiento_id))
        except:
            db.session.rollback()
            flash('Error al crear.', 'error')
    return render_template('fases/nueva.html', formulario=form, yacimiento=yacimiento)

@fase_bp.route('/yacimiento/<int:yacimiento_id>/fases')
@login_required
def listar(yacimiento_id):
    """Listar fases"""
    yacimiento = Yacimiento.query.get_or_404(yacimiento_id)

    if yacimiento.user_id != current_user.id and not Invitacion.query.filter_by(
        yacimiento_id=yacimiento_id,
        invitado_id=current_user.id,
        estado='aceptada'
    ).first():
        abort(403)

    fases = FaseProyecto.query.filter_by(yacimiento_id=yacimiento_id).order_by(FaseProyecto.orden).all()

    return render_template(
        'fases/listar.html',
        yacimiento=yacimiento,
        fases=fases
    )

@fase_bp.route('/fase/<int:fase_id>')
@login_required
def detalle(fase_id):
    """Detalle de fase"""
    fase = FaseProyecto.query.get_or_404(fase_id)

    if fase.yacimiento.user_id != current_user.id and not Invitacion.query.filter_by(
        yacimiento_id=fase.yacimiento_id,
        invitado_id=current_user.id,
        estado='aceptada'
    ).first():
        abort(403)

    eventos = Evento.query.filter_by(fase_id=fase_id).order_by(Evento.fecha.desc()).all()

    return render_template(
        'fases/detalle.html',
        fase=fase,
        eventos=eventos,
        time_ago=time_ago
    )

@fase_bp.route('/editar_fase/<int:fase_id>', methods=['GET', 'POST'])
@login_required
def editar(fase_id):
    """Editar fase"""
    fase = FaseProyecto.query.get_or_404(fase_id)

    if fase.yacimiento.user_id != current_user.id and not Invitacion.query.filter_by(
        yacimiento_id=fase.yacimiento_id,
        invitado_id=current_user.id,
        estado='aceptada',
        rol='editor'
    ).first():
        abort(403)

    form = FaseForm(obj=fase)
    if form.validate_on_submit():
        try:
            fase.nombre = form.nombre.data
            fase.descripcion = form.descripcion.data
            fase.estado = form.estado.data
            fase.fecha_inicio = form.fecha_inicio.data
            fase.fecha_fin = form.fecha_fin.data
            db.session.commit()
            flash('Fase actualizada.', 'success')
            return redirect(url_for('fase.detalle', fase_id=fase.id))
        except:
            db.session.rollback()
            flash('Error al actualizar.', 'error')
    return render_template('fases/editar.html', formulario=form, fase=fase)

@fase_bp.route('/eliminar_fase/<int:fase_id>', methods=['POST'])
@login_required
def eliminar(fase_id):
    """Eliminar fase"""
    fase = FaseProyecto.query.get_or_404(fase_id)
    if fase.yacimiento.user_id != current_user.id:
        abort(403)
    try:
        db.session.delete(fase)
        db.session.commit()
        flash('Fase eliminada.', 'success')
    except:
        db.session.rollback()
        flash('Error al eliminar.', 'error')
    return redirect(url_for('fase.listar', yacimiento_id=fase.yacimiento_id))
