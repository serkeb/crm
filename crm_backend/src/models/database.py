from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

db = SQLAlchemy()

def generate_uuid():
    return str(uuid.uuid4())

# Modelo de Usuario
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='agent')  # admin, manager, agent
    is_active = db.Column(db.Boolean, default=True)
    customer_id = db.Column(db.String(36), db.ForeignKey('customers.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    customer = db.relationship('Customer', backref='users')
    assigned_conversations = db.relationship('Conversation', backref='assigned_agent')
    assigned_tickets = db.relationship('Ticket', backref='assigned_agent')

# Modelo de Cliente (Tenant)
class Customer(db.Model):
    __tablename__ = 'customers'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    phone = db.Column(db.String(50))
    company = db.Column(db.String(255))
    subscription_plan = db.Column(db.String(50), default='starter')  # starter, professional, enterprise
    is_active = db.Column(db.Boolean, default=True)
    settings = db.Column(db.JSON)  # Configuraciones personalizadas
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Modelo de Contacto
class Contact(db.Model):
    __tablename__ = 'contacts'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    customer_id = db.Column(db.String(36), db.ForeignKey('customers.id'), nullable=False)
    name = db.Column(db.String(255))
    email = db.Column(db.String(255))
    phone = db.Column(db.String(50))
    whatsapp_id = db.Column(db.String(100))
    instagram_id = db.Column(db.String(100))
    messenger_id = db.Column(db.String(100))
    telegram_id = db.Column(db.String(100))
    tags = db.Column(db.JSON)  # Array de tags
    custom_fields = db.Column(db.JSON)  # Campos personalizados
    is_blocked = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    customer = db.relationship('Customer', backref='contacts')
    conversations = db.relationship('Conversation', backref='contact')

# Modelo de Canal
class Channel(db.Model):
    __tablename__ = 'channels'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    customer_id = db.Column(db.String(36), db.ForeignKey('customers.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # whatsapp, instagram, messenger, sms, email
    name = db.Column(db.String(255), nullable=False)
    config = db.Column(db.JSON)  # Configuración específica del canal
    credentials = db.Column(db.JSON)  # Credenciales encriptadas
    is_active = db.Column(db.Boolean, default=True)
    is_connected = db.Column(db.Boolean, default=False)
    last_sync = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    customer = db.relationship('Customer', backref='channels')
    conversations = db.relationship('Conversation', backref='channel')

# Modelo de Conversación
class Conversation(db.Model):
    __tablename__ = 'conversations'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    customer_id = db.Column(db.String(36), db.ForeignKey('customers.id'), nullable=False)
    contact_id = db.Column(db.String(36), db.ForeignKey('contacts.id'), nullable=False)
    channel_id = db.Column(db.String(36), db.ForeignKey('channels.id'), nullable=False)
    assigned_to = db.Column(db.String(36), db.ForeignKey('users.id'))
    status = db.Column(db.String(50), default='open')  # open, assigned, closed, archived
    priority = db.Column(db.String(50), default='normal')  # low, normal, high, urgent
    subject = db.Column(db.String(500))
    tags = db.Column(db.JSON)
    extra_data = db.Column(db.JSON)  # Metadatos adicionales
    last_message_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    customer = db.relationship('Customer', backref='conversations')
    messages = db.relationship('Message', backref='conversation', cascade='all, delete-orphan')

# Modelo de Mensaje
class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    conversation_id = db.Column(db.String(36), db.ForeignKey('conversations.id'), nullable=False)
    external_id = db.Column(db.String(255))  # ID del mensaje en la plataforma externa
    direction = db.Column(db.String(20), nullable=False)  # inbound, outbound
    type = db.Column(db.String(50), nullable=False)  # text, image, document, audio, video, location
    content = db.Column(db.JSON)  # Contenido del mensaje
    sender_type = db.Column(db.String(50))  # contact, agent, system
    sender_id = db.Column(db.String(36))
    status = db.Column(db.String(50), default='sent')  # sent, delivered, read, failed
    extra_data = db.Column(db.JSON)  # Metadatos adicionales
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Modelo de Ticket
class Ticket(db.Model):
    __tablename__ = 'tickets'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    customer_id = db.Column(db.String(36), db.ForeignKey('customers.id'), nullable=False)
    conversation_id = db.Column(db.String(36), db.ForeignKey('conversations.id'))
    contact_id = db.Column(db.String(36), db.ForeignKey('contacts.id'))
    assigned_to = db.Column(db.String(36), db.ForeignKey('users.id'))
    title = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default='open')  # open, in_progress, resolved, closed
    priority = db.Column(db.String(50), default='normal')  # low, normal, high, urgent
    category = db.Column(db.String(100))
    tags = db.Column(db.JSON)
    resolution = db.Column(db.Text)
    resolved_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    customer = db.relationship('Customer', backref='tickets')
    conversation = db.relationship('Conversation', backref='tickets')
    contact = db.relationship('Contact', backref='tickets')

# Modelo de Automatización
class Automation(db.Model):
    __tablename__ = 'automations'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    customer_id = db.Column(db.String(36), db.ForeignKey('customers.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    trigger_type = db.Column(db.String(100), nullable=False)  # keyword, time, new_conversation, etc.
    trigger_config = db.Column(db.JSON)
    actions = db.Column(db.JSON)  # Array de acciones a ejecutar
    conditions = db.Column(db.JSON)  # Condiciones adicionales
    is_active = db.Column(db.Boolean, default=True)
    execution_count = db.Column(db.Integer, default=0)
    last_executed = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    customer = db.relationship('Customer', backref='automations')

# Modelo de Plantilla
class Template(db.Model):
    __tablename__ = 'templates'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    customer_id = db.Column(db.String(36), db.ForeignKey('customers.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), default='text')  # text, whatsapp_template
    category = db.Column(db.String(100))
    variables = db.Column(db.JSON)  # Variables disponibles en la plantilla
    usage_count = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    customer = db.relationship('Customer', backref='templates')

# Modelo de Webhook
class Webhook(db.Model):
    __tablename__ = 'webhooks'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    customer_id = db.Column(db.String(36), db.ForeignKey('customers.id'), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    events = db.Column(db.JSON)  # Array de eventos suscritos
    secret = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    last_delivery = db.Column(db.DateTime)
    failure_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    customer = db.relationship('Customer', backref='webhooks')

# Modelo de Log de Actividad
class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    customer_id = db.Column(db.String(36), db.ForeignKey('customers.id'), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'))
    action = db.Column(db.String(100), nullable=False)
    resource_type = db.Column(db.String(50))  # conversation, ticket, contact, etc.
    resource_id = db.Column(db.String(36))
    details = db.Column(db.JSON)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    customer = db.relationship('Customer', backref='activity_logs')
    user = db.relationship('User', backref='activity_logs')

