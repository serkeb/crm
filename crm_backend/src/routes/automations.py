from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.database import db, User, Automation
from datetime import datetime

automations_bp = Blueprint('automations', __name__)

def get_current_user():
    user_id = get_jwt_identity()
    return User.query.get(user_id)

@automations_bp.route('/', methods=['GET'])
@jwt_required()
def get_automations():
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        automations = Automation.query.filter_by(customer_id=user.customer_id).all()
        
        result = []
        for automation in automations:
            result.append({
                'id': automation.id,
                'name': automation.name,
                'description': automation.description,
                'trigger_type': automation.trigger_type,
                'trigger_config': automation.trigger_config,
                'actions': automation.actions,
                'conditions': automation.conditions,
                'is_active': automation.is_active,
                'execution_count': automation.execution_count,
                'last_executed': automation.last_executed.isoformat() if automation.last_executed else None,
                'created_at': automation.created_at.isoformat(),
                'updated_at': automation.updated_at.isoformat()
            })
        
        return jsonify({
            'automations': result
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Error interno del servidor'}), 500

@automations_bp.route('/<automation_id>', methods=['GET'])
@jwt_required()
def get_automation(automation_id):
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        automation = Automation.query.filter_by(
            id=automation_id,
            customer_id=user.customer_id
        ).first()
        
        if not automation:
            return jsonify({'error': 'Automatización no encontrada'}), 404
        
        return jsonify({
            'automation': {
                'id': automation.id,
                'name': automation.name,
                'description': automation.description,
                'trigger_type': automation.trigger_type,
                'trigger_config': automation.trigger_config,
                'actions': automation.actions,
                'conditions': automation.conditions,
                'is_active': automation.is_active,
                'execution_count': automation.execution_count,
                'last_executed': automation.last_executed.isoformat() if automation.last_executed else None,
                'created_at': automation.created_at.isoformat(),
                'updated_at': automation.updated_at.isoformat()
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Error interno del servidor'}), 500

@automations_bp.route('/', methods=['POST'])
@jwt_required()
def create_automation():
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        data = request.get_json()
        
        # Validar datos requeridos
        required_fields = ['name', 'trigger_type', 'trigger_config', 'actions']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} es requerido'}), 400
        
        # Validar tipo de trigger
        valid_triggers = ['keyword', 'time', 'new_conversation', 'inactivity', 'channel_message']
        if data['trigger_type'] not in valid_triggers:
            return jsonify({'error': 'Tipo de trigger inválido'}), 400
        
        # Validar estructura de acciones
        actions = data['actions']
        if not isinstance(actions, list) or len(actions) == 0:
            return jsonify({'error': 'Se requiere al menos una acción'}), 400
        
        automation = Automation(
            customer_id=user.customer_id,
            name=data['name'],
            description=data.get('description'),
            trigger_type=data['trigger_type'],
            trigger_config=data['trigger_config'],
            actions=actions,
            conditions=data.get('conditions', {}),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(automation)
        db.session.commit()
        
        return jsonify({
            'message': 'Automatización creada exitosamente',
            'automation': {
                'id': automation.id,
                'name': automation.name,
                'description': automation.description,
                'trigger_type': automation.trigger_type,
                'is_active': automation.is_active
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error interno del servidor'}), 500

@automations_bp.route('/<automation_id>', methods=['PUT'])
@jwt_required()
def update_automation(automation_id):
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        data = request.get_json()
        
        automation = Automation.query.filter_by(
            id=automation_id,
            customer_id=user.customer_id
        ).first()
        
        if not automation:
            return jsonify({'error': 'Automatización no encontrada'}), 404
        
        # Actualizar campos
        if 'name' in data:
            automation.name = data['name']
        if 'description' in data:
            automation.description = data['description']
        if 'trigger_config' in data:
            automation.trigger_config = data['trigger_config']
        if 'actions' in data:
            automation.actions = data['actions']
        if 'conditions' in data:
            automation.conditions = data['conditions']
        if 'is_active' in data:
            automation.is_active = data['is_active']
        
        automation.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Automatización actualizada exitosamente',
            'automation': {
                'id': automation.id,
                'name': automation.name,
                'description': automation.description,
                'trigger_type': automation.trigger_type,
                'is_active': automation.is_active
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error interno del servidor'}), 500

@automations_bp.route('/<automation_id>/toggle', methods=['POST'])
@jwt_required()
def toggle_automation(automation_id):
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        automation = Automation.query.filter_by(
            id=automation_id,
            customer_id=user.customer_id
        ).first()
        
        if not automation:
            return jsonify({'error': 'Automatización no encontrada'}), 404
        
        automation.is_active = not automation.is_active
        automation.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': f'Automatización {"activada" if automation.is_active else "desactivada"} exitosamente',
            'automation': {
                'id': automation.id,
                'name': automation.name,
                'is_active': automation.is_active
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error interno del servidor'}), 500

@automations_bp.route('/<automation_id>/test', methods=['POST'])
@jwt_required()
def test_automation(automation_id):
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        automation = Automation.query.filter_by(
            id=automation_id,
            customer_id=user.customer_id
        ).first()
        
        if not automation:
            return jsonify({'error': 'Automatización no encontrada'}), 404
        
        # Simular ejecución de la automatización
        test_result = {
            'success': True,
            'message': 'Automatización ejecutada exitosamente en modo de prueba',
            'executed_actions': len(automation.actions),
            'test_timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify({
            'test_result': test_result
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Error interno del servidor'}), 500

@automations_bp.route('/<automation_id>', methods=['DELETE'])
@jwt_required()
def delete_automation(automation_id):
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        automation = Automation.query.filter_by(
            id=automation_id,
            customer_id=user.customer_id
        ).first()
        
        if not automation:
            return jsonify({'error': 'Automatización no encontrada'}), 404
        
        db.session.delete(automation)
        db.session.commit()
        
        return jsonify({
            'message': 'Automatización eliminada exitosamente'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error interno del servidor'}), 500

@automations_bp.route('/templates', methods=['GET'])
@jwt_required()
def get_automation_templates():
    try:
        templates = [
            {
                'id': 'welcome_message',
                'name': 'Mensaje de Bienvenida',
                'description': 'Envía un mensaje automático cuando llega un nuevo contacto',
                'trigger_type': 'new_conversation',
                'trigger_config': {},
                'actions': [
                    {
                        'type': 'send_message',
                        'config': {
                            'message': '¡Hola! Gracias por contactarnos. En breve un agente te atenderá.',
                            'delay': 0
                        }
                    }
                ]
            },
            {
                'id': 'keyword_response',
                'name': 'Respuesta por Palabra Clave',
                'description': 'Responde automáticamente cuando se detecta una palabra clave',
                'trigger_type': 'keyword',
                'trigger_config': {
                    'keywords': ['hola', 'ayuda', 'soporte'],
                    'match_type': 'contains'
                },
                'actions': [
                    {
                        'type': 'send_message',
                        'config': {
                            'message': 'He detectado que necesitas ayuda. Te conectaré con un agente.',
                            'delay': 1000
                        }
                    },
                    {
                        'type': 'assign_conversation',
                        'config': {
                            'assignment_type': 'next_available'
                        }
                    }
                ]
            },
            {
                'id': 'business_hours',
                'name': 'Mensaje Fuera de Horario',
                'description': 'Informa sobre horarios de atención fuera del horario laboral',
                'trigger_type': 'new_conversation',
                'trigger_config': {},
                'conditions': {
                    'business_hours': {
                        'enabled': True,
                        'timezone': 'America/Mexico_City',
                        'schedule': {
                            'monday': {'start': '09:00', 'end': '18:00'},
                            'tuesday': {'start': '09:00', 'end': '18:00'},
                            'wednesday': {'start': '09:00', 'end': '18:00'},
                            'thursday': {'start': '09:00', 'end': '18:00'},
                            'friday': {'start': '09:00', 'end': '18:00'},
                            'saturday': {'start': '09:00', 'end': '14:00'},
                            'sunday': {'closed': True}
                        }
                    }
                },
                'actions': [
                    {
                        'type': 'send_message',
                        'config': {
                            'message': 'Gracias por contactarnos. Nuestro horario de atención es de lunes a viernes de 9:00 AM a 6:00 PM y sábados de 9:00 AM a 2:00 PM. Te responderemos en cuanto estemos disponibles.',
                            'delay': 0
                        }
                    }
                ]
            },
            {
                'id': 'inactivity_followup',
                'name': 'Seguimiento por Inactividad',
                'description': 'Envía un mensaje de seguimiento después de un período de inactividad',
                'trigger_type': 'inactivity',
                'trigger_config': {
                    'duration_minutes': 60,
                    'check_last_message_from': 'contact'
                },
                'actions': [
                    {
                        'type': 'send_message',
                        'config': {
                            'message': '¿Hay algo más en lo que pueda ayudarte? Si tienes alguna pregunta adicional, no dudes en escribirme.',
                            'delay': 0
                        }
                    }
                ]
            }
        ]
        
        return jsonify({
            'templates': templates
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Error interno del servidor'}), 500

