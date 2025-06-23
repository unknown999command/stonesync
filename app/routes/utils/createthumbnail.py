from PIL import Image

def create_thumbnail(image_path, thumbnail_path, size=(150, 150)):
    with Image.open(image_path) as img:
        img.thumbnail(size)
        img.save(thumbnail_path)