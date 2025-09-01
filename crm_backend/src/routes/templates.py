from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.database import db, User, Template
from datetime import datetime

templates_bp = Blueprint('templates', __name__)

def get_current_user():
    user_id = get_jwt_identity()
    return User.query.get(user_id)

@templates_bp.route('/', methods=['GET'])
@jwt_required()
def get_templates():
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        # Parámetros de consulta
        category = request.args.get('category')
        template_type = request.args.get('type')
        search = request.args.get('search')
        
        # Construir consulta base
        query = Template.query.filter_by(
            customer_id=user.customer_id,
            is_active=True
        )
        
        # Aplicar filtros
        if category:
            query = query.filter(Template.category == category)
        
        if template_type:
            query = query.filter(Template.type == template_type)
        
        if search:
            query = query.filter(Template.name.ilike(f'%{search}%'))
        
        # Ordenar por uso y fecha
        query = query.order_by(Template.usage_count.desc(), Template.created_at.desc())
        
        templates = query.all()
        
        result = []
        for template in templates:
            result.append({
                'id': template.id,
                'name': template.name,
                'content': template.content,
                'type': template.type,
                'category': template.category,
                'variables': template.variables or [],
                'usage_count': template.usage_count,
                'created_at': template.created_at.isoformat(),
                'updated_at': template.updated_at.isoformat()
            })
        
        return jsonify({
            'templates': result
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Error interno del servidor'}), 500

@templates_bp.route('/<template_id>', methods=['GET'])
@jwt_required()
def get_template(template_id):
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        template = Template.query.filter_by(
            id=template_id,
            customer_id=user.customer_id
        ).first()
        
        if not template:
            return jsonify({'error': 'Plantilla no encontrada'}), 404
        
        return jsonify({
            'template': {
                'id': template.id,
                'name': template.name,
                'content': template.content,
                'type': template.type,
                'category': template.category,
                'variables': template.variables or [],
                'usage_count': template.usage_count,
                'is_active': template.is_active,
                'created_at': template.created_at.isoformat(),
                'updated_at': template.updated_at.isoformat()
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Error interno del servidor'}), 500

@templates_bp.route('/', methods=['POST'])
@jwt_required()
def create_template():
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        data = request.get_json()
        
        # Validar datos requeridos
        if not data.get('name') or not data.get('content'):
            return jsonify({'error': 'name y content son requeridos'}), 400
        
        # Validar tipo de plantilla
        valid_types = ['text', 'whatsapp_template', 'email']
        template_type = data.get('type', 'text')
        if template_type not in valid_types:
            return jsonify({'error': 'Tipo de plantilla inválido'}), 400
        
        # Extraer variables del contenido
        import re
        variables = re.findall(r'\{\{(\w+)\}\}', data['content'])
        
        template = Template(
            customer_id=user.customer_id,
            name=data['name'],
            content=data['content'],
            type=template_type,
            category=data.get('category'),
            variables=list(set(variables))  # Eliminar duplicados
        )
        
        db.session.add(template)
        db.session.commit()
        
        return jsonify({
            'message': 'Plantilla creada exitosamente',
            'template': {
                'id': template.id,
                'name': template.name,
                'content': template.content,
                'type': template.type,
                'category': template.category,
                'variables': template.variables
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error interno del servidor'}), 500

@templates_bp.route('/<template_id>', methods=['PUT'])
@jwt_required()
def update_template(template_id):
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        data = request.get_json()
        
        template = Template.query.filter_by(
            id=template_id,
            customer_id=user.customer_id
        ).first()
        
        if not template:
            return jsonify({'error': 'Plantilla no encontrada'}), 404
        
        # Actualizar campos
        if 'name' in data:
            template.name = data['name']
        
        if 'content' in data:
            template.content = data['content']
            # Actualizar variables automáticamente
            import re
            variables = re.findall(r'\{\{(\w+)\}\}', data['content'])
            template.variables = list(set(variables))
        
        if 'category' in data:
            template.category = data['category']
        
        if 'is_active' in data:
            template.is_active = data['is_active']
        
        template.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Plantilla actualizada exitosamente',
            'template': {
                'id': template.id,
                'name': template.name,
                'content': template.content,
                'type': template.type,
                'category': template.category,
                'variables': template.variables
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error interno del servidor'}), 500

@templates_bp.route('/<template_id>/use', methods=['POST'])
@jwt_required()
def use_template(template_id):
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        data = request.get_json()
        variables = data.get('variables', {})
        
        template = Template.query.filter_by(
            id=template_id,
            customer_id=user.customer_id
        ).first()
        
        if not template:
            return jsonify({'error': 'Plantilla no encontrada'}), 404
        
        # Reemplazar variables en el contenido
        content = template.content
        for var_name, var_value in variables.items():
            content = content.replace(f'{{{{{var_name}}}}}', str(var_value))
        
        # Incrementar contador de uso
        template.usage_count += 1
        db.session.commit()
        
        return jsonify({
            'processed_content': content,
            'original_content': template.content,
            'variables_used': variables
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error interno del servidor'}), 500

@templates_bp.route('/<template_id>', methods=['DELETE'])
@jwt_required()
def delete_template(template_id):
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        template = Template.query.filter_by(
            id=template_id,
            customer_id=user.customer_id
        ).first()
        
        if not template:
            return jsonify({'error': 'Plantilla no encontrada'}), 404
        
        db.session.delete(template)
        db.session.commit()
        
        return jsonify({
            'message': 'Plantilla eliminada exitosamente'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error interno del servidor'}), 500

@templates_bp.route('/categories', methods=['GET'])
@jwt_required()
def get_template_categories():
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        # Obtener categorías únicas de las plantillas del cliente
        categories = db.session.query(Template.category).filter_by(
            customer_id=user.customer_id,
            is_active=True
        ).distinct().all()
        
        # Categorías predefinidas
        predefined_categories = [
            'Bienvenida',
            'Soporte',
            'Ventas',
            'Seguimiento',
            'Despedida',
            'Promociones',
            'Recordatorios',
            'Confirmaciones'
        ]
        
        # Combinar categorías existentes con predefinidas
        all_categories = predefined_categories.copy()
        for cat in categories:
            if cat[0] and cat[0] not in all_categories:
                all_categories.append(cat[0])
        
        return jsonify({
            'categories': sorted(all_categories)
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Error interno del servidor'}), 500

@templates_bp.route('/import', methods=['POST'])
@jwt_required()
def import_templates():
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        data = request.get_json()
        templates_data = data.get('templates', [])
        
        if not templates_data:
            return jsonify({'error': 'No se proporcionaron plantillas'}), 400
        
        created_count = 0
        errors = []
        
        for template_data in templates_data:
            try:
                # Validar datos mínimos
                if not template_data.get('name') or not template_data.get('content'):
                    errors.append(f"Plantilla sin nombre o contenido: {template_data}")
                    continue
                
                # Extraer variables del contenido
                import re
                variables = re.findall(r'\{\{(\w+)\}\}', template_data['content'])
                
                template = Template(
                    customer_id=user.customer_id,
                    name=template_data['name'],
                    content=template_data['content'],
                    type=template_data.get('type', 'text'),
                    category=template_data.get('category'),
                    variables=list(set(variables))
                )
                
                db.session.add(template)
                created_count += 1
                
            except Exception as e:
                errors.append(f"Error procesando plantilla {template_data.get('name', 'sin nombre')}: {str(e)}")
        
        db.session.commit()
        
        return jsonify({
            'message': 'Importación completada',
            'created': created_count,
            'errors': errors
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error interno del servidor'}), 500

