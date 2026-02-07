from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Yacimiento, Hallazgo, Sector, FaseProyecto, Evento, Invitacion
from app.forms import YacimientoForm, EditarProcesoYacimientoForm
from app.utils import generar_codigo_unico, allowed_file, is_safe_url, time_ago
from werkzeug.utils import secure_filename
import os
import json
from geoalchemy2.shape import to_shape
from shapely.geometry import mapping

yacimiento_bp = Blueprint('yacimiento', __name__)

@yacimiento_bp.route('/nuevo_yacimiento', methods=['GET', 'POST'])
@login_required
def nuevo_yacimiento():
    """Crear nuevo yacimiento"""
    form = YacimientoForm()
    if form.validate_on_submit():
        try:
            yacimiento = Yacimiento(
                user_id=current_user.id,
                nombre=form.nombre.data,
                ubicacion=form.ubicacion.data,
                descripcion=form.descripcion.data,
                lat=form.lat.data,
                lng=form.lng.data,
                polygon_geojson=form.polygon_geojson.data,
                area_m2=form.area.data
            )
            db.session.add(yacimiento)
            db.session.commit()
            flash('Yacimiento creado exitosamente.', 'success')
            return redirect(url_for('yacimiento.detalle', yacimiento_id=yacimiento.id))
        except:
            db.session.rollback()
            flash('Error al crear el yacimiento.', 'error')
    return render_template('yacimientos/nuevo.html', form=form)

@yacimiento_bp.route('/yacimiento/<int:yacimiento_id>')
@login_required
def detalle(yacimiento_id):
    """Detalle del yacimiento"""
    yacimiento = Yacimiento.query.get_or_404(yacimiento_id)

    # Verificar acceso
    puede_editar = yacimiento.user_id == current_user.id or Invitacion.query.filter_by(
        yacimiento_id=yacimiento_id,
        invitado_id=current_user.id,
        estado='aceptada',
        rol='asistente'
    ).first()

    puede_crear = yacimiento.user_id == current_user.id or Invitacion.query.filter_by(
        yacimiento_id=yacimiento_id,
        invitado_id=current_user.id,
        estado='aceptada'
    ).filter(Invitacion.rol.in_(['colaborador', 'asistente'])).first()

    hallazgos = Hallazgo.query.filter_by(yacimiento_id=yacimiento_id).all()
    sectores = Sector.query.filter_by(yacimiento_id=yacimiento_id).all()
    fases = FaseProyecto.query.filter_by(yacimiento_id=yacimiento_id).all()

    return render_template(
        'yacimientos/detalle.html',
        yacimiento=yacimiento,
        hallazgos=hallazgos,
        sectores=sectores,
        fases=fases,
        puede_editar=puede_editar,
        puede_crear=puede_crear
    )

@yacimiento_bp.route('/editar_yacimiento/<int:yacimiento_id>', methods=['GET', 'POST'])
@login_required
def editar(yacimiento_id):
    """Editar yacimiento"""
    yacimiento = Yacimiento.query.get_or_404(yacimiento_id)
    if yacimiento.user_id != current_user.id:
        abort(403)

    form = YacimientoForm(obj=yacimiento)
    if form.validate_on_submit():
        try:
            yacimiento.nombre = form.nombre.data
            yacimiento.ubicacion = form.ubicacion.data
            yacimiento.descripcion = form.descripcion.data
            yacimiento.lat = form.lat.data
            yacimiento.lng = form.lng.data
            yacimiento.polygon_geojson = form.polygon_geojson.data
            yacimiento.area_m2 = form.area.data
            db.session.commit()
            flash('Yacimiento actualizado.', 'success')
            return redirect(url_for('yacimiento.detalle', yacimiento_id=yacimiento.id))
        except:
            db.session.rollback()
            flash('Error al actualizar.', 'error')
    return render_template('yacimientos/editar.html', form=form, yacimiento=yacimiento)

@yacimiento_bp.route('/eliminar_yacimiento/<int:yacimiento_id>', methods=['POST'])
@login_required
def eliminar(yacimiento_id):
    """Eliminar yacimiento"""
    yacimiento = Yacimiento.query.get_or_404(yacimiento_id)
    if yacimiento.user_id != current_user.id:
        abort(403)
    try:
        db.session.delete(yacimiento)
        db.session.commit()
        flash('Yacimiento eliminado.', 'success')
    except:
        db.session.rollback()
        flash('Error al eliminar.', 'error')
    return redirect(url_for('main.inicio'))

@yacimiento_bp.route('/proceso_yacimiento/<int:yacimiento_id>')
@login_required
def proceso(yacimiento_id):
    """Proceso de excavación"""
    yacimiento = Yacimiento.query.get_or_404(yacimiento_id)

    # Verificar acceso
    if yacimiento.user_id != current_user.id and not Invitacion.query.filter_by(
        yacimiento_id=yacimiento_id,
        invitado_id=current_user.id,
        estado='aceptada'
    ).first():
        abort(403)

    puede_editar = yacimiento.user_id == current_user.id or Invitacion.query.filter_by(
        yacimiento_id=yacimiento_id,
        invitado_id=current_user.id,
        estado='aceptada',
        rol='asistente'
    ).first()

    puede_crear = yacimiento.user_id == current_user.id or Invitacion.query.filter_by(
        yacimiento_id=yacimiento_id,
        invitado_id=current_user.id,
        estado='aceptada'
    ).filter(Invitacion.rol.in_(['colaborador', 'asistente'])).first()

    fases = FaseProyecto.query.filter_by(yacimiento_id=yacimiento_id).order_by(FaseProyecto.orden).all()
    eventos = Evento.query.filter_by(yacimiento_id=yacimiento_id).order_by(Evento.fecha.desc()).limit(5).all()

    return render_template(
        'yacimientos/proceso.html',
        yacimiento=yacimiento,
        fases=fases,
        eventos=eventos,
        puede_editar=puede_editar,
        puede_crear=puede_crear,
        time_ago=time_ago
    )

@yacimiento_bp.route('/editar_proceso_yacimiento/<int:yacimiento_id>', methods=['GET', 'POST'])
@login_required
def editar_proceso(yacimiento_id):
    """Editar proceso de excavación"""
    yacimiento = Yacimiento.query.get_or_404(yacimiento_id)
    if yacimiento.user_id != current_user.id:
        abort(403)

    form = EditarProcesoYacimientoForm(obj=yacimiento)
    if form.validate_on_submit():
        try:
            yacimiento.responsable = form.responsable.data
            yacimiento.fecha_inicio = form.fecha_inicio.data
            if form.esta_activo.data:
                yacimiento.fecha_fin = None
            else:
                yacimiento.fecha_fin = form.fecha_fin.data
            db.session.commit()
            flash('Proceso actualizado.', 'success')
            return redirect(url_for('yacimiento.proceso', yacimiento_id=yacimiento.id))
        except:
            db.session.rollback()
            flash('Error al actualizar.', 'error')
    return render_template('yacimientos/editar_proceso.html', form=form, yacimiento=yacimiento)
