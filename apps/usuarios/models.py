from django.contrib.auth.models import AbstractUser
from django.db import models

class Trabajador(AbstractUser):
    #El RUT es obligatorio para la DT
    rut = models.CharField(max_length=12, unique=True, help_text="Ej: 12.345.678-9")
    cargo = models.CharField(max_length=100, blank=True, null=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.rut})"