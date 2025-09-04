from io import BytesIO
from PIL import Image
import io

def procesar_imagen(imagen, nuevo_nombre, tipo="articulo"):
    """
    Procesa una imagen según el tipo, redimensiona y cambia el formato.
    Retorna un objeto BytesIO listo para subir a Cloudinary.
    
    Args:
        imagen: Archivo recibido (InMemoryUploadedFile, BytesIO, etc.)
        nuevo_nombre: str -> nombre base de la imagen (ej: "Order-1")
        tipo: str -> "boleta", "logo", "articulo"
    """

    try:
        # Asegurar que sea archivo en memoria (InMemoryUploadedFile, BytesIO, etc.)
        img = Image.open(imagen)

        # Convertir a RGB si viene con canal alfa
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        # Ajustes según tipo
        if tipo == "logo":
            img = img.resize((300, 300))
            formato = "JPEG"
        elif tipo == "boleta":
            img = img.resize((1024, 1024))
            formato = "JPEG"
        elif tipo == "articulo":
            img = img.resize((800, 800))
            formato = "JPEG"
        else:
            raise serializers.ValidationError({"detail": "Tipo de imagen no soportado"})

        # Guardar en memoria
        img_io = io.BytesIO()
        img.save(img_io, formato, quality=85, optimize=True)
        img_io.seek(0)

        return img_io

    except UnidentifiedImageError:
        raise serializers.ValidationError({"detail": "El archivo no es una imagen válida"})
    except OSError:
        raise serializers.ValidationError({"detail": "Error procesando la imagen"})
