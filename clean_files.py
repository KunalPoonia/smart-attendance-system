
import os

def clean_file(filepath):
    try:
        with open(filepath, 'rb') as f:
            content = f.read()
            
        # Remove BOM if present
        if content.startswith(b'\xef\xbb\xbf'):
            content = content[3:]
        elif content.startswith(b'\xff\xfe'):
            content = content[2:]
            
        # Remove null bytes
        content = content.replace(b'\x00', b'')
        
        with open(filepath, 'wb') as f:
            f.write(content)
        print(f"Cleaned {filepath}")
    except Exception as e:
        print(f"Error cleaning {filepath}: {e}")

for root, dirs, files in os.walk('.'):
    for file in files:
        if file.endswith('.py'):
            clean_file(os.path.join(root, file))
