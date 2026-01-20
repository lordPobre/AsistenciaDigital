import hashlib
import datetime
from cloudinary_storage.storage import MediaCloudinaryStorage
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

User = get_user_model()

class Marcacion(models.Model):
    TIPOS = [
        ('ENTRADA', 'Entrada'),
        ('INICIO_COLACION', 'Inicio Colación'),
        ('FIN_COLACION', 'Fin Colación'),
        ('SALIDA', 'Salida'),
    ]

    trabajador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=timezone.now, editable=False)
    tipo = models.CharField(max_length=20, choices=TIPOS, default='ENTRADA')
    foto = models.ImageField(
        upload_to='marcas/%Y/%m/', 
        null=True, 
        blank=True,
        storage=MediaCloudinaryStorage()  # <--- ESTO ES LA MAGIA
    )
    alerta_olvido_enviada = models.BooleanField(default=False)

    ESTADOS_MARCA = [
        ('VIGENTE', 'Vigente'),
        ('RECTIFICADA', 'Rectificada (Histórico)'),
        ('ANULADA', 'Anulada')
    ]
    estado = models.CharField(max_length=20, choices=ESTADOS_MARCA, default='VIGENTE')

    ANIMO_CHOICES = [
        ('FELIZ', 'Feliz'),
        ('NEUTRAL', 'Neutral'),
        ('MOLESTO', 'Molesto/Triste'),
    ]
    animo = models.CharField(max_length=10, choices=ANIMO_CHOICES, null=True, blank=True)
    comentario_animo = models.TextField(null=True, blank=True, verbose_name="¿Por qué te sientes así?")

    # Para saber si esta marca corrige a otra anterior (ID 2 referencia a ID 1)
    marca_reemplazada = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='reemplazo')

    # Para saber si fue creada por sistema o manualmente por admin
    es_manual = models.BooleanField(default=False)
    observacion = models.TextField(blank=True, null=True)

    # Datos de Geolocalización y Red
    latitud = models.DecimalField(max_digits=10, decimal_places=7, null=True)
    longitud = models.DecimalField(max_digits=10, decimal_places=7, null=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    direccion = models.CharField(max_length=255, blank=True, null=True, help_text="Dirección obtenida vía GPS")

    # Seguridad (Cadena de Bloques / Inviolabilidad)
    hash_previo = models.CharField(max_length=64, blank=True)
    hash_actual = models.CharField(max_length=64, blank=True, editable=False)

    def calcular_hash(self):
        """Genera firma SHA-256 única encadenada al registro anterior"""
        # Buscamos la última marca de ESTE trabajador
        ultima = Marcacion.objects.filter(trabajador=self.trabajador).order_by('-timestamp').first()
        prev = ultima.hash_actual if ultima else "GENESIS_BLOCK"

        self.hash_previo = prev
        # String único: ID_Usuario + Fecha + Tipo + HashAnterior
        raw_data = f"{self.trabajador.id}{self.timestamp}{self.tipo}{prev}"
        return hashlib.sha256(raw_data.encode('utf-8')).hexdigest()

    def clean(self):
        """Validador lógico para impedir inconsistencias"""
        super().clean()

        # Validación: La Salida no puede ser anterior a la última Entrada
        if self.tipo == 'SALIDA':
            # Buscamos la última entrada de este trabajador
            ultima_entrada = Marcacion.objects.filter(
                trabajador=self.trabajador,
                tipo='ENTRADA'
            ).exclude(pk=self.pk).order_by('-timestamp').first()

            if ultima_entrada:
                # Si la marca que intentamos guardar es ANTERIOR a la entrada...
                if self.timestamp < ultima_entrada.timestamp:
                    raise ValidationError(f"Error Cronológico: No puedes marcar SALIDA ({self.timestamp.strftime('%H:%M')}) antes de la ENTRADA ({ultima_entrada.timestamp.strftime('%H:%M')}).")

    def save(self, *args, **kwargs):
        # 1. ESTA ES LA LÍNEA MÁGICA QUE FALTABA:
        # Obliga a ejecutar el método clean() antes de escribir en la base de datos.
        self.full_clean()

        # 2. Generación del Hash (Blockchain)
        if not self.pk:
            self.hash_actual = self.calcular_hash()

        # 3. Guardado real
        super(Marcacion, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.trabajador} - {self.tipo} ({self.timestamp})"

class SolicitudMarca(models.Model):
    TIPOS_SOLICITUD = [
        ('NUEVA', 'Nueva Marca (Falla Técnica)'),
        ('RECTIFICACION', 'Corregir Marca Existente'),
    ]
    ESTADOS_SOLICITUD = [
        ('PENDIENTE', 'Pendiente de Aprobación'),
        ('ACEPTADA', 'Aceptada por Trabajador'),
        ('RECHAZADA', 'Rechazada por Trabajador'),
    ]

    trabajador = models.ForeignKey(User, on_delete=models.CASCADE, related_name='solicitudes_recibidas')
    solicitante = models.ForeignKey(User, on_delete=models.PROTECT, related_name='solicitudes_creadas') # El Admin

    tipo_solicitud = models.CharField(max_length=20, choices=TIPOS_SOLICITUD)
    estado = models.CharField(max_length=20, choices=ESTADOS_SOLICITUD, default='PENDIENTE')

    # Datos propuestos
    fecha_hora_propuesta = models.DateTimeField()
    tipo_marca_propuesta = models.CharField(max_length=20) # ENTRADA, SALIDA...
    motivo = models.TextField(help_text="Motivo de la falla o error")

    # Si es rectificación, apuntamos a la marca original que se quiere cambiar
    marca_original = models.ForeignKey(Marcacion, on_delete=models.SET_NULL, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Solicitud {self.tipo_solicitud} para {self.trabajador}"

class Empresa(models.Model):
    nombre = models.CharField(max_length=100)
    email_rrhh = models.EmailField(verbose_name="Correo RRHH para Notificaciones")
    rut = models.CharField(
        max_length=12,
        verbose_name="RUT Empresa",
        help_text="Ej: 76.123.456-K",
        null=True,
        blank=True
    )

    direccion = models.CharField(
        max_length=255,
        verbose_name="Dirección Comercial",
        null=True,
        blank=True
    )

    razon_social = models.CharField(
        max_length=200,
        verbose_name="Razón Social (Legal)",
        help_text="Nombre legal ante el SII",
        null=True,
        blank=True
    )
    logo = models.ImageField(upload_to='logos_empresas/', null=True, blank=True, verbose_name="Logo de la Empresa")

    def __str__(self):
        return self.nombre

class Perfil(models.Model):
    ROLES = (
        ('TRABAJADOR', 'Trabajador'),
        ('EMPLEADOR', 'Empleador / RRHH'),
        ('FISCALIZADOR', 'Fiscalizador DT'),
    )

    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, null=True, blank=True)
    rut = models.CharField(max_length=12, blank=True, null=True)
    cargo = models.CharField(max_length=100)
    rol = models.CharField(max_length=20, choices=ROLES, default='TRABAJADOR')
    trabaja_lunes = models.BooleanField(default=True, verbose_name="Lunes")
    trabaja_martes = models.BooleanField(default=True, verbose_name="Martes")
    trabaja_miercoles = models.BooleanField(default=True, verbose_name="Miércoles")
    trabaja_jueves = models.BooleanField(default=True, verbose_name="Jueves")
    trabaja_viernes = models.BooleanField(default=True, verbose_name="Viernes")
    trabaja_sabado = models.BooleanField(default=False, verbose_name="Sábado")
    trabaja_domingo = models.BooleanField(default=False, verbose_name="Domingo")

    def debe_trabajar_hoy(self):
        """Devuelve True si al usuario le toca trabajar hoy según su configuración"""
        from django.utils import timezone
        dia_semana = timezone.localdate().weekday() # 0=Lunes, 6=Domingo

        mapa_dias = {
            0: self.trabaja_lunes,
            1: self.trabaja_martes,
            2: self.trabaja_miercoles,
            3: self.trabaja_jueves,
            4: self.trabaja_viernes,
            5: self.trabaja_sabado,
            6: self.trabaja_domingo,
        }
        return mapa_dias.get(dia_semana, False)

    # --- AGREGA ESTE CAMPO NUEVO ---
    cambiar_pass_inicial = models.BooleanField(default=True, verbose_name="Debe cambiar contraseña")
    jornada_diaria = models.IntegerField(
        default=9,
        verbose_name="Horas Jornada Diaria",
        help_text="Ej: 9 para jornada de 45 horas semanales."
    )
    hora_entrada = models.TimeField(
        default=datetime.time(9, 0),
        verbose_name="Hora Entrada Oficial",
        help_text="Hora límite antes de contar atraso."
    )

    def __str__(self):
        return f"Perfil de {self.usuario.username}"

# --- AGREGA ESTO AL FINAL DEL ARCHIVO ---

@receiver(post_save, sender=User)
def crear_o_actualizar_perfil(sender, instance, created, **kwargs):
    """
    Gestiona la creación del perfil de forma segura.
    """
    if created:
        # get_or_create es la clave: Si ya existe, lo trae. Si no, lo crea.
        # Esto evita el choque con el Admin.
        Perfil.objects.get_or_create(usuario=instance)

    # Solo intentamos guardar si el perfil existe, para evitar errores raros
    if hasattr(instance, 'perfil'):
        instance.perfil.save()

class LogAlerta(models.Model):
    TIPOS = [
        ('AUSENCIA', 'Ausencia Laboral'),
        ('EXCESO_HORAS', 'Exceso de Horas Extras (+2h)'),
    ]
    trabajador = models.ForeignKey(User, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=20, choices=TIPOS)
    fecha = models.DateField(auto_now_add=True) # Fecha de hoy
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.trabajador} - {self.tipo} - {self.fecha}"

