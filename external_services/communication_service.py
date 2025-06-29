import requests
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from django.conf import settings

logger = logging.getLogger(__name__)


class CommunicationService:
    """Mock communication service for testing integrations."""
    
    def __init__(self, base_url: str = "https://api.emailservice.com/v1", api_key: str = "test_email_key"):
        self.base_url = base_url
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })
    
    def send_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send an email."""
        try:
            response = self.session.post(
                f"{self.base_url}/emails",
                json=email_data
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending email: {e}")
            raise
    
    def send_notification(self, notification_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send a notification."""
        try:
            response = self.session.post(
                f"{self.base_url}/notifications",
                json=notification_data
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending notification: {e}")
            raise
    
    def get_message_status(self, message_id: str) -> Dict[str, Any]:
        """Get message delivery status."""
        try:
            response = self.session.get(f"{self.base_url}/messages/{message_id}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting message status: {e}")
            raise
    
    def list_messages(self, **params) -> Dict[str, Any]:
        """List messages."""
        try:
            response = self.session.get(f"{self.base_url}/messages", params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error listing messages: {e}")
            raise
    
    def create_template(self, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create an email template."""
        try:
            response = self.session.post(
                f"{self.base_url}/templates",
                json=template_data
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating template: {e}")
            raise


class MockCommunicationService:
    """Mock implementation for testing without external API calls."""
    
    def __init__(self):
        self.messages = {}
        self.templates = {}
        self.next_message_id = 1
        self.next_template_id = 1
    
    def send_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send a mock email."""
        message_id = f"msg_{self.next_message_id}"
        self.next_message_id += 1
        
        # Simulate delivery success/failure
        recipient = email_data.get('to', '')
        success = '@' in recipient and '.' in recipient.split('@')[1]  # Simple validation
        
        message = {
            'id': message_id,
            'type': 'email',
            'to': email_data.get('to'),
            'from': email_data.get('from', 'noreply@example.com'),
            'subject': email_data.get('subject', ''),
            'template': email_data.get('template'),
            'status': 'delivered' if success else 'bounced',
            'delivery_time_ms': 1250 if success else None,
            'bounce_reason': None if success else 'recipient_not_found',
            'created_at': datetime.now().isoformat(),
            'delivered_at': datetime.now().isoformat() if success else None
        }
        
        self.messages[message_id] = message
        return message
    
    def send_notification(self, notification_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send a mock notification."""
        message_id = f"msg_{self.next_message_id}"
        self.next_message_id += 1
        
        message = {
            'id': message_id,
            'type': 'notification',
            'recipient': notification_data.get('recipient'),
            'template': notification_data.get('template'),
            'channel': notification_data.get('channel', 'email'),
            'status': 'sent',
            'created_at': datetime.now().isoformat(),
            'sent_at': datetime.now().isoformat()
        }
        
        self.messages[message_id] = message
        return message
    
    def get_message_status(self, message_id: str) -> Dict[str, Any]:
        """Get mock message status."""
        if message_id not in self.messages:
            raise ValueError(f"Message not found: {message_id}")
        
        return self.messages[message_id]
    
    def list_messages(self, **params) -> Dict[str, Any]:
        """List mock messages."""
        messages = list(self.messages.values())
        
        # Apply filters
        if 'type' in params:
            messages = [msg for msg in messages if msg['type'] == params['type']]
        
        if 'status' in params:
            messages = [msg for msg in messages if msg['status'] == params['status']]
        
        if 'recipient' in params:
            messages = [msg for msg in messages if msg.get('to') == params['recipient'] or msg.get('recipient') == params['recipient']]
        
        return {
            'messages': messages,
            'total': len(messages),
            'page': params.get('page', 1),
            'per_page': params.get('per_page', 20)
        }
    
    def create_template(self, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a mock email template."""
        template_id = f"tpl_{self.next_template_id}"
        self.next_template_id += 1
        
        template = {
            'id': template_id,
            'name': template_data.get('name'),
            'subject': template_data.get('subject'),
            'html_content': template_data.get('html_content'),
            'text_content': template_data.get('text_content'),
            'variables': template_data.get('variables', []),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        self.templates[template_id] = template
        return template
    
    def get_template(self, template_id: str) -> Dict[str, Any]:
        """Get a mock template."""
        if template_id not in self.templates:
            raise ValueError(f"Template not found: {template_id}")
        
        return self.templates[template_id]
    
    def update_template(self, template_id: str, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a mock template."""
        if template_id not in self.templates:
            raise ValueError(f"Template not found: {template_id}")
        
        template = self.templates[template_id]
        template.update(template_data)
        template['updated_at'] = datetime.now().isoformat()
        
        return template
    
    def delete_template(self, template_id: str) -> Dict[str, Any]:
        """Delete a mock template."""
        if template_id not in self.templates:
            raise ValueError(f"Template not found: {template_id}")
        
        del self.templates[template_id]
        return {'id': template_id, 'deleted': True}
    
    def list_templates(self, **params) -> Dict[str, Any]:
        """List mock templates."""
        templates = list(self.templates.values())
        
        return {
            'templates': templates,
            'total': len(templates),
            'page': params.get('page', 1),
            'per_page': params.get('per_page', 20)
        }
    
    def send_bulk_email(self, bulk_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send bulk emails."""
        recipients = bulk_data.get('recipients', [])
        template_id = bulk_data.get('template_id')
        variables = bulk_data.get('variables', {})
        
        message_ids = []
        for recipient in recipients:
            email_data = {
                'to': recipient,
                'template': template_id,
                'variables': variables
            }
            message = self.send_email(email_data)
            message_ids.append(message['id'])
        
        return {
            'campaign_id': f"camp_{len(message_ids)}",
            'message_ids': message_ids,
            'total_sent': len(message_ids),
            'status': 'completed'
        }
    
    def get_delivery_stats(self, **params) -> Dict[str, Any]:
        """Get delivery statistics."""
        messages = list(self.messages.values())
        
        total = len(messages)
        delivered = len([msg for msg in messages if msg['status'] == 'delivered'])
        bounced = len([msg for msg in messages if msg['status'] == 'bounced'])
        failed = len([msg for msg in messages if msg['status'] == 'failed'])
        
        return {
            'total': total,
            'delivered': delivered,
            'bounced': bounced,
            'failed': failed,
            'delivery_rate': (delivered / total * 100) if total > 0 else 0,
            'bounce_rate': (bounced / total * 100) if total > 0 else 0
        }


# Factory function to get the appropriate service
def get_communication_service(use_mock: bool = True) -> CommunicationService:
    """Get communication service instance."""
    if use_mock:
        return MockCommunicationService()
    else:
        return CommunicationService()
