from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from apps.asistencia.models import Marcacion
from datetime import timedelta

class Command(BaseCommand):
    help = 'Detecta trabajadores que marcaron entrada pero no salida'

    def handle(self, *args, **kwargs):
        now = timezone.now()
        # Definimos el límite: Si pasaron más de 10 horas desde la entrada
        # (9 horas de jornada + 1 hora de colación/extra)
        LIMITE_HORAS = 10 

        # 1. Buscamos todas las ENTRADAS de hoy que NO tengan alerta enviada
        entradas_hoy = Marcacion.objects.filter(
            tipo='ENTRADA',
            timestamp__date=now.date(),
            alerta_olvido_enviada=False
        )

        count = 0
        for entrada in entradas_hoy:
            # 2. Calculamos cuánto tiempo ha pasado
            tiempo_transcurrido = now - entrada.timestamp
            horas_pasadas = tiempo_transcurrido.total_seconds() / 3600

            if horas_pasadas > LIMITE_HORAS:
                # 3. Verificamos si existe una SALIDA posterior a esa entrada
                salida_existe = Marcacion.objects.filter(
                    trabajador=entrada.trabajador,
                    tipo='SALIDA',
                    timestamp__gt=entrada.timestamp # Que sea DESPUÉS de la entrada
                ).exists()

                if not salida_existe:
                    # ¡OLVIDO DETECTADO! 🚨
                    self.enviar_alerta(entrada)
                    count += 1

        self.stdout.write(self.style.SUCCESS(f'Proceso terminado. Se enviaron {count} alertas.'))

    def enviar_alerta(self, entrada):
        trabajador = entrada.trabajador
        empresa = trabajador.perfil.empresa.nombre if hasattr(trabajador, 'perfil') else "Empresa"
        
        asunto = f"⚠️ Alerta de Asistencia: Sin marca de salida - {trabajador.get_full_name()}"
        mensaje = f"""
        Estimado/a,
        
        El trabajador {trabajador.get_full_name()} marcó ENTRADA a las {entrada.timestamp.strftime('%H:%M')}, 
        pero han pasado más de 10 horas y no se registra su SALIDA.
        
        Por favor, verificar si se trata de un olvido o una hora extra extensa.
        
        Saludos,
        Sistema de Asistencia {empresa}
        """

        try:
            # Enviar correo (puedes poner el email del jefe aquí)
            destinatarios = [trabajador.email] # Agrega el mail del jefe a la lista
            
            send_mail(asunto, mensaje, None, destinatarios)
            
            # Marcar como enviada para no repetir
            entrada.alerta_olvido_enviada = True
            entrada.save()
            print(f"📧 Correo enviado a {trabajador.email}")
            
        except Exception as e:
            print(f"Error enviando correo a {trabajador.email}: {e}")