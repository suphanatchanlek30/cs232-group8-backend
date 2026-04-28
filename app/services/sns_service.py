import logging
import re
from typing import Optional

import boto3
from botocore.exceptions import ClientError

from app.core.config import settings

logger = logging.getLogger(__name__)

class SNSService:
    def __init__(self):
        self.region = settings.AWS_REGION
        self.sns_client = None
        # We initialize the client if we're actually going to use it
        try:
            self.sns_client = boto3.client("sns", region_name=self.region)
        except Exception as e:
            logger.warning(f"Failed to initialize SNS Client: {e}")

    def publish_to_email_topic(self, topic_arn: str, subject: str, message: str) -> bool:
        """
        Publish a message to an SNS topic that has an email subscription.
        """
        if not self.sns_client:
            logger.error("SNS client is not initialized.")
            return False

        if not topic_arn:
            logger.error("No SNS Topic ARN provided.")
            return False

        try:
            response = self.sns_client.publish(
                TopicArn=topic_arn,
                Subject=subject,
                Message=message
            )
            logger.info(f"Successfully published to SNS Topic: {topic_arn}. MessageId: {response.get('MessageId')}")
            return True
        except ClientError as e:
            logger.error(f"Error publishing to SNS Topic {topic_arn}: {e}")
            return False

    def create_topic_and_subscribe(self, unit_name: str, email: str) -> Optional[str]:
        """
        Creates an SNS Topic for a unit and subscribes the email.
        Returns the TopicArn.
        """
        if not self.sns_client:
            return None
        
        try:
            # AWS SNS Topic names MUST be ASCII alphanumeric, hyphens, or underscores only.
            # Thai characters are NOT allowed.
            safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', unit_name)
            topic_name = f"tupulse-unit-{safe_name}"[:256]
            
            print(f"[SNS DEBUG] Attempting to create topic: {topic_name}")
            
            response = self.sns_client.create_topic(Name=topic_name)
            topic_arn = response.get("TopicArn")
            
            if topic_arn and email:
                print(f"[SNS DEBUG] Topic created: {topic_arn}. Subscribing {email}...")
                self.sns_client.subscribe(
                    TopicArn=topic_arn,
                    Protocol="email",
                    Endpoint=email
                )
                logger.info(f"Created Topic and subscribed {email} to {topic_arn}")
            
            return topic_arn
        except ClientError as e:
            print(f"[SNS ERROR] ClientError: {str(e)}")
            logger.error(f"Failed to create SNS topic/subscribe for unit {unit_name}: {e}")
            return None
        except Exception as e:
            print(f"[SNS ERROR] Unexpected Error: {str(e)}")
            return None

sns_service = SNSService()