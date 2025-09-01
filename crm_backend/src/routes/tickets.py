from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.database import db, User, Ticket, Contact, Conversation
from datetime import datetime
from sqlalchemy import desc, and_

tickets_bp = Blueprint('tickets', __name__)

def get_current_user():
    user_id = get_jwt_identity()
    return User.query.get(user_id)

@tickets_bp.route('/', methods=['GET'])
@jwt_required()
def get_tickets():
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        # Parámetros de consulta
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        status = request.args.get('status')
        priority = request.args.get('priority')
        assigned_to = request.args.get('assigned_to')
        category = request.args.get('category')
        search = request.args.get('search')
        
        # Construir consulta base
        query = Ticket.query.filter_by(customer_id=user.customer_id)
        
        # Aplicar filtros
        if status:
            query = query.filter(Ticket.status == status)
        
        if priority:
            query = query.filter(Ticket.priority == priority)
        
        if category:
            query = query.filter(Ticket.category == category)
        
        if assigned_to:
            if assigned_to == 'me':
                query = query.filter(Ticket.assigned_to == user.id)
            elif assigned_to == 'unassigned':
                query = query.filter(Ticket.assigned_to.is_(None))
            else:
                query = query.filter(Ticket.assigned_to == assigned_to)
        
        if search:
            query = query.filter(
                Ticket.title.ilike(f'%{search}%')
            )
        
        # Ordenar por fecha de creación
        query = query.order_by(desc(Ticket.created_at))
        
        # Paginación
        tickets = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        # Formatear respuesta
        result = []
        for ticket in tickets.items:
            result.append({
                'id': ticket.id,
                'title': ticket.title,
                'description': ticket.description,
                'status': ticket.status,
                'priority': ticket.priority,
                'category': ticket.category,
                'tags': ticket.tags or [],
                'contact': {
                    'id': ticket.contact.id,
                    'name': ticket.contact.name,
                    'email': ticket.contact.email,
                    'phone': ticket.contact.phone
                } if ticket.contact else None,
                'conversation': {
                    'id': ticket.conversation.id,
                    'channel_type': ticket.conversation.channel.type
                } if ticket.conversation else None,
                'assigned_agent': {
                    'id': ticket.assigned_agent.id,
                    'name': f"{ticket.assigned_agent.first_name} {ticket.assigned_agent.last_name}"
                } if ticket.assigned_agent else None,
                'resolution': ticket.resolution,
                'resolved_at': ticket.resolved_at.isoformat() if ticket.resolved_at else None,
                'created_at': ticket.created_at.isoformat(),
                'updated_at': ticket.updated_at.isoformat()
            })
        
        return jsonify({
            'tickets': result,
            'pagination': {
                'page': tickets.page,
                'pages': tickets.pages,
                'per_page': tickets.per_page,
                'total': tickets.total,
                'has_next': tickets.has_next,
                'has_prev': tickets.has_prev
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Error interno del servidor'}), 500

@tickets_bp.route('/<ticket_id>', methods=['GET'])
@jwt_required()
def get_ticket(ticket_id):
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        ticket = Ticket.query.filter_by(
            id=ticket_id,
            customer_id=user.customer_id
        ).first()
        
        if not ticket:
            return jsonify({'error': 'Ticket no encontrado'}), 404
        
        return jsonify({
            'ticket': {
                'id': ticket.id,
                'title': ticket.title,
                'description': ticket.description,
                'status': ticket.status,
                'priority': ticket.priority,
                'category': ticket.category,
                'tags': ticket.tags or [],
                'contact': {
                    'id': ticket.contact.id,
                    'name': ticket.contact.name,
                    'email': ticket.contact.email,
                    'phone': ticket.contact.phone,
                    'whatsapp_id': ticket.contact.whatsapp_id,
                    'instagram_id': ticket.contact.instagram_id,
                    'messenger_id': ticket.contact.messenger_id
                } if ticket.contact else None,
                'conversation': {
                    'id': ticket.conversation.id,
                    'channel_type': ticket.conversation.channel.type,
                    'channel_name': ticket.conversation.channel.name
                } if ticket.conversation else None,
                'assigned_agent': {
                    'id': ticket.assigned_agent.id,
                    'name': f"{ticket.assigned_agent.first_name} {ticket.assigned_agent.last_name}",
                    'email': ticket.assigned_agent.email
                } if ticket.assigned_agent else None,
                'resolution': ticket.resolution,
                'resolved_at': ticket.resolved_at.isoformat() if ticket.resolved_at else None,
                'created_at': ticket.created_at.isoformat(),
                'updated_at': ticket.updated_at.isoformat()
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Error interno del servidor'}), 500

@tickets_bp.route('/', methods=['POST'])
@jwt_required()
def create_ticket():
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        data = request.get_json()
        
        # Validar datos requeridos
        if not data.get('title'):
            return jsonify({'error': 'title es requerido'}), 400
        
        # Validar prioridad
        valid_priorities = ['low', 'normal', 'high', 'urgent']
        priority = data.get('priority', 'normal')
        if priority not in valid_priorities:
            return jsonify({'error': 'Prioridad inválida'}), 400
        
        # Verificar contacto si se proporciona
        contact_id = data.get('contact_id')
        if contact_id:
            contact = Contact.query.filter_by(
                id=contact_id,
                customer_id=user.customer_id
            ).first()
            if not contact:
                return jsonify({'error': 'Contacto no encontrado'}), 404
        
        # Verificar conversación si se proporciona
        conversation_id = data.get('conversation_id')
        if conversation_id:
            conversation = Conversation.query.filter_by(
                id=conversation_id,
                customer_id=user.customer_id
            ).first()
            if not conversation:
                return jsonify({'error': 'Conversación no encontrada'}), 404
        
        ticket = Ticket(
            customer_id=user.customer_id,
            title=data['title'],
            description=data.get('description'),
            priority=priority,
            category=data.get('category'),
            tags=data.get('tags', []),
            contact_id=contact_id,
            conversation_id=conversation_id,
            assigned_to=data.get('assigned_to')
        )
        
        db.session.add(ticket)
        db.session.commit()
        
        return jsonify({
            'message': 'Ticket creado exitosamente',
            'ticket': {
                'id': ticket.id,
                'title': ticket.title,
                'description': ticket.description,
                'status': ticket.status,
                'priority': ticket.priority,
                'category': ticket.category,
                'tags': ticket.tags
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error interno del servidor'}), 500

@tickets_bp.route('/<ticket_id>', methods=['PUT'])
@jwt_required()
def update_ticket(ticket_id):
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        data = request.get_json()
        
        ticket = Ticket.query.filter_by(
            id=ticket_id,
            customer_id=user.customer_id
        ).first()
        
        if not ticket:
            return jsonify({'error': 'Ticket no encontrado'}), 404
        
        # Actualizar campos
        if 'title' in data:
            ticket.title = data['title']
        if 'description' in data:
            ticket.description = data['description']
        if 'priority' in data and data['priority'] in ['low', 'normal', 'high', 'urgent']:
            ticket.priority = data['priority']
        if 'category' in data:
            ticket.category = data['category']
        if 'tags' in data:
            ticket.tags = data['tags']
        if 'resolution' in data:
            ticket.resolution = data['resolution']
        
        ticket.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Ticket actualizado exitosamente',
            'ticket': {
                'id': ticket.id,
                'title': ticket.title,
                'description': ticket.description,
                'status': ticket.status,
                'priority': ticket.priority,
                'category': ticket.category,
                'tags': ticket.tags,
                'resolution': ticket.resolution
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error interno del servidor'}), 500

@tickets_bp.route('/<ticket_id>/assign', methods=['POST'])
@jwt_required()
def assign_ticket(ticket_id):
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        data = request.get_json()
        agent_id = data.get('agent_id')
        
        ticket = Ticket.query.filter_by(
            id=ticket_id,
            customer_id=user.customer_id
        ).first()
        
        if not ticket:
            return jsonify({'error': 'Ticket no encontrado'}), 404
        
        # Verificar que el agente pertenece al mismo cliente
        if agent_id:
            agent = User.query.filter_by(
                id=agent_id,
                customer_id=user.customer_id,
                is_active=True
            ).first()
            
            if not agent:
                return jsonify({'error': 'Agente no encontrado'}), 404
        
        ticket.assigned_to = agent_id
        if agent_id and ticket.status == 'open':
            ticket.status = 'in_progress'
        ticket.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Ticket asignado exitosamente',
            'ticket': {
                'id': ticket.id,
                'assigned_to': agent_id,
                'status': ticket.status
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error interno del servidor'}), 500

@tickets_bp.route('/<ticket_id>/status', methods=['PUT'])
@jwt_required()
def update_ticket_status(ticket_id):
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        data = request.get_json()
        status = data.get('status')
        
        if status not in ['open', 'in_progress', 'resolved', 'closed']:
            return jsonify({'error': 'Estado inválido'}), 400
        
        ticket = Ticket.query.filter_by(
            id=ticket_id,
            customer_id=user.customer_id
        ).first()
        
        if not ticket:
            return jsonify({'error': 'Ticket no encontrado'}), 404
        
        ticket.status = status
        
        # Si se resuelve o cierra, marcar fecha
        if status in ['resolved', 'closed'] and not ticket.resolved_at:
            ticket.resolved_at = datetime.utcnow()
        
        ticket.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Estado actualizado exitosamente',
            'ticket': {
                'id': ticket.id,
                'status': ticket.status,
                'resolved_at': ticket.resolved_at.isoformat() if ticket.resolved_at else None
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error interno del servidor'}), 500

@tickets_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_ticket_stats():
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        # Estadísticas básicas
        total = Ticket.query.filter_by(customer_id=user.customer_id).count()
        open_count = Ticket.query.filter_by(customer_id=user.customer_id, status='open').count()
        in_progress = Ticket.query.filter_by(customer_id=user.customer_id, status='in_progress').count()
        resolved = Ticket.query.filter_by(customer_id=user.customer_id, status='resolved').count()
        closed = Ticket.query.filter_by(customer_id=user.customer_id, status='closed').count()
        
        # Tickets por prioridad
        high_priority = Ticket.query.filter_by(
            customer_id=user.customer_id,
            priority='high'
        ).filter(Ticket.status.in_(['open', 'in_progress'])).count()
        
        urgent_priority = Ticket.query.filter_by(
            customer_id=user.customer_id,
            priority='urgent'
        ).filter(Ticket.status.in_(['open', 'in_progress'])).count()
        
        # Tickets asignados al usuario actual
        my_tickets = Ticket.query.filter_by(
            customer_id=user.customer_id,
            assigned_to=user.id
        ).filter(Ticket.status.in_(['open', 'in_progress'])).count()
        
        return jsonify({
            'stats': {
                'total': total,
                'open': open_count,
                'in_progress': in_progress,
                'resolved': resolved,
                'closed': closed,
                'high_priority': high_priority,
                'urgent_priority': urgent_priority,
                'my_tickets': my_tickets
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Error interno del servidor'}), 500

