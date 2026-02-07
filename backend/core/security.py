from cryptography.fernet import Fernet
import base64
import os
from typing import Optional

class SecretManager:
    """Handles encryption and decryption of sensitive API keys using Fernet."""
    
    def __init__(self, master_key: Optional[str] = None):
        if not master_key:
            # For development, generate a key if not provided
            # In production, this MUST be loaded from environment variables
            self.key = Fernet.generate_key()
        else:
            self.key = master_key.encode() if isinstance(master_key, str) else master_key
            
        self.fernet = Fernet(self.key)

    def encrypt(self, data: str) -> str:
        """Encrypts a string and returns a URL-safe base64 encoded string."""
        return self.fernet.encrypt(data.encode()).decode()

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypts an encrypted string."""
        return self.fernet.decrypt(encrypted_data.encode()).decode()

    @staticmethod
    def generate_master_key() -> str:
        """Utility to generate a new master key for configuration."""
        return Fernet.generate_key().decode()

# Global instance for easy access if needed (prefer dependency injection)
secret_manager = SecretManager(os.getenv("MASTER_ENCRYPTION_KEY"))
