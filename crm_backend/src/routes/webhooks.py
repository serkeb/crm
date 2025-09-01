from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.database import db, User, Webhook
from datetime import datetime

webhooks_bp = Blueprint('webhooks', __name__)

def get_current_user():
    user_id = get_jwt_identity()
    return User.query.get(user_id)

@webhooks_bp.route('/', methods=['GET'])
@jwt_required()
def get_webhooks():
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        webhooks = Webhook.query.filter_by(customer_id=user.customer_id).all()
        
        result = []
        for webhook in webhooks:
            result.append({
                'id': webhook.id,
                'url': webhook.url,
                'events': webhook.events or [],
                'is_active': webhook.is_active,
                'last_delivery': webhook.last_delivery.isoformat() if webhook.last_delivery else None,
                'failure_count': webhook.failure_count,
                'created_at': webhook.created_at.isoformat(),
                'updated_at': webhook.updated_at.isoformat()
            })
        
        return jsonify({
            'webhooks': result
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Error interno del servidor'}), 500

@webhooks_bp.route('/<webhook_id>', methods=['GET'])
@jwt_required()
def get_webhook(webhook_id):
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        webhook = Webhook.query.filter_by(
            id=webhook_id,
            customer_id=user.customer_id
        ).first()
        
        if not webhook:
            return jsonify({'error': 'Webhook no encontrado'}), 404
        
        return jsonify({
            'webhook': {
                'id': webhook.id,
                'url': webhook.url,
                'events': webhook.events or [],
                'is_active': webhook.is_active,
                'last_delivery': webhook.last_delivery.isoformat() if webhook.last_delivery else None,
                'failure_count': webhook.failure_count,
                'created_at': webhook.created_at.isoformat(),
                'updated_at': webhook.updated_at.isoformat()
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Error interno del servidor'}), 500

@webhooks_bp.route('/', methods=['POST'])
@jwt_required()
def create_webhook():
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        # Solo administradores pueden crear webhooks
        if user.role not in ['admin', 'manager']:
            return jsonify({'error': 'Permisos insuficientes'}), 403
        
        data = request.get_json()
        
        # Validar datos requeridos
        if not data.get('url') or not data.get('events'):
            return jsonify({'error': 'url y events son requeridos'}), 400
        
        # Validar URL
        import re
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        if not url_pattern.match(data['url']):
            return jsonify({'error': 'URL inválida'}), 400
        
        # Validar eventos
        valid_events = [
            'message.received',
            'message.sent',
            'conversation.created',
            'conversation.assigned',
            'conversation.closed',
            'ticket.created',
            'ticket.updated',
            'ticket.closed',
            'contact.created',
            'contact.updated'
        ]
        
        events = data['events']
        if not isinstance(events, list) or not all(event in valid_events for event in events):
            return jsonify({'error': 'Eventos inválidos'}), 400
        
        # Generar secret para validación
        import secrets
        webhook_secret = secrets.token_urlsafe(32)
        
        webhook = Webhook(
            customer_id=user.customer_id,
            url=data['url'],
            events=events,
            secret=webhook_secret,
            is_active=data.get('is_active', True)
        )
        
        db.session.add(webhook)
        db.session.commit()
        
        return jsonify({
            'message': 'Webhook creado exitosamente',
            'webhook': {
                'id': webhook.id,
                'url': webhook.url,
                'events': webhook.events,
                'secret': webhook_secret,
                'is_active': webhook.is_active
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error interno del servidor'}), 500

@webhooks_bp.route('/<webhook_id>', methods=['PUT'])
@jwt_required()
def update_webhook(webhook_id):
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        # Solo administradores pueden actualizar webhooks
        if user.role not in ['admin', 'manager']:
            return jsonify({'error': 'Permisos insuficientes'}), 403
        
        data = request.get_json()
        
        webhook = Webhook.query.filter_by(
            id=webhook_id,
            customer_id=user.customer_id
        ).first()
        
        if not webhook:
            return jsonify({'error': 'Webhook no encontrado'}), 404
        
        # Actualizar campos
        if 'url' in data:
            # Validar URL
            import re
            url_pattern = re.compile(
                r'^https?://'
                r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
                r'localhost|'
                r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
                r'(?::\d+)?'
                r'(?:/?|[/?]\S+)$', re.IGNORECASE)
            
            if not url_pattern.match(data['url']):
                return jsonify({'error': 'URL inválida'}), 400
            
            webhook.url = data['url']
        
        if 'events' in data:
            valid_events = [
                'message.received',
                'message.sent',
                'conversation.created',
                'conversation.assigned',
                'conversation.closed',
                'ticket.created',
                'ticket.updated',
                'ticket.closed',
                'contact.created',
                'contact.updated'
            ]
            
            events = data['events']
            if not isinstance(events, list) or not all(event in valid_events for event in events):
                return jsonify({'error': 'Eventos inválidos'}), 400
            
            webhook.events = events
        
        if 'is_active' in data:
            webhook.is_active = data['is_active']
            # Resetear contador de fallos si se reactiva
            if data['is_active']:
                webhook.failure_count = 0
        
        webhook.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Webhook actualizado exitosamente',
            'webhook': {
                'id': webhook.id,
                'url': webhook.url,
                'events': webhook.events,
                'is_active': webhook.is_active
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error interno del servidor'}), 500

@webhooks_bp.route('/<webhook_id>/test', methods=['POST'])
@jwt_required()
def test_webhook(webhook_id):
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        webhook = Webhook.query.filter_by(
            id=webhook_id,
            customer_id=user.customer_id
        ).first()
        
        if not webhook:
            return jsonify({'error': 'Webhook no encontrado'}), 404
        
        # Crear payload de prueba
        test_payload = {
            'event': 'webhook.test',
            'data': {
                'message': 'Este es un webhook de prueba',
                'timestamp': datetime.utcnow().isoformat(),
                'customer_id': user.customer_id
            },
            'webhook_id': webhook.id
        }
        
        # Generar firma
        import hmac
        import hashlib
        import json
        
        payload_string = json.dumps(test_payload, sort_keys=True)
        signature = hmac.new(
            webhook.secret.encode('utf-8'),
            payload_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Enviar webhook de prueba
        import requests
        
        try:
            response = requests.post(
                webhook.url,
                json=test_payload,
                headers={
                    'Content-Type': 'application/json',
                    'X-Webhook-Signature': f'sha256={signature}',
                    'X-Webhook-Event': 'webhook.test',
                    'User-Agent': 'CRM-Multicanal-Webhook/1.0'
                },
                timeout=30
            )
            
            test_result = {
                'success': response.status_code < 400,
                'status_code': response.status_code,
                'response_time': response.elapsed.total_seconds(),
                'message': 'Webhook de prueba enviado exitosamente' if response.status_code < 400 else f'Error HTTP {response.status_code}'
            }
            
            # Actualizar última entrega si fue exitoso
            if response.status_code < 400:
                webhook.last_delivery = datetime.utcnow()
                db.session.commit()
            
        except requests.exceptions.RequestException as e:
            test_result = {
                'success': False,
                'message': f'Error de conexión: {str(e)}'
            }
        
        return jsonify({
            'test_result': test_result
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Error interno del servidor'}), 500

@webhooks_bp.route('/<webhook_id>', methods=['DELETE'])
@jwt_required()
def delete_webhook(webhook_id):
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        # Solo administradores pueden eliminar webhooks
        if user.role != 'admin':
            return jsonify({'error': 'Permisos insuficientes'}), 403
        
        webhook = Webhook.query.filter_by(
            id=webhook_id,
            customer_id=user.customer_id
        ).first()
        
        if not webhook:
            return jsonify({'error': 'Webhook no encontrado'}), 404
        
        db.session.delete(webhook)
        db.session.commit()
        
        return jsonify({
            'message': 'Webhook eliminado exitosamente'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error interno del servidor'}), 500

@webhooks_bp.route('/events', methods=['GET'])
@jwt_required()
def get_available_events():
    try:
        events = [
            {
                'event': 'message.received',
                'description': 'Se recibe un nuevo mensaje de un contacto',
                'payload_example': {
                    'message_id': 'msg_123',
                    'conversation_id': 'conv_456',
                    'contact_id': 'contact_789',
                    'content': 'Hola, necesito ayuda',
                    'channel': 'whatsapp'
                }
            },
            {
                'event': 'message.sent',
                'description': 'Se envía un mensaje a un contacto',
                'payload_example': {
                    'message_id': 'msg_124',
                    'conversation_id': 'conv_456',
                    'agent_id': 'user_123',
                    'content': 'Hola, ¿en qué puedo ayudarte?',
                    'channel': 'whatsapp'
                }
            },
            {
                'event': 'conversation.created',
                'description': 'Se crea una nueva conversación',
                'payload_example': {
                    'conversation_id': 'conv_456',
                    'contact_id': 'contact_789',
                    'channel': 'whatsapp',
                    'status': 'open'
                }
            },
            {
                'event': 'conversation.assigned',
                'description': 'Se asigna una conversación a un agente',
                'payload_example': {
                    'conversation_id': 'conv_456',
                    'agent_id': 'user_123',
                    'assigned_by': 'user_456'
                }
            },
            {
                'event': 'ticket.created',
                'description': 'Se crea un nuevo ticket',
                'payload_example': {
                    'ticket_id': 'ticket_789',
                    'title': 'Problema con el producto',
                    'priority': 'high',
                    'contact_id': 'contact_789'
                }
            }
        ]
        
        return jsonify({
            'events': events
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Error interno del servidor'}), 500

