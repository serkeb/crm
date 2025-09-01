from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.database import db, User, Conversation, Message, Ticket, Contact, Channel
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_

reports_bp = Blueprint('reports', __name__)

def get_current_user():
    user_id = get_jwt_identity()
    return User.query.get(user_id)

@reports_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        # Obtener rango de fechas (por defecto últimos 30 días)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        
        # Estadísticas generales
        total_conversations = Conversation.query.filter_by(customer_id=user.customer_id).count()
        total_messages = Message.query.join(Conversation).filter(
            Conversation.customer_id == user.customer_id
        ).count()
        total_contacts = Contact.query.filter_by(customer_id=user.customer_id).count()
        total_tickets = Ticket.query.filter_by(customer_id=user.customer_id).count()
        
        # Conversaciones activas
        active_conversations = Conversation.query.filter_by(
            customer_id=user.customer_id,
            status='open'
        ).count()
        
        # Tickets pendientes
        pending_tickets = Ticket.query.filter_by(
            customer_id=user.customer_id
        ).filter(Ticket.status.in_(['open', 'in_progress'])).count()
        
        # Mensajes del período
        period_messages = Message.query.join(Conversation).filter(
            and_(
                Conversation.customer_id == user.customer_id,
                Message.created_at >= start_date,
                Message.created_at <= end_date
            )
        ).count()
        
        # Nuevos contactos del período
        new_contacts = Contact.query.filter(
            and_(
                Contact.customer_id == user.customer_id,
                Contact.created_at >= start_date,
                Contact.created_at <= end_date
            )
        ).count()
        
        # Distribución por canales
        channel_stats = db.session.query(
            Channel.type,
            func.count(Conversation.id).label('conversations')
        ).join(Conversation).filter(
            Conversation.customer_id == user.customer_id
        ).group_by(Channel.type).all()
        
        channel_distribution = {}
        for channel_type, count in channel_stats:
            channel_distribution[channel_type] = count
        
        # Tendencia de mensajes (últimos 7 días)
        message_trend = []
        for i in range(7):
            day = end_date - timedelta(days=i)
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            
            day_messages = Message.query.join(Conversation).filter(
                and_(
                    Conversation.customer_id == user.customer_id,
                    Message.created_at >= day_start,
                    Message.created_at < day_end
                )
            ).count()
            
            message_trend.append({
                'date': day_start.strftime('%Y-%m-%d'),
                'messages': day_messages
            })
        
        message_trend.reverse()  # Ordenar cronológicamente
        
        return jsonify({
            'stats': {
                'total_conversations': total_conversations,
                'total_messages': total_messages,
                'total_contacts': total_contacts,
                'total_tickets': total_tickets,
                'active_conversations': active_conversations,
                'pending_tickets': pending_tickets,
                'period_messages': period_messages,
                'new_contacts': new_contacts
            },
            'channel_distribution': channel_distribution,
            'message_trend': message_trend,
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Error interno del servidor'}), 500

@reports_bp.route('/conversations', methods=['GET'])
@jwt_required()
def get_conversation_report():
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        # Parámetros de consulta
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        channel_type = request.args.get('channel')
        
        # Fechas por defecto (últimos 30 días)
        if not start_date:
            start_date = (datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.utcnow().strftime('%Y-%m-%d')
        
        start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
        end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
        
        # Consulta base
        query = Conversation.query.filter(
            and_(
                Conversation.customer_id == user.customer_id,
                Conversation.created_at >= start_datetime,
                Conversation.created_at < end_datetime
            )
        )
        
        if channel_type:
            query = query.join(Channel).filter(Channel.type == channel_type)
        
        conversations = query.all()
        
        # Análisis de datos
        total_conversations = len(conversations)
        status_distribution = {}
        priority_distribution = {}
        channel_distribution = {}
        daily_conversations = {}
        
        for conv in conversations:
            # Distribución por estado
            status = conv.status
            status_distribution[status] = status_distribution.get(status, 0) + 1
            
            # Distribución por prioridad
            priority = conv.priority
            priority_distribution[priority] = priority_distribution.get(priority, 0) + 1
            
            # Distribución por canal
            channel = conv.channel.type
            channel_distribution[channel] = channel_distribution.get(channel, 0) + 1
            
            # Conversaciones por día
            day = conv.created_at.strftime('%Y-%m-%d')
            daily_conversations[day] = daily_conversations.get(day, 0) + 1
        
        # Tiempo promedio de respuesta
        response_times = []
        for conv in conversations:
            first_inbound = Message.query.filter_by(
                conversation_id=conv.id,
                direction='inbound'
            ).order_by(Message.created_at).first()
            
            first_outbound = Message.query.filter_by(
                conversation_id=conv.id,
                direction='outbound'
            ).order_by(Message.created_at).first()
            
            if first_inbound and first_outbound and first_outbound.created_at > first_inbound.created_at:
                response_time = (first_outbound.created_at - first_inbound.created_at).total_seconds() / 60
                response_times.append(response_time)
        
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        return jsonify({
            'report': {
                'total_conversations': total_conversations,
                'avg_response_time_minutes': round(avg_response_time, 2),
                'status_distribution': status_distribution,
                'priority_distribution': priority_distribution,
                'channel_distribution': channel_distribution,
                'daily_conversations': daily_conversations
            },
            'period': {
                'start_date': start_date,
                'end_date': end_date
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Error interno del servidor'}), 500

@reports_bp.route('/messages', methods=['GET'])
@jwt_required()
def get_message_report():
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        # Parámetros de consulta
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Fechas por defecto (últimos 30 días)
        if not start_date:
            start_date = (datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.utcnow().strftime('%Y-%m-%d')
        
        start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
        end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
        
        # Consulta de mensajes
        messages = Message.query.join(Conversation).filter(
            and_(
                Conversation.customer_id == user.customer_id,
                Message.created_at >= start_datetime,
                Message.created_at < end_datetime
            )
        ).all()
        
        # Análisis de datos
        total_messages = len(messages)
        inbound_messages = len([m for m in messages if m.direction == 'inbound'])
        outbound_messages = len([m for m in messages if m.direction == 'outbound'])
        
        # Distribución por tipo
        type_distribution = {}
        for msg in messages:
            msg_type = msg.type
            type_distribution[msg_type] = type_distribution.get(msg_type, 0) + 1
        
        # Mensajes por hora del día
        hourly_distribution = {}
        for msg in messages:
            hour = msg.created_at.hour
            hourly_distribution[hour] = hourly_distribution.get(hour, 0) + 1
        
        # Mensajes por día de la semana
        weekday_distribution = {}
        weekdays = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        for msg in messages:
            weekday = weekdays[msg.created_at.weekday()]
            weekday_distribution[weekday] = weekday_distribution.get(weekday, 0) + 1
        
        # Tendencia diaria
        daily_messages = {}
        for msg in messages:
            day = msg.created_at.strftime('%Y-%m-%d')
            daily_messages[day] = daily_messages.get(day, 0) + 1
        
        return jsonify({
            'report': {
                'total_messages': total_messages,
                'inbound_messages': inbound_messages,
                'outbound_messages': outbound_messages,
                'type_distribution': type_distribution,
                'hourly_distribution': hourly_distribution,
                'weekday_distribution': weekday_distribution,
                'daily_messages': daily_messages
            },
            'period': {
                'start_date': start_date,
                'end_date': end_date
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Error interno del servidor'}), 500

@reports_bp.route('/tickets', methods=['GET'])
@jwt_required()
def get_ticket_report():
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        # Parámetros de consulta
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Fechas por defecto (últimos 30 días)
        if not start_date:
            start_date = (datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.utcnow().strftime('%Y-%m-%d')
        
        start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
        end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
        
        # Consulta de tickets
        tickets = Ticket.query.filter(
            and_(
                Ticket.customer_id == user.customer_id,
                Ticket.created_at >= start_datetime,
                Ticket.created_at < end_datetime
            )
        ).all()
        
        # Análisis de datos
        total_tickets = len(tickets)
        resolved_tickets = len([t for t in tickets if t.status in ['resolved', 'closed']])
        
        # Distribución por estado
        status_distribution = {}
        for ticket in tickets:
            status = ticket.status
            status_distribution[status] = status_distribution.get(status, 0) + 1
        
        # Distribución por prioridad
        priority_distribution = {}
        for ticket in tickets:
            priority = ticket.priority
            priority_distribution[priority] = priority_distribution.get(priority, 0) + 1
        
        # Distribución por categoría
        category_distribution = {}
        for ticket in tickets:
            category = ticket.category or 'Sin categoría'
            category_distribution[category] = category_distribution.get(category, 0) + 1
        
        # Tiempo promedio de resolución
        resolution_times = []
        for ticket in tickets:
            if ticket.resolved_at:
                resolution_time = (ticket.resolved_at - ticket.created_at).total_seconds() / 3600  # horas
                resolution_times.append(resolution_time)
        
        avg_resolution_time = sum(resolution_times) / len(resolution_times) if resolution_times else 0
        
        # Tickets por agente
        agent_distribution = {}
        for ticket in tickets:
            if ticket.assigned_agent:
                agent_name = f"{ticket.assigned_agent.first_name} {ticket.assigned_agent.last_name}"
                agent_distribution[agent_name] = agent_distribution.get(agent_name, 0) + 1
            else:
                agent_distribution['Sin asignar'] = agent_distribution.get('Sin asignar', 0) + 1
        
        # Tendencia diaria
        daily_tickets = {}
        for ticket in tickets:
            day = ticket.created_at.strftime('%Y-%m-%d')
            daily_tickets[day] = daily_tickets.get(day, 0) + 1
        
        return jsonify({
            'report': {
                'total_tickets': total_tickets,
                'resolved_tickets': resolved_tickets,
                'resolution_rate': round((resolved_tickets / total_tickets * 100) if total_tickets > 0 else 0, 2),
                'avg_resolution_time_hours': round(avg_resolution_time, 2),
                'status_distribution': status_distribution,
                'priority_distribution': priority_distribution,
                'category_distribution': category_distribution,
                'agent_distribution': agent_distribution,
                'daily_tickets': daily_tickets
            },
            'period': {
                'start_date': start_date,
                'end_date': end_date
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Error interno del servidor'}), 500

@reports_bp.route('/agents', methods=['GET'])
@jwt_required()
def get_agent_performance():
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        # Parámetros de consulta
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Fechas por defecto (últimos 30 días)
        if not start_date:
            start_date = (datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.utcnow().strftime('%Y-%m-%d')
        
        start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
        end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
        
        # Obtener todos los agentes del cliente
        agents = User.query.filter_by(
            customer_id=user.customer_id,
            is_active=True
        ).all()
        
        agent_performance = []
        
        for agent in agents:
            # Conversaciones asignadas
            assigned_conversations = Conversation.query.filter(
                and_(
                    Conversation.assigned_to == agent.id,
                    Conversation.created_at >= start_datetime,
                    Conversation.created_at < end_datetime
                )
            ).count()
            
            # Tickets asignados
            assigned_tickets = Ticket.query.filter(
                and_(
                    Ticket.assigned_to == agent.id,
                    Ticket.created_at >= start_datetime,
                    Ticket.created_at < end_datetime
                )
            ).count()
            
            # Tickets resueltos
            resolved_tickets = Ticket.query.filter(
                and_(
                    Ticket.assigned_to == agent.id,
                    Ticket.status.in_(['resolved', 'closed']),
                    Ticket.created_at >= start_datetime,
                    Ticket.created_at < end_datetime
                )
            ).count()
            
            # Mensajes enviados
            sent_messages = Message.query.join(Conversation).filter(
                and_(
                    Message.sender_id == agent.id,
                    Message.direction == 'outbound',
                    Message.created_at >= start_datetime,
                    Message.created_at < end_datetime,
                    Conversation.customer_id == user.customer_id
                )
            ).count()
            
            agent_performance.append({
                'agent': {
                    'id': agent.id,
                    'name': f"{agent.first_name} {agent.last_name}",
                    'email': agent.email,
                    'role': agent.role
                },
                'metrics': {
                    'assigned_conversations': assigned_conversations,
                    'assigned_tickets': assigned_tickets,
                    'resolved_tickets': resolved_tickets,
                    'resolution_rate': round((resolved_tickets / assigned_tickets * 100) if assigned_tickets > 0 else 0, 2),
                    'sent_messages': sent_messages
                }
            })
        
        return jsonify({
            'agent_performance': agent_performance,
            'period': {
                'start_date': start_date,
                'end_date': end_date
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Error interno del servidor'}), 500

