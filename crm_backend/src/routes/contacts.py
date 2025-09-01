from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.database import db, User, Contact
from datetime import datetime
from sqlalchemy import or_

contacts_bp = Blueprint('contacts', __name__)

def get_current_user():
    user_id = get_jwt_identity()
    return User.query.get(user_id)

@contacts_bp.route('/', methods=['GET'])
@jwt_required()
def get_contacts():
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        # Parámetros de consulta
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        search = request.args.get('search')
        tags = request.args.get('tags')
        
        # Construir consulta base
        query = Contact.query.filter_by(
            customer_id=user.customer_id,
            is_blocked=False
        )
        
        # Aplicar filtros
        if search:
            query = query.filter(
                or_(
                    Contact.name.ilike(f'%{search}%'),
                    Contact.email.ilike(f'%{search}%'),
                    Contact.phone.ilike(f'%{search}%')
                )
            )
        
        if tags:
            tag_list = tags.split(',')
            # Filtrar por tags (asumiendo que tags es un array JSON)
            for tag in tag_list:
                query = query.filter(Contact.tags.contains([tag]))
        
        # Ordenar por nombre
        query = query.order_by(Contact.name)
        
        # Paginación
        contacts = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        # Formatear respuesta
        result = []
        for contact in contacts.items:
            result.append({
                'id': contact.id,
                'name': contact.name,
                'email': contact.email,
                'phone': contact.phone,
                'whatsapp_id': contact.whatsapp_id,
                'instagram_id': contact.instagram_id,
                'messenger_id': contact.messenger_id,
                'telegram_id': contact.telegram_id,
                'tags': contact.tags or [],
                'custom_fields': contact.custom_fields or {},
                'created_at': contact.created_at.isoformat(),
                'updated_at': contact.updated_at.isoformat()
            })
        
        return jsonify({
            'contacts': result,
            'pagination': {
                'page': contacts.page,
                'pages': contacts.pages,
                'per_page': contacts.per_page,
                'total': contacts.total,
                'has_next': contacts.has_next,
                'has_prev': contacts.has_prev
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Error interno del servidor'}), 500

@contacts_bp.route('/<contact_id>', methods=['GET'])
@jwt_required()
def get_contact(contact_id):
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        contact = Contact.query.filter_by(
            id=contact_id,
            customer_id=user.customer_id
        ).first()
        
        if not contact:
            return jsonify({'error': 'Contacto no encontrado'}), 404
        
        # Obtener estadísticas del contacto
        from src.models.database import Conversation, Message, Ticket
        
        conversations_count = Conversation.query.filter_by(contact_id=contact_id).count()
        messages_count = Message.query.join(Conversation).filter(
            Conversation.contact_id == contact_id
        ).count()
        tickets_count = Ticket.query.filter_by(contact_id=contact_id).count()
        
        return jsonify({
            'contact': {
                'id': contact.id,
                'name': contact.name,
                'email': contact.email,
                'phone': contact.phone,
                'whatsapp_id': contact.whatsapp_id,
                'instagram_id': contact.instagram_id,
                'messenger_id': contact.messenger_id,
                'telegram_id': contact.telegram_id,
                'tags': contact.tags or [],
                'custom_fields': contact.custom_fields or {},
                'is_blocked': contact.is_blocked,
                'created_at': contact.created_at.isoformat(),
                'updated_at': contact.updated_at.isoformat(),
                'stats': {
                    'conversations': conversations_count,
                    'messages': messages_count,
                    'tickets': tickets_count
                }
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Error interno del servidor'}), 500

@contacts_bp.route('/', methods=['POST'])
@jwt_required()
def create_contact():
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        data = request.get_json()
        
        # Validar que al menos un campo de contacto esté presente
        if not any([data.get('name'), data.get('email'), data.get('phone'), 
                   data.get('whatsapp_id'), data.get('instagram_id'), data.get('messenger_id')]):
            return jsonify({'error': 'Al menos un campo de contacto es requerido'}), 400
        
        # Verificar si el contacto ya existe
        existing_contact = None
        if data.get('email'):
            existing_contact = Contact.query.filter_by(
                customer_id=user.customer_id,
                email=data['email']
            ).first()
        elif data.get('phone'):
            existing_contact = Contact.query.filter_by(
                customer_id=user.customer_id,
                phone=data['phone']
            ).first()
        
        if existing_contact:
            return jsonify({'error': 'El contacto ya existe'}), 409
        
        contact = Contact(
            customer_id=user.customer_id,
            name=data.get('name'),
            email=data.get('email'),
            phone=data.get('phone'),
            whatsapp_id=data.get('whatsapp_id'),
            instagram_id=data.get('instagram_id'),
            messenger_id=data.get('messenger_id'),
            telegram_id=data.get('telegram_id'),
            tags=data.get('tags', []),
            custom_fields=data.get('custom_fields', {})
        )
        
        db.session.add(contact)
        db.session.commit()
        
        return jsonify({
            'message': 'Contacto creado exitosamente',
            'contact': {
                'id': contact.id,
                'name': contact.name,
                'email': contact.email,
                'phone': contact.phone,
                'whatsapp_id': contact.whatsapp_id,
                'instagram_id': contact.instagram_id,
                'messenger_id': contact.messenger_id,
                'telegram_id': contact.telegram_id,
                'tags': contact.tags,
                'custom_fields': contact.custom_fields
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error interno del servidor'}), 500

@contacts_bp.route('/<contact_id>', methods=['PUT'])
@jwt_required()
def update_contact(contact_id):
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        data = request.get_json()
        
        contact = Contact.query.filter_by(
            id=contact_id,
            customer_id=user.customer_id
        ).first()
        
        if not contact:
            return jsonify({'error': 'Contacto no encontrado'}), 404
        
        # Actualizar campos
        if 'name' in data:
            contact.name = data['name']
        if 'email' in data:
            contact.email = data['email']
        if 'phone' in data:
            contact.phone = data['phone']
        if 'whatsapp_id' in data:
            contact.whatsapp_id = data['whatsapp_id']
        if 'instagram_id' in data:
            contact.instagram_id = data['instagram_id']
        if 'messenger_id' in data:
            contact.messenger_id = data['messenger_id']
        if 'telegram_id' in data:
            contact.telegram_id = data['telegram_id']
        if 'tags' in data:
            contact.tags = data['tags']
        if 'custom_fields' in data:
            contact.custom_fields = data['custom_fields']
        
        contact.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Contacto actualizado exitosamente',
            'contact': {
                'id': contact.id,
                'name': contact.name,
                'email': contact.email,
                'phone': contact.phone,
                'whatsapp_id': contact.whatsapp_id,
                'instagram_id': contact.instagram_id,
                'messenger_id': contact.messenger_id,
                'telegram_id': contact.telegram_id,
                'tags': contact.tags,
                'custom_fields': contact.custom_fields
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error interno del servidor'}), 500

@contacts_bp.route('/<contact_id>/block', methods=['POST'])
@jwt_required()
def block_contact(contact_id):
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        contact = Contact.query.filter_by(
            id=contact_id,
            customer_id=user.customer_id
        ).first()
        
        if not contact:
            return jsonify({'error': 'Contacto no encontrado'}), 404
        
        contact.is_blocked = True
        contact.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Contacto bloqueado exitosamente'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error interno del servidor'}), 500

@contacts_bp.route('/<contact_id>/unblock', methods=['POST'])
@jwt_required()
def unblock_contact(contact_id):
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        contact = Contact.query.filter_by(
            id=contact_id,
            customer_id=user.customer_id
        ).first()
        
        if not contact:
            return jsonify({'error': 'Contacto no encontrado'}), 404
        
        contact.is_blocked = False
        contact.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Contacto desbloqueado exitosamente'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error interno del servidor'}), 500

@contacts_bp.route('/import', methods=['POST'])
@jwt_required()
def import_contacts():
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        data = request.get_json()
        contacts_data = data.get('contacts', [])
        
        if not contacts_data:
            return jsonify({'error': 'No se proporcionaron contactos'}), 400
        
        created_count = 0
        updated_count = 0
        errors = []
        
        for contact_data in contacts_data:
            try:
                # Buscar contacto existente por email o teléfono
                existing_contact = None
                if contact_data.get('email'):
                    existing_contact = Contact.query.filter_by(
                        customer_id=user.customer_id,
                        email=contact_data['email']
                    ).first()
                elif contact_data.get('phone'):
                    existing_contact = Contact.query.filter_by(
                        customer_id=user.customer_id,
                        phone=contact_data['phone']
                    ).first()
                
                if existing_contact:
                    # Actualizar contacto existente
                    for field in ['name', 'email', 'phone', 'whatsapp_id', 'instagram_id', 'messenger_id']:
                        if field in contact_data:
                            setattr(existing_contact, field, contact_data[field])
                    existing_contact.updated_at = datetime.utcnow()
                    updated_count += 1
                else:
                    # Crear nuevo contacto
                    contact = Contact(
                        customer_id=user.customer_id,
                        name=contact_data.get('name'),
                        email=contact_data.get('email'),
                        phone=contact_data.get('phone'),
                        whatsapp_id=contact_data.get('whatsapp_id'),
                        instagram_id=contact_data.get('instagram_id'),
                        messenger_id=contact_data.get('messenger_id'),
                        telegram_id=contact_data.get('telegram_id'),
                        tags=contact_data.get('tags', []),
                        custom_fields=contact_data.get('custom_fields', {})
                    )
                    db.session.add(contact)
                    created_count += 1
                    
            except Exception as e:
                errors.append(f"Error procesando contacto: {str(e)}")
        
        db.session.commit()
        
        return jsonify({
            'message': 'Importación completada',
            'created': created_count,
            'updated': updated_count,
            'errors': errors
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error interno del servidor'}), 500

