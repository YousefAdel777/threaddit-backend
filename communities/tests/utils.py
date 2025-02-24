import tempfile
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile

def create_temp_image_file():
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
        image = Image.new("RGB", (100, 100), color=(255, 0, 0))
        image.save(temp_file, format="PNG")
        temp_file.seek(0)
        return SimpleUploadedFile(temp_file.name, temp_file.read(), content_type="image/png")