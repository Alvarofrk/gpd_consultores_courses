import os
from OpenSSL import crypto

def generate_self_signed_cert():
    # Generar clave privada
    k = crypto.PKey()
    k.generate_key(crypto.TYPE_RSA, 2048)

    # Crear certificado
    cert = crypto.X509()
    cert.get_subject().C = "PE"
    cert.get_subject().ST = "Lima"
    cert.get_subject().L = "Lima"
    cert.get_subject().O = "GPD Consultores"
    cert.get_subject().OU = "Development"
    cert.get_subject().CN = "localhost"
    cert.set_serial_number(1000)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(365*24*60*60)  # Válido por 1 año
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(k)
    cert.sign(k, 'sha256')

    # Crear directorio si no existe
    os.makedirs('certs', exist_ok=True)

    # Guardar certificado
    with open("certs/cert.pem", "wb") as f:
        f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
    
    # Guardar clave privada
    with open("certs/key.pem", "wb") as f:
        f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k))

if __name__ == '__main__':
    generate_self_signed_cert()
    print("Certificados SSL generados en el directorio 'certs'") 