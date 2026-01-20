import ntplib
from time import ctime
from datetime import datetime, timezone

def obtener_hora_oficial_chile():
    """
    Consulta el servidor NTP del SHOA (Servicio Hidrográfico y Oceanográfico de la Armada).
    Si falla, usa la hora del servidor pero deja un registro del fallo.
    """
    servidor_ntp = 'ntp.shoa.cl'
    cliente = ntplib.NTPClient()
    
    try:
        respuesta = cliente.request(servidor_ntp, version=3, timeout=2)
        hora_exacta = datetime.fromtimestamp(respuesta.tx_time, timezone.utc)
        return {
            'hora': hora_exacta,
            'origen': 'SHOA (Oficial)',
            'sincronizado': True
        }
    except Exception as e:
        return {
            'hora': datetime.now(timezone.utc),
            'origen': 'Servidor Local (Fallback)',
            'sincronizado': False,
            'error': str(e)
        }