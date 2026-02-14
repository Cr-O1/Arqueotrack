from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Yacimiento, Hallazgo, Sector, FaseProyecto, Evento, Comentario, Invitacion
from app.utils import time_ago, is_safe_url
from app.forms import BuscarCodigoForm

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def portada():
    """Página de bienvenida"""
    if current_user.is_authenticated:
        return redirect(url_for('main.inicio'))
    return render_template('portada.html')

@main_bp.route('/inicio')
@login_required
def inicio():
    """Dashboard principal"""
    # Yacimientos propios
    yacimientos = Yacimiento.query.filter_by(user_id=current_user.id).all()
    
    # Yacimientos en colaboración
    invitaciones = Invitacion.query.filter_by(invitado_id=current_user.id, estado='aceptada').all()
    yacimientos_colaborando = [inv.yacimiento for inv in invitaciones]
    
    # Todos los yacimientos accesibles
    todos_yacimientos = yacimientos + yacimientos_colaborando
    
    # Estadísticas globales
    total_hallazgos = sum(y.total_hallazgos for y in todos_yacimientos) if todos_yacimientos else 0
    yacimientos_activos = sum(1 for y in todos_yacimientos if not y.fecha_fin) if todos_yacimientos else 0
    yacimientos_finalizados = sum(1 for y in todos_yacimientos if y.fecha_fin) if todos_yacimientos else 0
    
    yacimientos_json = [y.to_dict(include_relations=True) for y in yacimientos]
    
    return render_template(
        'inicio.html',
        yacimientos=yacimientos,
        yacimientos_colaborando=yacimientos_colaborando,
        total_hallazgos=total_hallazgos,
        yacimientos_activos=yacimientos_activos,
        yacimientos_finalizados=yacimientos_finalizados,
        yacimientos_json=yacimientos_json
    )

@main_bp.route('/perfil')
@login_required
def perfil():
    """Perfil del usuario"""
    total_yacimientos = Yacimiento.query.filter_by(user_id=current_user.id).count()
    total_hallazgos = Hallazgo.query.filter_by(user_id=current_user.id).count()
    total_eventos = Evento.query.filter_by(usuario_id=current_user.id).count()
    total_comentarios = Comentario.query.filter_by(usuario_id=current_user.id).count()

    return render_template(
        'perfil.html',
        usuario=current_user,
        total_yacimientos=total_yacimientos,
        total_hallazgos=total_hallazgos,
        total_eventos=total_eventos,
        total_comentarios=total_comentarios
    )

@main_bp.route('/eliminar_cuenta', methods=['POST'])
@login_required
def eliminar_cuenta():
    """Eliminar cuenta del usuario"""
    try:
        db.session.delete(current_user)
        db.session.commit()
        flash('Tu cuenta ha sido eliminada correctamente.', 'success')
        return redirect(url_for('main.portada'))
    except:
        db.session.rollback()
        flash('Error al eliminar la cuenta. Por favor, contacta al administrador.', 'error')
        return redirect(url_for('main.perfil'))

@main_bp.route('/buscar_codigo', methods=['GET', 'POST'])
@login_required
def buscar_codigo():
    """Buscar hallazgo por código"""
    form = BuscarCodigoForm()
    if form.validate_on_submit():
        codigo = form.codigo.data.upper()
        hallazgo = Hallazgo.query.filter_by(codigo_acceso=codigo).first()
        if hallazgo:
            # Verificar acceso
            es_propietario_yacimiento = hallazgo.yacimiento and hallazgo.yacimiento.user_id == current_user.id
            if hallazgo.user_id == current_user.id or es_propietario_yacimiento or Invitacion.query.filter_by(
                yacimiento_id=hallazgo.yacimiento_id,
                invitado_id=current_user.id,
                estado='aceptada'
            ).first():
                return redirect(url_for('hallazgo.detalle', hallazgo_id=hallazgo.id))
            else:
                flash('No tienes acceso a este hallazgo.', 'error')
        else:
            flash('Código no encontrado.', 'error')
    return render_template('buscar_codigo.html', formulario=form)
