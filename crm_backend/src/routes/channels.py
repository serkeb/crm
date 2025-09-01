from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.database import db, User, Channel
from datetime import datetime

channels_bp = Blueprint('channels', __name__)

def get_current_user():
    user_id = get_jwt_identity()
    return User.query.get(user_id)

@channels_bp.route('/', methods=['GET'])
@jwt_required()
def get_channels():
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        channels = Channel.query.filter_by(customer_id=user.customer_id).all()
        
        result = []
        for channel in channels:
            result.append({
                'id': channel.id,
                'type': channel.type,
                'name': channel.name,
                'is_active': channel.is_active,
                'is_connected': channel.is_connected,
                'last_sync': channel.last_sync.isoformat() if channel.last_sync else None,
                'created_at': channel.created_at.isoformat(),
                'updated_at': channel.updated_at.isoformat()
            })
        
        return jsonify({
            'channels': result
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Error interno del servidor'}), 500

@channels_bp.route('/<channel_id>', methods=['GET'])
@jwt_required()
def get_channel(channel_id):
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        channel = Channel.query.filter_by(
            id=channel_id,
            customer_id=user.customer_id
        ).first()
        
        if not channel:
            return jsonify({'error': 'Canal no encontrado'}), 404
        
        # No incluir credenciales sensibles en la respuesta
        config = channel.config or {}
        safe_config = {k: v for k, v in config.items() if 'secret' not in k.lower() and 'token' not in k.lower()}
        
        return jsonify({
            'channel': {
                'id': channel.id,
                'type': channel.type,
                'name': channel.name,
                'config': safe_config,
                'is_active': channel.is_active,
                'is_connected': channel.is_connected,
                'last_sync': channel.last_sync.isoformat() if channel.last_sync else None,
                'created_at': channel.created_at.isoformat(),
                'updated_at': channel.updated_at.isoformat()
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Error interno del servidor'}), 500

@channels_bp.route('/', methods=['POST'])
@jwt_required()
def create_channel():
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        # Solo administradores pueden crear canales
        if user.role not in ['admin', 'manager']:
            return jsonify({'error': 'Permisos insuficientes'}), 403
        
        data = request.get_json()
        
        # Validar datos requeridos
        if not data.get('type') or not data.get('name'):
            return jsonify({'error': 'type y name son requeridos'}), 400
        
        # Validar tipo de canal
        valid_types = ['whatsapp', 'instagram', 'messenger', 'sms', 'email', 'telegram']
        if data['type'] not in valid_types:
            return jsonify({'error': 'Tipo de canal inválido'}), 400
        
        # Verificar si ya existe un canal del mismo tipo
        existing_channel = Channel.query.filter_by(
            customer_id=user.customer_id,
            type=data['type']
        ).first()
        
        if existing_channel:
            return jsonify({'error': f'Ya existe un canal de tipo {data["type"]}'}), 409
        
        channel = Channel(
            customer_id=user.customer_id,
            type=data['type'],
            name=data['name'],
            config=data.get('config', {}),
            credentials=data.get('credentials', {}),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(channel)
        db.session.commit()
        
        return jsonify({
            'message': 'Canal creado exitosamente',
            'channel': {
                'id': channel.id,
                'type': channel.type,
                'name': channel.name,
                'is_active': channel.is_active
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error interno del servidor'}), 500

@channels_bp.route('/<channel_id>', methods=['PUT'])
@jwt_required()
def update_channel(channel_id):
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        # Solo administradores pueden actualizar canales
        if user.role not in ['admin', 'manager']:
            return jsonify({'error': 'Permisos insuficientes'}), 403
        
        data = request.get_json()
        
        channel = Channel.query.filter_by(
            id=channel_id,
            customer_id=user.customer_id
        ).first()
        
        if not channel:
            return jsonify({'error': 'Canal no encontrado'}), 404
        
        # Actualizar campos
        if 'name' in data:
            channel.name = data['name']
        if 'config' in data:
            channel.config = data['config']
        if 'credentials' in data:
            channel.credentials = data['credentials']
        if 'is_active' in data:
            channel.is_active = data['is_active']
        
        channel.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Canal actualizado exitosamente',
            'channel': {
                'id': channel.id,
                'type': channel.type,
                'name': channel.name,
                'is_active': channel.is_active
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error interno del servidor'}), 500

@channels_bp.route('/<channel_id>/test', methods=['POST'])
@jwt_required()
def test_channel_connection(channel_id):
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        channel = Channel.query.filter_by(
            id=channel_id,
            customer_id=user.customer_id
        ).first()
        
        if not channel:
            return jsonify({'error': 'Canal no encontrado'}), 404
        
        # Aquí se implementaría la lógica específica para probar cada tipo de canal
        # Por ahora simulamos la prueba
        
        test_result = {
            'success': True,
            'message': f'Conexión con {channel.type} exitosa',
            'details': {
                'channel_type': channel.type,
                'test_timestamp': datetime.utcnow().isoformat()
            }
        }
        
        if test_result['success']:
            channel.is_connected = True
            channel.last_sync = datetime.utcnow()
            db.session.commit()
        
        return jsonify({
            'test_result': test_result
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Error interno del servidor'}), 500

@channels_bp.route('/<channel_id>/sync', methods=['POST'])
@jwt_required()
def sync_channel(channel_id):
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        channel = Channel.query.filter_by(
            id=channel_id,
            customer_id=user.customer_id
        ).first()
        
        if not channel:
            return jsonify({'error': 'Canal no encontrado'}), 404
        
        if not channel.is_active:
            return jsonify({'error': 'Canal inactivo'}), 400
        
        # Aquí se implementaría la lógica de sincronización específica para cada canal
        # Por ahora simulamos la sincronización
        
        sync_result = {
            'success': True,
            'message': f'Sincronización de {channel.type} completada',
            'synced_items': {
                'messages': 0,
                'contacts': 0
            },
            'sync_timestamp': datetime.utcnow().isoformat()
        }
        
        channel.last_sync = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'sync_result': sync_result
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error interno del servidor'}), 500

@channels_bp.route('/<channel_id>', methods=['DELETE'])
@jwt_required()
def delete_channel(channel_id):
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        # Solo administradores pueden eliminar canales
        if user.role != 'admin':
            return jsonify({'error': 'Permisos insuficientes'}), 403
        
        channel = Channel.query.filter_by(
            id=channel_id,
            customer_id=user.customer_id
        ).first()
        
        if not channel:
            return jsonify({'error': 'Canal no encontrado'}), 404
        
        # Verificar si hay conversaciones asociadas
        from src.models.database import Conversation
        conversations_count = Conversation.query.filter_by(channel_id=channel_id).count()
        
        if conversations_count > 0:
            return jsonify({
                'error': 'No se puede eliminar el canal porque tiene conversaciones asociadas'
            }), 400
        
        db.session.delete(channel)
        db.session.commit()
        
        return jsonify({
            'message': 'Canal eliminado exitosamente'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error interno del servidor'}), 500

@channels_bp.route('/types', methods=['GET'])
@jwt_required()
def get_channel_types():
    try:
        channel_types = [
            {
                'type': 'whatsapp',
                'name': 'WhatsApp Business',
                'description': 'Integración con WhatsApp Business API',
                'features': ['Mensajes de texto', 'Imágenes', 'Documentos', 'Plantillas'],
                'required_fields': ['access_token', 'phone_number_id', 'business_account_id']
            },
            {
                'type': 'instagram',
                'name': 'Instagram Messaging',
                'description': 'Mensajes directos de Instagram',
                'features': ['Mensajes de texto', 'Imágenes', 'Quick replies'],
                'required_fields': ['access_token', 'instagram_account_id']
            },
            {
                'type': 'messenger',
                'name': 'Facebook Messenger',
                'description': 'Mensajes de Facebook Messenger',
                'features': ['Mensajes de texto', 'Imágenes', 'Botones', 'Plantillas'],
                'required_fields': ['access_token', 'page_id']
            },
            {
                'type': 'sms',
                'name': 'SMS',
                'description': 'Mensajes de texto SMS',
                'features': ['Mensajes de texto'],
                'required_fields': ['api_key', 'sender_id']
            },
            {
                'type': 'email',
                'name': 'Email',
                'description': 'Correo electrónico',
                'features': ['Mensajes HTML', 'Archivos adjuntos'],
                'required_fields': ['smtp_host', 'smtp_port', 'username', 'password']
            },
            {
                'type': 'telegram',
                'name': 'Telegram',
                'description': 'Mensajes de Telegram',
                'features': ['Mensajes de texto', 'Imágenes', 'Documentos'],
                'required_fields': ['bot_token']
            }
        ]
        
        return jsonify({
            'channel_types': channel_types
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Error interno del servidor'}), 500

