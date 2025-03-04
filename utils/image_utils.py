from PIL import Image

def is_image_valid(file_stream):
    try:
        image = Image.open(file_stream)
        image.verify()  # Vérifie l'intégrité de l'image
        file_stream.seek(0)  # Remet le curseur au début pour une utilisation ultérieure
        return True
    except Exception as e:
        print(f"Image invalid: {e}")
        return False
