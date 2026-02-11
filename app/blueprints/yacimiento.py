from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app import db
from app.models import Yacimiento, Hallazgo, Sector, FaseProyecto, Evento
from app.forms import YacimientoForm, EditarProcesoYacimientoForm
from app.utils import time_ago
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
                area_m2=form.area.data,
                responsable=form.responsable.data,
                fecha_inicio=form.fecha_inicio.data,
                fecha_fin=form.fecha_fin.data,
                altitud_media=form.altitud_media.data
            )
            db.session.add(yacimiento)
            db.session.commit()
            flash('Yacimiento creado exitosamente.', 'success')
            return redirect(url_for('yacimiento.detalle', yacimiento_id=yacimiento.id))
        except:
            db.session.rollback()
            flash('Error al crear el yacimiento.', 'error')
    return render_template('yacimientos/nuevo.html', formulario=form)

@yacimiento_bp.route('/yacimiento/<int:yacimiento_id>')
@login_required
def detalle(yacimiento_id):
    """Detalle del yacimiento"""
    yacimiento = Yacimiento.query.get_or_404(yacimiento_id)

    puede_ver, rol_invitado = current_user.has_permission(yacimiento_id, 'read')
    if not puede_ver:
        abort(403)

    puede_editar, _ = current_user.has_permission(yacimiento_id, 'edit')
    puede_crear, _ = current_user.has_permission(yacimiento_id, 'create')

    hallazgos = Hallazgo.query.filter_by(yacimiento_id=yacimiento_id).all()
    sectores = Sector.query.filter_by(yacimiento_id=yacimiento_id).all()
    fases = FaseProyecto.query.filter_by(yacimiento_id=yacimiento_id).all()
    es_propietario = yacimiento.user_id == current_user.id
    rol_usuario = 'propietario' if es_propietario else rol_invitado
    total_hallazgos = len(hallazgos)
    total_sectores = len(sectores)
    total_fases = len(fases)
    hallazgos_con_foto = sum(1 for h in hallazgos if h.foto)
    sectores_json = [s.to_dict() for s in sectores]

    return render_template(
        'yacimientos/detalle.html',
        yacimiento=yacimiento,
        hallazgos=hallazgos,
        sectores=sectores,
        fases=fases,
        puede_editar=puede_editar,
        puede_crear=puede_crear,
        es_propietario=es_propietario,
        rol_usuario=rol_usuario,
        total_hallazgos=total_hallazgos,
        total_sectores=total_sectores,
        total_fases=total_fases,
        hallazgos_con_foto=hallazgos_con_foto,
        sectores_json=sectores_json
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
            yacimiento.responsable = form.responsable.data
            yacimiento.fecha_inicio = form.fecha_inicio.data
            yacimiento.fecha_fin = form.fecha_fin.data
            yacimiento.altitud_media = form.altitud_media.data
            db.session.commit()
            flash('Yacimiento actualizado.', 'success')
            return redirect(url_for('yacimiento.detalle', yacimiento_id=yacimiento.id))
        except:
            db.session.rollback()
            flash('Error al actualizar.', 'error')
    return render_template('yacimientos/editar.html', formulario=form, yacimiento=yacimiento)

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
    puede_ver, _ = current_user.has_permission(yacimiento_id, 'read')
    if not puede_ver:
        abort(403)

    puede_editar, _ = current_user.has_permission(yacimiento_id, 'edit')
    puede_crear, _ = current_user.has_permission(yacimiento_id, 'create')

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
    return render_template('yacimientos/editar_proceso.html', formulario=form, yacimiento=yacimiento)
