from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model
from .models import Marcacion, Empresa, Perfil, SolicitudMarca, Feriado, Vacacion

User = get_user_model()

# --- 1. CONFIGURACIÓN DE EMPRESA ---

@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'cargo', 'trabaja_sabado')
    fieldsets = (
        (None, {'fields': ('usuario', 'rut', 'cargo', 'empresa')}),
        ('Jornada Laboral', {
            'fields': (
                ('trabaja_lunes', 'trabaja_martes', 'trabaja_miercoles'),
                ('trabaja_jueves', 'trabaja_viernes'),
                ('trabaja_sabado', 'trabaja_domingo')
            )
        }),
    )

@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'rut', 'direccion', 'tiene_logo')
    search_fields = ('nombre', 'rut')
    # Esto asegura que aparezca el campo para subir la imagen
    fields = ('nombre', 'rut', 'razon_social', 'direccion', 'email_rrhh', 'logo')

    def tiene_logo(self, obj):
        return "✅ Sí" if obj.logo else "❌ No"
    tiene_logo.short_description = "Logo Subido"

# --- 2. CONFIGURACIÓN DEL PERFIL (Inline) ---
class PerfilInline(admin.StackedInline):
    model = Perfil
    can_delete = False
    verbose_name_plural = 'Perfil del Trabajador (Empresa)'
    fk_name = 'usuario'

# --- 3. EXTENSIÓN DEL ADMIN DE USUARIOS ---
class UserAdmin(BaseUserAdmin):
    def get_inlines(self, request, obj=None):
        if not obj:
            return []
        return [PerfilInline]

# --- 4. RE-REGISTRO DEL USUARIO ---
if admin.site.is_registered(User):
    admin.site.unregister(User)

admin.site.register(User, UserAdmin)

# --- 5. CONFIGURACIÓN DE MARCACIÓN ---
class MarcacionAdmin(admin.ModelAdmin):
    list_display = ('trabajador', 'get_empresa', 'tipo', 'timestamp', 'latitud', 'longitud')
    list_filter = ('tipo', 'timestamp', 'trabajador__perfil__empresa')

    search_fields = (
        'trabajador__first_name',
        'trabajador__last_name',
        'trabajador__perfil__rut',
        'trabajador__perfil__empresa__nombre'
    )

    def get_empresa(self, obj):
        if hasattr(obj.trabajador, 'perfil') and obj.trabajador.perfil.empresa:
            return obj.trabajador.perfil.empresa.nombre
        return "Sin Empresa Asignada"

    get_empresa.short_description = 'Empresa'
    get_empresa.admin_order_field = 'trabajador__perfil__empresa'

admin.site.register(Marcacion, MarcacionAdmin)
admin.site.register(SolicitudMarca)

@admin.register(Feriado)
class FeriadoAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'descripcion', 'es_futuro')
    search_fields = ('descripcion',)

    def es_futuro(self, obj):
        from django.utils import timezone
        return obj.fecha >= timezone.localdate()
    es_futuro.boolean = True
    es_futuro.short_description = "¿Es futuro?"

@admin.register(Vacacion)
class VacacionAdmin(admin.ModelAdmin):
    list_display = ('trabajador', 'inicio', 'fin', 'dias_duracion')
    search_fields = ('trabajador__username', 'trabajador__first_name')
    list_filter = ('inicio',)

    def dias_duracion(self, obj):
        return (obj.fin - obj.inicio).days + 1
    dias_duracion.short_description = "Días"

