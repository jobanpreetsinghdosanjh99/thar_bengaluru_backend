from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
import os
from typing import List


class Settings(BaseSettings):
    """Application settings from environment variables."""
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    
    # Database Configuration
    database_url: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/thar_bengaluru_db")
    
    # JWT Configuration
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Server Configuration
    environment: str = os.getenv("ENVIRONMENT", "development")
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    debug: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # CORS Configuration (stored as string, converted to listvia property)
    cors_origins_str: str = Field(default=os.getenv("CORS_ORIGINS", "http://localhost:3000"), alias="CORS_ORIGINS")
    
    # Payment Gateway Configuration
    razorpay_key_id: str = os.getenv("RAZORPAY_KEY_ID", "")
    razorpay_key_secret: str = os.getenv("RAZORPAY_KEY_SECRET", "")
    phonepe_merchant_id: str = os.getenv("PHONEPE_MERCHANT_ID", "")
    phonepe_salt_key: str = os.getenv("PHONEPE_SALT_KEY", "")
    phonepe_salt_index: int = int(os.getenv("PHONEPE_SALT_INDEX", "1"))
    
    # Email Service Configuration
    smtp_host: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_user: str = os.getenv("SMTP_USER", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    smtp_from_email: str = os.getenv("SMTP_FROM_EMAIL", "noreply@tharbengaluru.com")
    smtp_from_name: str = os.getenv("SMTP_FROM_NAME", "THAR Bengaluru")
    
    # WhatsApp Business API Configuration
    whatsapp_api_url: str = os.getenv("WHATSAPP_API_URL", "https://graph.facebook.com/v17.0")
    whatsapp_phone_number_id: str = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
    whatsapp_access_token: str = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
    
    # SMS Gateway Configuration
    sms_gateway_url: str = os.getenv("SMS_GATEWAY_URL", "https://api.twilio.com/2010-04-01")
    sms_account_sid: str = os.getenv("SMS_ACCOUNT_SID", "")
    sms_auth_token: str = os.getenv("SMS_AUTH_TOKEN", "")
    sms_from_number: str = os.getenv("SMS_FROM_NUMBER", "")
    
    @property
    def cors_origins(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins_str.split(",") if origin.strip()]
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"


settings = Settings()
