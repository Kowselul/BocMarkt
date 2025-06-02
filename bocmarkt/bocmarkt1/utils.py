from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile

def process_image(image):
    """Process image to 400x300 landscape format with white background"""
    img = Image.open(image)
    
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    ratio = min(400/img.width, 300/img.height)
    new_size = (int(img.width * ratio), int(img.height * ratio))
    img = img.resize(new_size, Image.Resampling.LANCZOS)
    
    background = Image.new('RGB', (400, 300), 'white')
    
    offset = ((400 - new_size[0]) // 2, (300 - new_size[1]) // 2)
    background.paste(img, offset)
    
    buffer = BytesIO()
    background.save(buffer, format='JPEG', quality=85)
    buffer.seek(0)
    
    return InMemoryUploadedFile(
        buffer,
        'ImageField',
        f"{image.name.split('.')[0]}.jpg",
        'image/jpeg',
        buffer.getbuffer().nbytes,
        None
    )