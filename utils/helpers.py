import hashlib

def calculate_file_hash(file):
    """
    Faylning SHA256 xeshini hisoblaydi.
    """
    # 1. Kursorni boshiga qaytarish (MUHIM!)
    file.seek(0) 
    
    sha256_hash = hashlib.sha256()
    for byte_block in iter(lambda: file.read(4096), b""):
        sha256_hash.update(byte_block)
    
    # 2. Ish tugagach, kursorni yana joyiga qaytarish (Django o'qiy olishi uchun)
    file.seek(0)
    
    return sha256_hash.hexdigest()