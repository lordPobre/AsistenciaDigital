from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User
from django.conf import settings
from django.core.mail import send_mail
from datetime import datetime, timedelta
import datetime as dt_module # Alias para evitar conflicto con datetime
from apps.asistencia.models import Empresa, Marcacion, LogAlerta, Feriado, LicenciaMedica, Vacacion

class Command(BaseCommand):
    help = 'Revisa atrasos y exceso de horas extras diferenciando por empresa'

    def handle(self, *args, **kwargs):
        self.stdout.write("⏳ Iniciando revisión Multi-Empresa...")

        # USAR LOCALDATE: Vital para que tome la fecha de Chile, no la UTC
        hoy = timezone.localdate()
        # ============================================================
        # 1. FILTRO DE FERIADOS (NUEVO)
        # ============================================================
        es_feriado = Feriado.objects.filter(fecha=hoy).exists()

        if es_feriado:
            # Obtenemos el nombre para mostrarlo en el log
            nombre_festivo = Feriado.objects.get(fecha=hoy).descripcion
            self.stdout.write(self.style.SUCCESS(f"🌴 HOY ES FERIADO ({nombre_festivo}). No se enviarán alertas."))
            return  # <--- AQUÍ SE DETIENE EL SCRIPT, NO SIGUE BAJANDO

        # ============================================================
        # 2. FILTRO DE FIN DE SEMANA (OPCIONAL PERO RECOMENDADO)
        # ============================================================
        # weekday(): 0=Lunes, 4=Viernes, 5=Sabado, 6=Domingo
        if hoy.weekday() >= 5:
            self.stdout.write(self.style.SUCCESS("🎉 Es Fin de Semana. El sistema descansa."))
            return

        ahora = timezone.localtime(timezone.now())

        self.stdout.write(f"Fecha revisión: {hoy} | Hora: {ahora.strftime('%H:%M')}")

        # 1. ITERAR POR CADA EMPRESA REGISTRADA
        empresas = Empresa.objects.all()

        if not empresas.exists():
            self.stdout.write(self.style.WARNING("No hay empresas registradas."))
            return

        for empresa in empresas:
            nombre_empresa = empresa.nombre
            email_rrhh = empresa.email_rrhh

            # Si la empresa no tiene correo, saltamos
            if not email_rrhh:
                # Opcional: imprimir en pantalla para debug
                # self.stdout.write(f"Empresa '{nombre_empresa}' sin correo RRHH. Saltando...")
                continue

            self.stdout.write(f"--- Revisando: {nombre_empresa} ---")

            remitente = f"Alerta Asistencia {nombre_empresa} <{settings.EMAIL_HOST_USER}>"

            # 2. OBTENER TRABAJADORES ACTIVOS DE ESTA EMPRESA
            usuarios = User.objects.filter(
                perfil__empresa=empresa,
                is_active=True,
                is_staff=False
            )

            for user in usuarios:
            # 1. Obtener perfil de forma segura

                perfil = getattr(user, 'perfil', None)
                if not perfil:
                    continue

                # 2. ¿LE TOCA TRABAJAR HOY? (Día Libre / Part-Time) 🛑
                if not perfil.debe_trabajar_hoy():
                    # self.stdout.write(f" - {user.username} tiene libre hoy por contrato. Saltando.")
                    continue

                # 3. AQUÍ DEBERÍA IR EL FILTRO DE VACACIONES/LICENCIAS (Que vimos antes)
                # Recuerda agregar aquí el bloque de: if Vacacion.objects.filter(...): continue

                # 4. Configuración de Horas
                # Si no tiene hora definida, asumimos 9:00 AM por defecto
                hora_entrada_user = perfil.hora_entrada if perfil.hora_entrada else dt_module.time(9, 0)
                jornada_horas = perfil.jornada_diaria if perfil.jornada_diaria else 9

                # 5. Construir la fecha/hora de entrada teórica
                entrada_naive = datetime.combine(hoy, hora_entrada_user)

                entrada_oficial = timezone.make_aware(entrada_naive)

                # Tolerancia de 45 minutos antes de acusarlo
                limite_ausencia = entrada_oficial + timedelta(minutes=45)

                # ====================================================
                # ALERTA 1: AUSENCIA (No ha llegado)
                # ====================================================
                # Solo revisamos si YA pasó la hora límite
                if ahora > limite_ausencia:
                    tiene_marca = Marcacion.objects.filter(trabajador=user, timestamp__date=hoy, tipo='ENTRADA').exists()

                    if not tiene_marca:
                        # Verificar si ya enviamos correo hoy para no spammear
                        ya_avisado = LogAlerta.objects.filter(trabajador=user, fecha=hoy, tipo='AUSENCIA').exists()

                        if not ya_avisado:
                            asunto = f"⚠️ ALERTA AUSENCIA: {user.get_full_name()}"
                            mensaje = (
                                f"Empresa: {nombre_empresa}\n"
                                f"Trabajador: {user.get_full_name()} (RUT: {perfil.rut or 'S/I'})\n\n"
                                f"Estado: NO HA MARCADO ENTRADA.\n"
                                f"Hora entrada pactada: {hora_entrada_user}\n"
                                f"Hora actual revisión: {ahora.strftime('%H:%M')}\n\n"
                                f"El sistema ha verificado y no existe registro de entrada."
                            )

                            send_mail(asunto, mensaje, remitente, [email_rrhh], fail_silently=True)

                            # Guardar registro para no volver a enviar hoy
                            LogAlerta.objects.create(trabajador=user, fecha=hoy, tipo='AUSENCIA')
                            self.stdout.write(self.style.WARNING(f" > ✉️  Aviso Ausencia enviado: {user.username}"))

                # ====================================================
                # ALERTA 2: EXCESO DE HORAS (Fatiga laboral)
                # ====================================================
                ultima_marca = Marcacion.objects.filter(trabajador=user, timestamp__date=hoy).order_by('-timestamp').first()

                esta_de_vacaciones = Vacacion.objects.filter(
                    trabajador=user, estado='APROBADA',inicio__lte=hoy, fin__gte=hoy
                ).exists()

                # B. Chequeo de Licencias (NUEVO)
                tiene_licencia = LicenciaMedica.objects.filter(
                    trabajador=user, inicio__lte=hoy, fin__gte=hoy
                ).exists()

                # Si cualquiera de las dos es verdad, saltamos al siguiente trabajador
                if esta_de_vacaciones or tiene_licencia:
                    # self.stdout.write(f" - {user.username} justificado (Vac/Lic).")
                    continue

                # Solo nos preocupa si la persona sigue marcada como "DENTRO" (Entrada o volvio de colación)
                # Si su última marca fue SALIDA, ya se fue, no hay problema.
                if ultima_marca and ultima_marca.tipo in ['ENTRADA', 'FIN_COLACION']:

                    primera_entrada = Marcacion.objects.filter(trabajador=user, timestamp__date=hoy, tipo='ENTRADA').order_by('timestamp').first()

                    if primera_entrada:
                        tiempo_transcurrido = ahora - primera_entrada.timestamp
                        horas_trabajadas = tiempo_transcurrido.total_seconds() / 3600

                        # Alerta si se pasa por 2 horas de su jornada
                        limite_fatiga = jornada_horas + 2

                        if horas_trabajadas > limite_fatiga:
                            ya_avisado = LogAlerta.objects.filter(trabajador=user, fecha=hoy, tipo='EXCESO_HORAS').exists()

                            if not ya_avisado:
                                asunto = f"🚨 URGENTE EXCESO: {user.get_full_name()}"
                                mensaje = (
                                    f"Empresa: {nombre_empresa}\n"
                                    f"Trabajador: {user.get_full_name()}\n\n"
                                    f"⚠️ ALERTA DE FATIGA / EXCESO DE JORNADA\n"
                                    f"Lleva {int(horas_trabajadas)} horas trabajando continuas.\n"
                                    f"Jornada pactada: {jornada_horas} hrs.\n"
                                    f"Favor contactar al trabajador para verificar su salida."
                                )

                                send_mail(asunto, mensaje, remitente, [email_rrhh], fail_silently=True)

                                LogAlerta.objects.create(trabajador=user, fecha=hoy, tipo='EXCESO_HORAS')
                                self.stdout.write(self.style.ERROR(f" > ✉️  Aviso Exceso enviado: {user.username}"))

        self.stdout.write(self.style.SUCCESS("✅ Revisión completada."))