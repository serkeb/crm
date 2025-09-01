from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.database import db, User, Customer
from datetime import datetime

customers_bp = Blueprint('customers', __name__)

def get_current_user():
    user_id = get_jwt_identity()
    return User.query.get(user_id)

@customers_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_customer_profile():
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        customer = user.customer
        
        return jsonify({
            'customer': {
                'id': customer.id,
                'name': customer.name,
                'email': customer.email,
                'phone': customer.phone,
                'company': customer.company,
                'subscription_plan': customer.subscription_plan,
                'is_active': customer.is_active,
                'settings': customer.settings or {},
                'created_at': customer.created_at.isoformat(),
                'updated_at': customer.updated_at.isoformat()
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Error interno del servidor'}), 500

@customers_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_customer_profile():
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        # Solo administradores pueden actualizar el perfil del cliente
        if user.role != 'admin':
            return jsonify({'error': 'Permisos insuficientes'}), 403
        
        data = request.get_json()
        customer = user.customer
        
        # Campos actualizables
        if 'name' in data:
            customer.name = data['name']
        if 'phone' in data:
            customer.phone = data['phone']
        if 'company' in data:
            customer.company = data['company']
        
        customer.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Perfil actualizado exitosamente',
            'customer': {
                'id': customer.id,
                'name': customer.name,
                'email': customer.email,
                'phone': customer.phone,
                'company': customer.company,
                'subscription_plan': customer.subscription_plan
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error interno del servidor'}), 500

@customers_bp.route('/settings', methods=['GET'])
@jwt_required()
def get_customer_settings():
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        customer = user.customer
        settings = customer.settings or {}
        
        # Configuraciones por defecto
        default_settings = {
            'notifications': {
                'email': True,
                'browser': True,
                'new_messages': True,
                'new_tickets': True,
                'assignments': True
            },
            'ui': {
                'theme': 'light',
                'language': 'es',
                'timezone': 'America/Mexico_City'
            },
            'integrations': {
                'whatsapp_enabled': False,
                'instagram_enabled': False,
                'messenger_enabled': False
            }
        }
        
        # Combinar configuraciones por defecto con las personalizadas
        merged_settings = {**default_settings, **settings}
        
        return jsonify({
            'settings': merged_settings
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Error interno del servidor'}), 500

@customers_bp.route('/settings', methods=['PUT'])
@jwt_required()
def update_customer_settings():
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        data = request.get_json()
        customer = user.customer
        
        # Actualizar configuraciones
        current_settings = customer.settings or {}
        updated_settings = {**current_settings, **data}
        
        customer.settings = updated_settings
        customer.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Configuraciones actualizadas exitosamente',
            'settings': updated_settings
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error interno del servidor'}), 500

@customers_bp.route('/users', methods=['GET'])
@jwt_required()
def get_customer_users():
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        # Solo administradores y managers pueden ver todos los usuarios
        if user.role not in ['admin', 'manager']:
            return jsonify({'error': 'Permisos insuficientes'}), 403
        
        users = User.query.filter_by(
            customer_id=user.customer_id,
            is_active=True
        ).all()
        
        result = []
        for u in users:
            result.append({
                'id': u.id,
                'email': u.email,
                'first_name': u.first_name,
                'last_name': u.last_name,
                'role': u.role,
                'is_active': u.is_active,
                'created_at': u.created_at.isoformat()
            })
        
        return jsonify({
            'users': result
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Error interno del servidor'}), 500

@customers_bp.route('/users', methods=['POST'])
@jwt_required()
def create_user():
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        # Solo administradores pueden crear usuarios
        if user.role != 'admin':
            return jsonify({'error': 'Permisos insuficientes'}), 403
        
        data = request.get_json()
        
        # Validar datos requeridos
        required_fields = ['email', 'password', 'first_name', 'last_name', 'role']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} es requerido'}), 400
        
        # Verificar que el email no existe
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'El email ya está registrado'}), 409
        
        # Validar rol
        if data['role'] not in ['admin', 'manager', 'agent']:
            return jsonify({'error': 'Rol inválido'}), 400
        
        from werkzeug.security import generate_password_hash
        
        new_user = User(
            email=data['email'],
            password_hash=generate_password_hash(data['password']),
            first_name=data['first_name'],
            last_name=data['last_name'],
            role=data['role'],
            customer_id=user.customer_id
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({
            'message': 'Usuario creado exitosamente',
            'user': {
                'id': new_user.id,
                'email': new_user.email,
                'first_name': new_user.first_name,
                'last_name': new_user.last_name,
                'role': new_user.role
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error interno del servidor'}), 500

@customers_bp.route('/users/<user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        # Solo administradores pueden actualizar usuarios
        if current_user.role != 'admin':
            return jsonify({'error': 'Permisos insuficientes'}), 403
        
        data = request.get_json()
        
        target_user = User.query.filter_by(
            id=user_id,
            customer_id=current_user.customer_id
        ).first()
        
        if not target_user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        # Actualizar campos
        if 'first_name' in data:
            target_user.first_name = data['first_name']
        if 'last_name' in data:
            target_user.last_name = data['last_name']
        if 'role' in data and data['role'] in ['admin', 'manager', 'agent']:
            target_user.role = data['role']
        if 'is_active' in data:
            target_user.is_active = data['is_active']
        
        target_user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Usuario actualizado exitosamente',
            'user': {
                'id': target_user.id,
                'email': target_user.email,
                'first_name': target_user.first_name,
                'last_name': target_user.last_name,
                'role': target_user.role,
                'is_active': target_user.is_active
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error interno del servidor'}), 500

