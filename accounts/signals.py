from .utils import (
    # generate_student_credentials,
    generate_lecturer_credentials,
    send_new_account_email,
)


def post_save_account_receiver(instance=None, created=False, *args, **kwargs):
    """
    Send email notification
    """
    if created:
        if instance.is_student:
            username = instance.username  # Asignamos el username de la instancia
            password = username  # La contraseña es igual al username
            print(f"Generated credentials for student: {username}, {password}")  # Imprime las credenciales generadas
            instance.set_password(password)  # La contraseña se convierte en hash
            instance.save()
            send_new_account_email(instance, password)

        if instance.is_lecturer:    
            username, password = generate_lecturer_credentials()
            print(f"Generated credentials for lecturer: {username}, {password}")  # Imprime las credenciales generadas
            instance.username = username
            instance.set_password(password)  # Aquí es cuando la contraseña se convierte en hash
            instance.save()
            send_new_account_email(instance, password)
