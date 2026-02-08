from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, current_app
from flask_login import login_required, current_user
from app import db
from app.models import Hallazgo, Yacimiento, Sector, Comentario, Invitacion
from app.forms import HallazgoForm
from app.utils import generar_codigo_unico, allowed_file, time_ago
from werkzeug.utils import secure_filename
import os

hallazgo_bp = Blueprint('hallazgo', __name__)

@hallazgo_bp.route('/nuevo_hallazgo/<int:yacimiento_id>', methods=['GET', 'POST'])
@login_required
def nuevo(yacimiento_id):
    """Crear nuevo hallazgo"""
    yacimiento = Yacimiento.query.get_or_404(yacimiento_id)

    # Verificar permiso
    if yacimiento.user_id != current_user.id and not Invitacion.query.filter_by(
        yacimiento_id=yacimiento_id,
        invitado_id=current_user.id,
        estado='aceptada'
    ).filter(Invitacion.rol.in_(['colaborador', 'asistente'])).first():
        abort(403)

    form = HallazgoForm()
    form.sector_id.choices = [(0, 'Sin sector')] + [(s.id, s.nombre) for s in Sector.query.filter_by(yacimiento_id=yacimiento_id).all()]

    if form.validate_on_submit():
        try:
            codigo = generar_codigo_unico()
            hallazgo = Hallazgo(
                user_id=current_user.id,
                yacimiento_id=yacimiento_id,
                sector_id=form.sector_id.data if form.sector_id.data != 0 else None,
                encontrado_por_id=current_user.id,
                tipo=form.tipo.data,
                material=form.material.data,
                datacion=form.datacion.data,
                dimensiones=form.dimensiones.data,
                peso=form.peso.data,
                estado_conservacion=form.estado_conservacion.data,
                descripcion=form.descripcion.data,
                lat=form.lat.data,
                lng=form.lng.data,
                fecha=form.fecha.data,
                codigo_acceso=codigo
            )

            if 'foto' in request.files:
                file = request.files['foto']
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                    hallazgo.foto = filename

            db.session.add(hallazgo)
            db.session.commit()
            flash('Hallazgo registrado.', 'success')
            return redirect(url_for('hallazgo.detalle', hallazgo_id=hallazgo.id))
        except:
            db.session.rollback()
            flash('Error al registrar.', 'error')
    return render_template('hallazgos/nuevo.html', formulario=form, yacimiento=yacimiento)

@hallazgo_bp.route('/hallazgo/<int:hallazgo_id>')
@login_required
def detalle(hallazgo_id):
    """Detalle del hallazgo"""
    hallazgo = Hallazgo.query.get_or_404(hallazgo_id)

    # Verificar acceso
    es_propietario_yacimiento = hallazgo.yacimiento and hallazgo.yacimiento.user_id == current_user.id
    if hallazgo.user_id != current_user.id and not es_propietario_yacimiento and not Invitacion.query.filter_by(
        yacimiento_id=hallazgo.yacimiento_id,
        invitado_id=current_user.id,
        estado='aceptada'
    ).first():
        abort(403)

    puede_editar = hallazgo.user_id == current_user.id or es_propietario_yacimiento or Invitacion.query.filter_by(
        yacimiento_id=hallazgo.yacimiento_id,
        invitado_id=current_user.id,
        estado='aceptada',
        rol='editor'  
    ).first() or Invitacion.query.filter_by(
        yacimiento_id=hallazgo.yacimiento_id,
        invitado_id=current_user.id,
        estado='aceptada',
        rol='asistente'
    ).first()

    comentarios = Comentario.query.filter_by(hallazgo_id=hallazgo_id).order_by(Comentario.fecha.desc()).all()

    return render_template(
        'hallazgos/detalle.html',
        hallazgo=hallazgo,
        comentarios=comentarios,
        puede_editar=puede_editar,
        time_ago=time_ago
    )