class Feriado(models.Model):
    fecha = models.DateField(unique=True, verbose_name="Fecha del Feriado")
    descripcion = models.CharField(max_length=100, verbose_name="Nombre (ej: Navidad)")

    def __str__(self):
        return f"{self.fecha} - {self.descripcion}"

    class Meta:
        verbose_name = "Feriado"
        verbose_name_plural = "Feriados y Festivos"
        ordering = ['-fecha']

class Vacacion(models.Model):
    ESTADOS = [
        ('PENDIENTE', 'Solicitud Pendiente'),
        ('APROBADA', 'Aprobada'),
        ('RECHAZADA', 'Rechazada'),
    ]

    trabajador = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vacaciones')
    inicio = models.DateField(verbose_name="Fecha Inicio")
    fin = models.DateField(verbose_name="Fecha Fin")
    comentario = models.CharField(max_length=200, blank=True, null=True)
    # --- CAMPO NUEVO QUE FALTABA ---
    estado = models.CharField(max_length=15, choices=ESTADOS, default='PENDIENTE')
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    # -------------------------------

    def __str__(self):
        return f"{self.trabajador.username} ({self.inicio} al {self.fin})"

    class Meta:
        verbose_name = "Vacación"
        verbose_name_plural = "Vacaciones"

class LicenciaMedica(models.Model):
    TIPOS = [
        ('ENFERMEDAD', 'Enfermedad Común'),
        ('ACCIDENTE', 'Accidente Laboral'),
        ('MATERNAL', 'Pre/Post Natal'),
        ('OTRO', 'Otro Motivo'),
    ]

    trabajador = models.ForeignKey(User, on_delete=models.CASCADE, related_name='licencias')
    inicio = models.DateField(verbose_name="Fecha Inicio")
    fin = models.DateField(verbose_name="Fecha Fin")
    tipo = models.CharField(max_length=20, choices=TIPOS, default='ENFERMEDAD')
    documento = models.FileField(upload_to='licencias/', blank=True, null=True, verbose_name="Certificado PDF")

    def __str__(self):
        return f"Licencia {self.trabajador.username} ({self.inicio} al {self.fin})"

class DiaAdministrativo(models.Model):
    ESTADOS = [
        ('PENDIENTE', 'Solicitud Pendiente'),
        ('APROBADO', 'Aprobado'),
        ('RECHAZADO', 'Rechazado'),
    ]

    TIPO_JORNADA = [
        ('COMPLETO', 'Día Completo'),
        ('MAÑANA', 'Media Jornada (Mañana)'),
        ('TARDE', 'Media Jornada (Tarde)'),
    ]

    trabajador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='dias_administrativos')
    fecha = models.DateField(verbose_name="Fecha Solicitada")
    tipo_jornada = models.CharField(max_length=10, choices=TIPO_JORNADA, default='COMPLETO')
    motivo = models.TextField(blank=True, null=True, help_text="Opcional: Trámites, personal, etc.")

    estado = models.CharField(max_length=15, choices=ESTADOS, default='PENDIENTE')
    fecha_solicitud = models.DateTimeField(auto_now_add=True)

    # Respuesta de RRHH
    comentario_rrhh = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return f"{self.trabajador} - {self.fecha} ({self.estado})"

    class Meta:
        ordering = ['-fecha']