from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Trabajador

#class TrabajadorAdmin(UserAdmin):
    #model = Trabajador
    
    # 1. Qué campos mostrar en la lista de usuarios (columnas)
    #list_display = ['username', 'first_name', 'last_name', 'rut', 'cargo', 'is_active']
    
    # 2. Qué campos mostrar en el formulario de edición
    # (Agregamos 'rut' y 'cargo' a la sección de datos personales)
    #fieldsets = UserAdmin.fieldsets + (
        #('Datos Laborales', {'fields': ('rut', 'cargo')}),
    #)
    
    # 3. Qué campos permitir al CREAR un usuario nuevo
    #add_fieldsets = UserAdmin.add_fieldsets + (
       # (None, {'fields': ('rut', 'cargo')}),
    #)

#admin.site.register(Trabajador, TrabajadorAdmin)