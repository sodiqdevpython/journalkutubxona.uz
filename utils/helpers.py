import hashlib

def calculate_file_hash(file):

    file.seek(0) 
    
    sha256_hash = hashlib.sha256()
    for byte_block in iter(lambda: file.read(4096), b""):
        sha256_hash.update(byte_block)
    
    file.seek(0)
    
    return sha256_hash.hexdigest()