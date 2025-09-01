from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.database import db, User, Conversation, Contact, Channel, Message
from datetime import datetime
from sqlalchemy import desc, and_

conversations_bp = Blueprint('conversations', __name__)

def get_current_user():
    user_id = get_jwt_identity()
    return User.query.get(user_id)

@conversations_bp.route('/', methods=['GET'])
@jwt_required()
def get_conversations():
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        # Parámetros de consulta
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        status = request.args.get('status')
        channel_type = request.args.get('channel')
        assigned_to = request.args.get('assigned_to')
        search = request.args.get('search')
        
        # Construir consulta base
        query = Conversation.query.filter_by(customer_id=user.customer_id)
        
        # Aplicar filtros
        if status:
            query = query.filter(Conversation.status == status)
        
        if channel_type:
            query = query.join(Channel).filter(Channel.type == channel_type)
        
        if assigned_to:
            if assigned_to == 'me':
                query = query.filter(Conversation.assigned_to == user.id)
            elif assigned_to == 'unassigned':
                query = query.filter(Conversation.assigned_to.is_(None))
            else:
                query = query.filter(Conversation.assigned_to == assigned_to)
        
        if search:
            query = query.join(Contact).filter(
                Contact.name.ilike(f'%{search}%')
            )
        
        # Ordenar por última actividad
        query = query.order_by(desc(Conversation.last_message_at))
        
        # Paginación
        conversations = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        # Formatear respuesta
        result = []
        for conv in conversations.items:
            # Obtener último mensaje
            last_message = Message.query.filter_by(
                conversation_id=conv.id
            ).order_by(desc(Message.created_at)).first()
            
            # Contar mensajes no leídos
            unread_count = Message.query.filter(
                and_(
                    Message.conversation_id == conv.id,
                    Message.direction == 'inbound',
                    Message.status != 'read'
                )
            ).count()
            
            result.append({
                'id': conv.id,
                'contact': {
                    'id': conv.contact.id,
                    'name': conv.contact.name,
                    'phone': conv.contact.phone,
                    'email': conv.contact.email
                },
                'channel': {
                    'id': conv.channel.id,
                    'type': conv.channel.type,
                    'name': conv.channel.name
                },
                'assigned_agent': {
                    'id': conv.assigned_agent.id,
                    'name': f"{conv.assigned_agent.first_name} {conv.assigned_agent.last_name}"
                } if conv.assigned_agent else None,
                'status': conv.status,
                'priority': conv.priority,
                'subject': conv.subject,
                'tags': conv.tags or [],
                'unread_count': unread_count,
                'last_message': {
                    'id': last_message.id,
                    'content': last_message.content,
                    'type': last_message.type,
                    'direction': last_message.direction,
                    'created_at': last_message.created_at.isoformat()
                } if last_message else None,
                'last_message_at': conv.last_message_at.isoformat() if conv.last_message_at else None,
                'created_at': conv.created_at.isoformat(),
                'updated_at': conv.updated_at.isoformat()
            })
        
        return jsonify({
            'conversations': result,
            'pagination': {
                'page': conversations.page,
                'pages': conversations.pages,
                'per_page': conversations.per_page,
                'total': conversations.total,
                'has_next': conversations.has_next,
                'has_prev': conversations.has_prev
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Error interno del servidor'}), 500

@conversations_bp.route('/<conversation_id>', methods=['GET'])
@jwt_required()
def get_conversation(conversation_id):
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        conversation = Conversation.query.filter_by(
            id=conversation_id,
            customer_id=user.customer_id
        ).first()
        
        if not conversation:
            return jsonify({'error': 'Conversación no encontrada'}), 404
        
        # Obtener mensajes de la conversación
        messages = Message.query.filter_by(
            conversation_id=conversation_id
        ).order_by(Message.created_at).all()
        
        # Formatear mensajes
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                'id': msg.id,
                'type': msg.type,
                'content': msg.content,
                'direction': msg.direction,
                'sender_type': msg.sender_type,
                'sender_id': msg.sender_id,
                'status': msg.status,
                'created_at': msg.created_at.isoformat(),
                'updated_at': msg.updated_at.isoformat()
            })
        
        return jsonify({
            'conversation': {
                'id': conversation.id,
                'contact': {
                    'id': conversation.contact.id,
                    'name': conversation.contact.name,
                    'phone': conversation.contact.phone,
                    'email': conversation.contact.email,
                    'whatsapp_id': conversation.contact.whatsapp_id,
                    'instagram_id': conversation.contact.instagram_id,
                    'messenger_id': conversation.contact.messenger_id,
                    'tags': conversation.contact.tags or [],
                    'custom_fields': conversation.contact.custom_fields or {}
                },
                'channel': {
                    'id': conversation.channel.id,
                    'type': conversation.channel.type,
                    'name': conversation.channel.name
                },
                'assigned_agent': {
                    'id': conversation.assigned_agent.id,
                    'name': f"{conversation.assigned_agent.first_name} {conversation.assigned_agent.last_name}",
                    'email': conversation.assigned_agent.email
                } if conversation.assigned_agent else None,
                'status': conversation.status,
                'priority': conversation.priority,
                'subject': conversation.subject,
                'tags': conversation.tags or [],
                'metadata': conversation.metadata or {},
                'created_at': conversation.created_at.isoformat(),
                'updated_at': conversation.updated_at.isoformat()
            },
            'messages': formatted_messages
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Error interno del servidor'}), 500

@conversations_bp.route('/<conversation_id>/assign', methods=['POST'])
@jwt_required()
def assign_conversation(conversation_id):
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        data = request.get_json()
        agent_id = data.get('agent_id')
        
        conversation = Conversation.query.filter_by(
            id=conversation_id,
            customer_id=user.customer_id
        ).first()
        
        if not conversation:
            return jsonify({'error': 'Conversación no encontrada'}), 404
        
        # Verificar que el agente pertenece al mismo cliente
        if agent_id:
            agent = User.query.filter_by(
                id=agent_id,
                customer_id=user.customer_id,
                is_active=True
            ).first()
            
            if not agent:
                return jsonify({'error': 'Agente no encontrado'}), 404
        
        conversation.assigned_to = agent_id
        conversation.status = 'assigned' if agent_id else 'open'
        conversation.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Conversación asignada exitosamente',
            'conversation': {
                'id': conversation.id,
                'assigned_to': agent_id,
                'status': conversation.status
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error interno del servidor'}), 500

@conversations_bp.route('/<conversation_id>/status', methods=['PUT'])
@jwt_required()
def update_conversation_status(conversation_id):
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        data = request.get_json()
        status = data.get('status')
        
        if status not in ['open', 'assigned', 'closed', 'archived']:
            return jsonify({'error': 'Estado inválido'}), 400
        
        conversation = Conversation.query.filter_by(
            id=conversation_id,
            customer_id=user.customer_id
        ).first()
        
        if not conversation:
            return jsonify({'error': 'Conversación no encontrada'}), 404
        
        conversation.status = status
        conversation.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Estado actualizado exitosamente',
            'conversation': {
                'id': conversation.id,
                'status': conversation.status
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error interno del servidor'}), 500

@conversations_bp.route('/<conversation_id>/tags', methods=['PUT'])
@jwt_required()
def update_conversation_tags(conversation_id):
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        data = request.get_json()
        tags = data.get('tags', [])
        
        conversation = Conversation.query.filter_by(
            id=conversation_id,
            customer_id=user.customer_id
        ).first()
        
        if not conversation:
            return jsonify({'error': 'Conversación no encontrada'}), 404
        
        conversation.tags = tags
        conversation.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Tags actualizados exitosamente',
            'conversation': {
                'id': conversation.id,
                'tags': conversation.tags
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error interno del servidor'}), 500

@conversations_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_conversation_stats():
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        # Estadísticas básicas
        total = Conversation.query.filter_by(customer_id=user.customer_id).count()
        open_count = Conversation.query.filter_by(customer_id=user.customer_id, status='open').count()
        assigned = Conversation.query.filter_by(customer_id=user.customer_id, status='assigned').count()
        closed = Conversation.query.filter_by(customer_id=user.customer_id, status='closed').count()
        
        # Conversaciones asignadas al usuario actual
        my_conversations = Conversation.query.filter_by(
            customer_id=user.customer_id,
            assigned_to=user.id
        ).count()
        
        return jsonify({
            'stats': {
                'total': total,
                'open': open_count,
                'assigned': assigned,
                'closed': closed,
                'my_conversations': my_conversations
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Error interno del servidor'}), 500

