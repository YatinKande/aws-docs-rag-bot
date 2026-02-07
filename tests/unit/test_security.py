import pytest
from backend.core.security import SecretManager

def test_encryption_decryption():
    dev_key = SecretManager.generate_master_key()
    manager = SecretManager(dev_key)
    original_text = "aws_secret_key_123"
    
    encrypted = manager.encrypt(original_text)
    assert encrypted != original_text
    
    decrypted = manager.decrypt(encrypted)
    assert decrypted == original_text

def test_generate_key():
    key = SecretManager.generate_master_key()
    assert isinstance(key, str)
    assert len(key) > 0
