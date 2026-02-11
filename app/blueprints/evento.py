from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app import db
from app.models import Evento, Yacimiento, FaseProyecto, Hallazgo, Sector
from app.forms import EventoForm
from app.utils import time_ago
from collections import Counter

evento_bp = Blueprint('evento', __name__)

@evento_bp.route('/yacimiento/<int:yacimiento_id>/timeline')
@login_required
def timeline(yacimiento_id):
    """Timeline del yacimiento"""
    yacimiento = Yacimiento.query.get_or_404(yacimiento_id)

    puede_ver, _ = current_user.has_permission(yacimiento_id, 'read')
    if not puede_ver:
        abort(403)

    eventos = Evento.query.filter_by(yacimiento_id=yacimiento_id).order_by(Evento.fecha.desc()).all()
    total_eventos = len(eventos)
    eventos_por_tipo = Counter(e.tipo for e in eventos)

    return render_template(
        'eventos/timeline.html',
        yacimiento=yacimiento,
        eventos=eventos,
        total_eventos=total_eventos,
        eventos_por_tipo=eventos_por_tipo,
        time_ago=time_ago
    )

@evento_bp.route('/yacimiento/<int:yacimiento_id>/evento/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo(yacimiento_id):
    """Crear nuevo evento"""
    yacimiento = Yacimiento.query.get_or_404(yacimiento_id)

    puede_crear, _ = current_user.has_permission(yacimiento_id, 'create')
    if not puede_crear:
        abort(403)

    form = EventoForm()
    form.fase_id.choices = [(0, 'Sin fase')] + [(f.id, f.nombre) for f in FaseProyecto.query.filter_by(yacimiento_id=yacimiento_id).all()]
    form.hallazgo_id.choices = [(0, 'Sin hallazgo')] + [(h.id, h.codigo_acceso) for h in Hallazgo.query.filter_by(yacimiento_id=yacimiento_id).all()]
    form.sector_id.choices = [(0, 'Sin sector')] + [(s.id, s.nombre) for s in Sector.query.filter_by(yacimiento_id=yacimiento_id).all()]

    if form.validate_on_submit():
        try:
            evento = Evento(
                yacimiento_id=yacimiento_id,
                usuario_id=current_user.id,
                tipo=form.tipo.data,
                titulo=form.titulo.data,
                descripcion=form.descripcion.data,
                fecha=form.fecha.data,
                fase_id=form.fase_id.data if form.fase_id.data != 0 else None,
                hallazgo_id=form.hallazgo_id.data if form.hallazgo_id.data != 0 else None,
                sector_id=form.sector_id.data if form.sector_id.data != 0 else None,
                prioridad=form.prioridad.data,
                estado_evento=form.estado_evento.data,
                participantes=form.participantes.data,
                resultados=form.resultados.data
            )
            db.session.add(evento)
            db.session.commit()
            flash('Evento registrado.', 'success')
            return redirect(url_for('evento.timeline', yacimiento_id=yacimiento_id))
        except:
            db.session.rollback()
            flash('Error al registrar.', 'error')
    return render_template('eventos/nuevo.html', formulario=form, yacimiento=yacimiento)

@evento_bp.route('/editar_evento/<int:evento_id>', methods=['GET', 'POST'])
@login_required
def editar(evento_id):
    """Editar evento"""
    evento = Evento.query.get_or_404(evento_id)

    puede_editar, _ = current_user.has_permission(evento.yacimiento_id, 'edit')
    if evento.usuario_id != current_user.id and not puede_editar:
        abort(403)

    form = EventoForm(obj=evento)
    form.fase_id.choices = [(0, 'Sin fase')] + [(f.id, f.nombre) for f in FaseProyecto.query.filter_by(yacimiento_id=evento.yacimiento_id).all()]
    form.hallazgo_id.choices = [(0, 'Sin hallazgo')] + [(h.id, h.codigo_acceso) for h in Hallazgo.query.filter_by(yacimiento_id=evento.yacimiento_id).all()]
    form.sector_id.choices = [(0, 'Sin sector')] + [(s.id, s.nombre) for s in Sector.query.filter_by(yacimiento_id=evento.yacimiento_id).all()]

    if form.validate_on_submit():
        try:
            evento.tipo = form.tipo.data
            evento.titulo = form.titulo.data
            evento.descripcion = form.descripcion.data
            evento.fecha = form.fecha.data
            evento.fase_id = form.fase_id.data if form.fase_id.data != 0 else None
            evento.hallazgo_id = form.hallazgo_id.data if form.hallazgo_id.data != 0 else None
            evento.sector_id = form.sector_id.data if form.sector_id.data != 0 else None
            evento.prioridad = form.prioridad.data
            evento.estado_evento = form.estado_evento.data
            evento.participantes = form.participantes.data
            evento.resultados = form.resultados.data
            db.session.commit()
            flash('Evento actualizado.', 'success')
            return redirect(url_for('evento.timeline', yacimiento_id=evento.yacimiento_id))
        except:
            db.session.rollback()
            flash('Error al actualizar.', 'error')
    return render_template('eventos/editar.html', formulario=form, evento=evento)

@evento_bp.route('/eliminar_evento/<int:evento_id>', methods=['POST'])
@login_required
def eliminar(evento_id):
    """Eliminar evento"""
    evento = Evento.query.get_or_404(evento_id)
    puede_eliminar, _ = current_user.has_permission(evento.yacimiento_id, 'delete')
    if evento.usuario_id != current_user.id and not puede_eliminar:
        abort(403)
    try:
        db.session.delete(evento)
        db.session.commit()
        flash('Evento eliminado.', 'success')
    except:
        db.session.rollback()
        flash('Error al eliminar.', 'error')
    return redirect(url_for('evento.timeline', yacimiento_id=evento.yacimiento_id))
