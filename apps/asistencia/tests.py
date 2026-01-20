from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Marcacion, Perfil

class CalculoJornadaTests(TestCase):

    def setUp(self):
        """Configuración inicial antes de cada prueba"""
        self.user = User.objects.create_user(username='tester', password='123')

        Perfil.objects.get_or_create(
            usuario=self.user,
            defaults={
                'rut': '11111111-1',
                'cargo': 'QA Tester',
                'rol': 'TRABAJADOR'
            }
        )

    def test_calculo_exacto_jornada(self):
        """Prueba que el cálculo entre Entrada y Salida sea correcto"""
        ahora = timezone.now().replace(hour=8, minute=0, second=0, microsecond=0)

        entrada = Marcacion.objects.create(
            trabajador=self.user,
            tipo='ENTRADA',
            timestamp=ahora,
            latitud=0, longitud=0 # Dato obligatorio
        )

        salida = Marcacion.objects.create(
            trabajador=self.user,
            tipo='SALIDA',
            timestamp=ahora + timedelta(hours=10),
            latitud=0, longitud=0 # Dato obligatorio
        )

        diferencia = salida.timestamp - entrada.timestamp
        horas_trabajadas = diferencia.total_seconds() / 3600

        print(f"\n🧪 TEST CÁLCULO:")
        print(f"   Entrada: {entrada.timestamp.strftime('%H:%M')}")
        print(f"   Salida:  {salida.timestamp.strftime('%H:%M')}")
        print(f"   Duración: {horas_trabajadas}h")

        self.assertEqual(horas_trabajadas, 10.0)

    def test_hash_seguridad_generado(self):
        """Prueba que se genere el hash de blockchain al guardar"""
        marca = Marcacion.objects.create(
            trabajador=self.user,
            tipo='ENTRADA',
            timestamp=timezone.now(),
            latitud=0, longitud=0 # <-- AGREGADO: Dato obligatorio
        )

        print(f"\n🔒 TEST BLOCKCHAIN:")
        print(f"   Hash: {marca.hash_actual[:15]}...") # Mostramos solo el inicio

        self.assertTrue(marca.hash_actual)

    def test_viaje_en_el_tiempo(self):
        """
        PRUEBA DE QA: Integridad Cronológica.
        Verifica que el sistema LANCE UN ERROR si intentamos viajar en el tiempo.
        """
        print("\n⏳ EJECUTANDO TEST: Viaje en el Tiempo")

        ahora = timezone.now()

        # 1. Entrada normal
        Marcacion.objects.create(
            trabajador=self.user,
            tipo='ENTRADA',
            timestamp=ahora,
            latitud=0, longitud=0 # <-- AGREGADO
        )

        # 2. Salida en el pasado (Debe fallar)
        with self.assertRaises(ValidationError):
            Marcacion.objects.create(
                trabajador=self.user,
                tipo='SALIDA',
                timestamp=ahora - timedelta(hours=1),
                latitud=0, longitud=0 # <-- AGREGADO
            )

        print("   ✅ ÉXITO: El sistema bloqueó la inconsistencia temporal.")