@hallazgo_bp.route('/editar_hallazgo/<int:hallazgo_id>', methods=['GET', 'POST'])
@login_required
def editar(hallazgo_id):
    """Editar hallazgo"""
    hallazgo = Hallazgo.query.get_or_404(hallazgo_id)

    es_propietario_yacimiento = hallazgo.yacimiento and hallazgo.yacimiento.user_id == current_user.id
    if hallazgo.user_id != current_user.id and not es_propietario_yacimiento and not Invitacion.query.filter_by(
        yacimiento_id=hallazgo.yacimiento_id,
        invitado_id=current_user.id,
        estado='aceptada',
        rol='editor'
    ).first():
        abort(403)

    form = HallazgoForm(obj=hallazgo)
    form.sector_id.choices = [(0, 'Sin sector')] + [(s.id, s.nombre) for s in Sector.query.filter_by(yacimiento_id=hallazgo.yacimiento_id).all()]

    if form.validate_on_submit():
        try:
            hallazgo.tipo = form.tipo.data
            hallazgo.material = form.material.data
            hallazgo.datacion = form.datacion.data
            hallazgo.dimensiones = form.dimensiones.data
            hallazgo.peso = form.peso.data
            hallazgo.estado_conservacion = form.estado_conservacion.data
            hallazgo.descripcion = form.descripcion.data
            hallazgo.lat = form.lat.data
            hallazgo.lng = form.lng.data
            hallazgo.fecha = form.fecha.data
            hallazgo.sector_id = form.sector_id.data if form.sector_id.data != 0 else None

            if 'foto' in request.files:
                file = request.files['foto']
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                    hallazgo.foto = filename

            db.session.commit()
            flash('Hallazgo actualizado.', 'success')
            return redirect(url_for('hallazgo.detalle', hallazgo_id=hallazgo.id))
        except:
            db.session.rollback()
            flash('Error al actualizar.', 'error')
    return render_template('hallazgos/editar.html', formulario=form, hallazgo=hallazgo)

@hallazgo_bp.route('/eliminar_hallazgo/<int:hallazgo_id>', methods=['POST'])
@login_required
def eliminar(hallazgo_id):
    """Eliminar hallazgo"""
    hallazgo = Hallazgo.query.get_or_404(hallazgo_id)
    if hallazgo.user_id != current_user.id and hallazgo.yacimiento.user_id != current_user.id:
        abort(403)
    try:
        db.session.delete(hallazgo)
        db.session.commit()
        flash('Hallazgo eliminado.', 'success')
    except:
        db.session.rollback()
        flash('Error al eliminar.', 'error')
    return redirect(url_for('yacimiento.detalle', yacimiento_id=hallazgo.yacimiento_id))

@hallazgo_bp.route('/comentar_hallazgo/<int:hallazgo_id>', methods=['POST'])
@login_required
def comentar(hallazgo_id):
    """Añadir comentario"""
    hallazgo = Hallazgo.query.get_or_404(hallazgo_id)

    # Verificar acceso
    es_propietario_yacimiento = hallazgo.yacimiento and hallazgo.yacimiento.user_id == current_user.id
    if hallazgo.user_id != current_user.id and not es_propietario_yacimiento and not Invitacion.query.filter_by(
        yacimiento_id=hallazgo.yacimiento_id,
        invitado_id=current_user.id,
        estado='aceptada'
    ).first():
        abort(403)

    texto = request.form.get('texto')
    if texto:
        comentario = Comentario(
            hallazgo_id=hallazgo_id,
            usuario_id=current_user.id,
            texto=texto
        )
        db.session.add(comentario)
        db.session.commit()
        flash('Comentario añadido.', 'success')
    return redirect(url_for('hallazgo.detalle', hallazgo_id=hallazgo_id))

@hallazgo_bp.route('/eliminar_comentario/<int:comentario_id>', methods=['POST'])
@login_required
def eliminar_comentario(comentario_id):
    """Eliminar comentario"""
    comentario = Comentario.query.get_or_404(comentario_id)
    if comentario.usuario_id != current_user.id and comentario.hallazgo.user_id != current_user.id and comentario.hallazgo.yacimiento.user_id != current_user.id:
        abort(403)
    db.session.delete(comentario)
    db.session.commit()
    flash('Comentario eliminado.', 'success')
    return redirect(url_for('hallazgo.detalle', hallazgo_id=comentario.hallazgo_id))
