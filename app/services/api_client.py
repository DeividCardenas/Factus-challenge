import httpx
import asyncio
import random
from app.core.config import settings

class FactusService:
    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {settings.FACTUS_TOKEN}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        # Si settings.FACTUS_URL es vacía o localhost, no importa en modo TEST
        self.base_url = settings.FACTUS_URL 

    async def verificar_estado_api(self):
        # MOCK/SIMULACIÓN para estado
        if settings.APP_MODE == "TEST":
            return {"codigo": 200, "mensaje": "Modo Simulación Activo", "data": "OK"}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/v1/numbering-ranges", headers=self.headers)
                return {
                    "codigo": response.status_code,
                    "mensaje": "Conexión Exitosa",
                    "data": str(response.json())
                }
            except Exception as e:
                return {"codigo": 500, "mensaje": f"Error: {str(e)}", "data": ""}

    async def enviar_factura(self, factura_json: dict):
        ref_code = factura_json.get("reference_code", "N/A")

        # --- 🔴 CORTOCIRCUITO (MOCK) ---
        # Aquí está la clave: Si es TEST, retornamos INMEDIATAMENTE.
        # NO usamos httpx. NO intentamos conectar a localhost:5000.
        if settings.APP_MODE == "TEST":
            # 1. Simular pequeña espera (latencia de red)
            await asyncio.sleep(0.1)
            
            # 2. Imprimir en consola para que veas que pasó por aquí
            print(f"✅ [MOCK INTERNO] Factura {ref_code} simulada con éxito.")
            
            # 3. Retornar éxito falso
            return {
                "ref": ref_code,
                "status": 201, # Created
                "response": {
                    "message": "Bill validated successfully [SIMULATION]",
                    "data": {
                        "bill": {
                            "number": ref_code,
                            "qr": "qr-falso-simulado",
                            "cufe": "cufe-falso-simulado"
                        }
                    }
                }
            }
        
        # --- CÓDIGO REAL (Solo se ejecuta si NO es TEST) ---
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/v1/bills/validate",
                    json=factura_json,
                    headers=self.headers,
                    timeout=30.0
                )
                return {
                    "ref": ref_code,
                    "status": response.status_code,
                    "response": response.json() if response.status_code != 500 else response.text
                }
            except Exception as e:
                return {
                    "ref": ref_code,
                    "status": 0,
                    "error": str(e)
                }

factus_client = FactusService()