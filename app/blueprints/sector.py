from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Sector, Yacimiento, Hallazgo, Invitacion
from app.forms import SectorForm
from app.utils import time_ago

sector_bp = Blueprint('sector', __name__)

@sector_bp.route('/yacimiento/<int:yacimiento_id>/nuevo_sector', methods=['GET', 'POST'])
@login_required
def nuevo_sector(yacimiento_id):
    """Crear nuevo sector"""
    yacimiento = Yacimiento.query.get_or_404(yacimiento_id)

    if yacimiento.user_id != current_user.id and not Invitacion.query.filter_by(
        yacimiento_id=yacimiento_id,
        invitado_id=current_user.id,
        estado='aceptada'
    ).filter(Invitacion.rol.in_(['colaborador', 'asistente'])).first():
        abort(403)

    form = SectorForm()
    if form.validate_on_submit():
        try:
            sector = Sector(
                yacimiento_id=yacimiento_id,
                nombre=form.nombre.data,
                descripcion=form.descripcion.data,
                color=form.color.data,
                lat=form.lat.data,
                lng=form.lng.data,
                polygon_geojson=form.polygon_geojson.data,
                area=form.area.data
            )
            db.session.add(sector)
            db.session.commit()
            flash('Sector creado.', 'success')
            return redirect(url_for('sector.listar', yacimiento_id=yacimiento_id))
        except:
            db.session.rollback()
            flash('Error al crear.', 'error')
    return render_template('sectores/nuevo.html', formulario=form, yacimiento=yacimiento)

@sector_bp.route('/yacimiento/<int:yacimiento_id>/sectores')
@login_required
def listar(yacimiento_id):
    """Listar sectores"""
    yacimiento = Yacimiento.query.get_or_404(yacimiento_id)

    if yacimiento.user_id != current_user.id and not Invitacion.query.filter_by(
        yacimiento_id=yacimiento_id,
        invitado_id=current_user.id,
        estado='aceptada'
    ).first():
        abort(403)

    invitacion_aceptada = Invitacion.query.filter_by(
        yacimiento_id=yacimiento_id,
        invitado_id=current_user.id,
        estado='aceptada'
    ).first()

    puede_crear = yacimiento.user_id == current_user.id or (
        invitacion_aceptada and invitacion_aceptada.rol in ['colaborador', 'asistente']
    )
    puede_editar_sectores = yacimiento.user_id == current_user.id or (
        invitacion_aceptada and invitacion_aceptada.rol in ['editor', 'asistente']
    )
    puede_eliminar_sectores = yacimiento.user_id == current_user.id

    sectores = Sector.query.filter_by(yacimiento_id=yacimiento_id).all()
    sectores_json = [s.to_dict() for s in sectores]
    total_hallazgos = sum(s.hallazgos.count() for s in sectores)

    return render_template(
        'sectores/listar.html',
        yacimiento=yacimiento,
        sectores=sectores,
        sectores_json=sectores_json,
        puede_crear=puede_crear,
        puede_editar_sectores=puede_editar_sectores,
        puede_eliminar_sectores=puede_eliminar_sectores,
        total_hallazgos=total_hallazgos
    )

@sector_bp.route('/yacimiento/<int:yacimiento_id>/mapa_sectores')
@login_required
def mapa_sectores(yacimiento_id):
    """Mapa de sectores"""
    yacimiento = Yacimiento.query.get_or_404(yacimiento_id)

    if yacimiento.user_id != current_user.id and not Invitacion.query.filter_by(
        yacimiento_id=yacimiento_id,
        invitado_id=current_user.id,
        estado='aceptada'
    ).first():
        abort(403)

    sectores = Sector.query.filter_by(yacimiento_id=yacimiento_id).all()
    sectores_json = [s.to_dict(include_relations=True) for s in sectores]

    hallazgos = Hallazgo.query.filter_by(yacimiento_id=yacimiento_id).all()
    hallazgos_json = [h.to_dict() for h in hallazgos]

    return render_template(
        'sectores/mapa_sectores.html',
        yacimiento=yacimiento,
        sectores_json=sectores_json,
        hallazgos_json=hallazgos_json
    )

@sector_bp.route('/sector/<int:sector_id>')
@login_required
def detalle(sector_id):
    """Detalle del sector"""
    sector = Sector.query.get_or_404(sector_id)

    if sector.yacimiento.user_id != current_user.id and not Invitacion.query.filter_by(
        yacimiento_id=sector.yacimiento_id,
        invitado_id=current_user.id,
        estado='aceptada'
    ).first():
        abort(403)

    return render_template('sectores/detalle.html', sector=sector)

@sector_bp.route('/editar_sector/<int:sector_id>', methods=['GET', 'POST'])
@login_required
def editar(sector_id):
    """Editar sector"""
    sector = Sector.query.get_or_404(sector_id)

    if sector.yacimiento.user_id != current_user.id and not Invitacion.query.filter_by(
        yacimiento_id=sector.yacimiento_id,
        invitado_id=current_user.id,
        estado='aceptada',
        rol='editor'
    ).first():
        abort(403)

    form = SectorForm(obj=sector)
    if form.validate_on_submit():
        try:
            sector.nombre = form.nombre.data
            sector.descripcion = form.descripcion.data
            sector.color = form.color.data
            sector.lat = form.lat.data
            sector.lng = form.lng.data
            sector.polygon_geojson = form.polygon_geojson.data
            sector.area = form.area.data
            db.session.commit()
            flash('Sector actualizado.', 'success')
            return redirect(url_for('sector.detalle', sector_id=sector.id))
        except:
            db.session.rollback()
            flash('Error al actualizar.', 'error')
    return render_template('sectores/editar.html', formulario=form, sector=sector)

@sector_bp.route('/eliminar_sector/<int:sector_id>', methods=['POST'])
@login_required
def eliminar(sector_id):
    """Eliminar sector"""
    sector = Sector.query.get_or_404(sector_id)
    if sector.yacimiento.user_id != current_user.id:
        abort(403)
    try:
        db.session.delete(sector)
        db.session.commit()
        flash('Sector eliminado.', 'success')
    except:
        db.session.rollback()
        flash('Error al eliminar.', 'error')
    return redirect(url_for('sector.listar', yacimiento_id=sector.yacimiento_id))
