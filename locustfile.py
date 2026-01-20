from locust import HttpUser, task, between

class UsuarioAsistencia(HttpUser):
    # Tiempo de espera aleatorio entre tareas (simula pensamiento humano)
    # El usuario espera entre 1 y 5 segundos antes de hacer otra cosa.
    wait_time = between(1, 5)

    def on_start(self):
        """
        Esto se ejecuta UNA vez cuando el usuario virtual "nace".
        Lo usamos para iniciar sesión.
        """
        # 1. Entramos al login para obtener la cookie CSRF
        response = self.client.get("/accounts/login/") 
        # NOTA: Ajusta '/accounts/login/' si tu URL de login es distinta (ej: '/login/')
        
        if 'csrftoken' in response.cookies:
            csrftoken = response.cookies['csrftoken']
        else:
            print("Error: No se encontró cookie CSRF")
            return

        # 2. Hacemos el POST para loguearnos
        # CAMBIA ESTO por un usuario y contraseña real de tu sistema
        self.client.post("/accounts/login/", {
            "username": "tu_usuario_prueba",  # <--- PON AQUÍ UN USUARIO REAL
            "password": "tu_password_prueba"  # <--- PON AQUÍ LA CONTRASEÑA
        }, headers={"X-CSRFToken": csrftoken})

    @task(3)
    def ver_dashboard(self):
        """
        Tarea frecuente: El usuario entra al dashboard a mirar la hora.
        El (3) significa que es 3 veces más probable que ocurra que las tareas de peso (1).
        """
        self.client.get("/")

    @task(1)
    def marcar_asistencia(self):
        """
        Tarea crítica: El usuario marca asistencia.
        Simulamos los datos que envía el JavaScript (GPS + Foto).
        """
        # Necesitamos el token CSRF nuevamente para este POST
        csrftoken = self.client.cookies.get('csrftoken')
        
        if not csrftoken:
            return

        # Datos simulados (GPS falso y una imagen base64 vacía o pequeña)
        datos = {
            "latitud": "-33.4489",
            "longitud": "-70.6693",
            "tipo": "ENTRADA", # Puedes variar esto si quieres
            "foto_base64": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=", # Un punto transparente
            "animo": "FELIZ" # Por si toca salida
        }

        # Enviamos la marca al endpoint que creaste
        self.client.post("/marcar/", datos, headers={"X-CSRFToken": csrftoken})

    @task(1)
    def ver_mis_vacaciones(self):
        """
        El usuario revisa sus vacaciones
        """
        self.client.get("/mis-vacaciones/")