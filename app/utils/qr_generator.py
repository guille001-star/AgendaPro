import qrcode
import io
import base64

def generate_qr_code(url):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convertir imagen a base64 para mostrarla en HTML sin guardar archivo
    data = io.BytesIO()
    img.save(data, "PNG")
    encoded_img = base64.b64encode(data.getvalue()).decode('utf-8')
    
    return encoded_img