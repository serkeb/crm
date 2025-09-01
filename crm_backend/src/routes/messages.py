from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.database import db, User, Message, Conversation, Contact, Channel
from datetime import datetime

messages_bp = Blueprint('messages', __name__)

def get_current_user():
    user_id = get_jwt_identity()
    return User.query.get(user_id)

@messages_bp.route('/', methods=['POST'])
@jwt_required()
def send_message():
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        data = request.get_json()
        conversation_id = data.get('conversation_id')
        content = data.get('content')
        message_type = data.get('type', 'text')
        
        if not conversation_id or not content:
            return jsonify({'error': 'conversation_id y content son requeridos'}), 400
        
        # Verificar que la conversación existe y pertenece al cliente
        conversation = Conversation.query.filter_by(
            id=conversation_id,
            customer_id=user.customer_id
        ).first()
        
        if not conversation:
            return jsonify({'error': 'Conversación no encontrada'}), 404
        
        # Crear el mensaje
        message = Message(
            conversation_id=conversation_id,
            direction='outbound',
            type=message_type,
            content=content,
            sender_type='agent',
            sender_id=user.id,
            status='sent'
        )
        
        db.session.add(message)
        
        # Actualizar última actividad de la conversación
        conversation.last_message_at = datetime.utcnow()
        conversation.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Aquí se integraría con las APIs externas para enviar el mensaje real
        # Por ahora solo simulamos el envío
        
        return jsonify({
            'message': {
                'id': message.id,
                'conversation_id': message.conversation_id,
                'type': message.type,
                'content': message.content,
                'direction': message.direction,
                'sender_type': message.sender_type,
                'sender_id': message.sender_id,
                'status': message.status,
                'created_at': message.created_at.isoformat()
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error interno del servidor'}), 500

@messages_bp.route('/<message_id>/status', methods=['PUT'])
@jwt_required()
def update_message_status(message_id):
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        data = request.get_json()
        status = data.get('status')
        
        if status not in ['sent', 'delivered', 'read', 'failed']:
            return jsonify({'error': 'Estado inválido'}), 400
        
        # Verificar que el mensaje pertenece al cliente
        message = Message.query.join(Conversation).filter(
            Message.id == message_id,
            Conversation.customer_id == user.customer_id
        ).first()
        
        if not message:
            return jsonify({'error': 'Mensaje no encontrado'}), 404
        
        message.status = status
        message.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Estado actualizado exitosamente',
            'message_id': message_id,
            'status': status
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error interno del servidor'}), 500

@messages_bp.route('/webhook', methods=['POST'])
def receive_webhook():
    """Endpoint para recibir webhooks de las plataformas externas"""
    try:
        data = request.get_json()
        headers = dict(request.headers)
        
        # Aquí se procesarían los webhooks de WhatsApp, Instagram, etc.
        # Por ahora solo registramos que se recibió
        
        # Determinar el tipo de webhook basado en headers o contenido
        webhook_type = headers.get('X-Webhook-Type', 'unknown')
        
        # Procesar según el tipo
        if webhook_type == 'whatsapp':
            return process_whatsapp_webhook(data)
        elif webhook_type == 'instagram':
            return process_instagram_webhook(data)
        elif webhook_type == 'messenger':
            return process_messenger_webhook(data)
        else:
            # Webhook genérico
            return jsonify({'status': 'received'}), 200
        
    except Exception as e:
        return jsonify({'error': 'Error procesando webhook'}), 500

def process_whatsapp_webhook(data):
    """Procesar webhook de WhatsApp"""
    try:
        # Implementar lógica específica de WhatsApp
        # Por ahora solo confirmamos recepción
        return jsonify({'status': 'processed', 'type': 'whatsapp'}), 200
    except Exception as e:
        return jsonify({'error': 'Error procesando webhook de WhatsApp'}), 500

def process_instagram_webhook(data):
    """Procesar webhook de Instagram"""
    try:
        # Implementar lógica específica de Instagram
        return jsonify({'status': 'processed', 'type': 'instagram'}), 200
    except Exception as e:
        return jsonify({'error': 'Error procesando webhook de Instagram'}), 500

def process_messenger_webhook(data):
    """Procesar webhook de Messenger"""
    try:
        # Implementar lógica específica de Messenger
        return jsonify({'status': 'processed', 'type': 'messenger'}), 200
    except Exception as e:
        return jsonify({'error': 'Error procesando webhook de Messenger'}), 500

@messages_bp.route('/search', methods=['GET'])
@jwt_required()
def search_messages():
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        query_text = request.args.get('q', '')
        conversation_id = request.args.get('conversation_id')
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        if not query_text:
            return jsonify({'error': 'Parámetro de búsqueda requerido'}), 400
        
        # Construir consulta
        query = Message.query.join(Conversation).filter(
            Conversation.customer_id == user.customer_id
        )
        
        if conversation_id:
            query = query.filter(Message.conversation_id == conversation_id)
        
        # Buscar en contenido de texto
        query = query.filter(
            Message.content.contains(query_text)
        )
        
        # Ordenar por fecha
        query = query.order_by(Message.created_at.desc())
        
        # Paginación
        messages = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        # Formatear resultados
        result = []
        for msg in messages.items:
            result.append({
                'id': msg.id,
                'conversation_id': msg.conversation_id,
                'type': msg.type,
                'content': msg.content,
                'direction': msg.direction,
                'sender_type': msg.sender_type,
                'status': msg.status,
                'created_at': msg.created_at.isoformat(),
                'conversation': {
                    'id': msg.conversation.id,
                    'contact_name': msg.conversation.contact.name,
                    'channel_type': msg.conversation.channel.type
                }
            })
        
        return jsonify({
            'messages': result,
            'pagination': {
                'page': messages.page,
                'pages': messages.pages,
                'per_page': messages.per_page,
                'total': messages.total,
                'has_next': messages.has_next,
                'has_prev': messages.has_prev
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Error interno del servidor'}), 500

