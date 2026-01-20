import pandas as pd
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.asistencia.models import Perfil, Empresa
from django.db import transaction

class Command(BaseCommand):
    help = 'Carga o Actualiza usuarios desde Excel'

    def add_arguments(self, parser):
        parser.add_argument('excel_file', type=str, help='Ruta al archivo Excel')

    def handle(self, *args, **kwargs):
        ruta_archivo = kwargs['excel_file']
        self.stdout.write(self.style.WARNING(f'Procesando: {ruta_archivo}...'))

        try:
            # Leemos el Excel
            df = pd.read_excel(ruta_archivo)
            # Limpiamos nombres de columnas (quita espacios al inicio/final)
            df.columns = df.columns.str.strip()
            
            # Buscamos la columna del email (acepta Email, email, Correo, CORREO)
            col_email = next((col for col in df.columns if col.lower() in ['email', 'correo', 'mail']), None)

            total_procesados = 0
            
            with transaction.atomic():
                for index, row in df.iterrows():
                    
                    rut = str(row.get('RUT', '')).strip()
                    nombres = str(row.get('Nombres', '')).strip()
                    apellidos = str(row.get('Apellidos', '')).strip()
                    nombre_empresa = str(row.get('Empresa', '')).strip()
                    cargo = str(row.get('Cargo', '')).strip()
                    
                    # Obtenemos el email si existe la columna, sino vacío
                    email = str(row.get(col_email, '')).strip() if col_email else ''
                    if email == 'nan': email = ''

                    if not rut or rut == 'nan': continue

                    # 1. Gestionar la Empresa
                    empresa_obj, _ = Empresa.objects.get_or_create(nombre=nombre_empresa)

                    # 2. CREAR O ACTUALIZAR USUARIO
                    # get_or_create devuelve el objeto y un booleano (True si fue creado recién)
                    user, created = User.objects.get_or_create(username=rut)

                    # Actualizamos SIEMPRE los datos (sea nuevo o viejo)
                    user.email = email
                    user.first_name = nombres
                    user.last_name = apellidos
                    
                    # Solo si es NUEVO asignamos la contraseña inicial
                    if created:
                        user.set_password(rut[:4])
                        accion = "CREADO"
                    else:
                        accion = "ACTUALIZADO"
                    
                    user.save()

                    # 3. Actualizar el Perfil
                    # Gracias a tu señal en models.py, el perfil ya existe. Lo traemos:
                    if hasattr(user, 'perfil'):
                        perfil = user.perfil
                        perfil.empresa = empresa_obj
                        perfil.cargo = cargo
                        perfil.rut = rut
                        
                        if accion == "NUEVO": # Solo si es nuevo
                            perfil.cambiar_pass_inicial = True # <--- FORZAMOS EL CAMBIO
                        
                        perfil.save()
                    
                    total_procesados += 1
                    msg = f'{accion}: {nombres} {apellidos} - {email}'
                    
                    if created:
                        self.stdout.write(self.style.SUCCESS(msg))
                    else:
                        self.stdout.write(self.style.WARNING(msg))
                    
                    

            self.stdout.write(self.style.SUCCESS(f'-----------------------------------'))
            self.stdout.write(self.style.SUCCESS(f'¡LISTO! Se procesaron {total_procesados} usuarios.'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))