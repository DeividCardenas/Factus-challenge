# ⚡ INICIAR EN 5 MINUTOS

## 1️⃣ Instalar dependencias (1 min)

```bash
cd c:\Users\Dillan\Music\factus-challenge
pip install -r requirements.txt
```

## 2️⃣ Verificar base de datos (1 min)

```bash
# PostgreSQL debe estar corriendo
# Si usas Docker:
docker-compose up -d postgres redis

# O verifica que PostgreSQL esté en localhost:5432
psql -U postgres -c "SELECT version();"
```

## 3️⃣ Iniciar servidor (1 min)

```bash
uvicorn app.main:app --reload
```

## 4️⃣ Abrir interfaz (1 min)

- **REST API Docs:** http://localhost:8000/docs
- **GraphQL Sandbox:** http://localhost:8000/graphql
- **Health Check:** http://localhost:8000/health

## 5️⃣ Haz tu primer request (1 min)

### Opción A: REST API (en Swagger)

1. Click en **POST /api/v1/auth/login** en http://localhost:8000/docs
2. Click **Try it out**
3. Pega esto en el JSON:
```json
{
  "username": "admin@example.com",
  "password": "admin123"
}
```
4. Click **Execute**

### Opción B: GraphQL (en Sandbox)

Ve a http://localhost:8000/graphql y pega esto:

```graphql
query {
  invoices(pagination: {skip: 0, limit: 5}) {
    items {
      id
      referenceCode
      total
      estado
    }
    total
    pages
  }
}
```

---

## 📚 Documentación Rápida

| Necesitas | Archivo | Tiempo |
|-----------|---------|--------|
| Entender arquitectura | docs/ARQUITECTURA_IMPLEMENTADA.md | 15 min |
| Validar todo está bien | docs/VALIDACION_ARQUITECTURA.md | 10 min |
| Ver cambios hechos | docs/RESUMEN_MEJORAS.md | 5 min |
| Encontrar un archivo | docs/MAPA_UBICACIONES.md | 2 min |
| Quick start | README.md | 5 min |

---

## 🔧 Comandos Útiles

```bash
# Iniciar servidor en otra terminal
uvicorn app.main:app --reload

# Verificar que compila
python -c "from app.main import app; print('✓')"

# Ver configuración actual
python -c "from app.core.config import settings; print(settings)"

# Ejecutar tests (cuando existan)
pytest tests/

# Con cobertura
pytest --cov=app tests/

# Ver logs en tiempo real
# En terminal: uvicorn app.main:app --reload --log-level debug
```

---

## ⚠️ Si something falla

```bash
# 1. ¿PostgreSQL no conecta?
# Verifica: DATABASE_URL en .env
database_url=postgresql+asyncpg://factus_user:factus_password@localhost:5432/factus_db

# 2. ¿Tablas no existen?
# Python crea auto al iniciar - revisa logs

# 3. ¿Port 8000 ocupado?
uvicorn app.main:app --port 8001

# 4. ¿Otro error?
# Sube log completo y revisa docs/
```

---

## 🎯 Próximas mejoras (cuando tengas tiempo)

- [ ] Crear tests unitarios (2-3 horas)
- [ ] Rate limiting + Redis caché (1 día)
- [ ] Monitoring Prometheus (1 día)
- [ ] CI/CD pipeline (2 horas)
- [ ] Deploy Docker (2 horas)

---

**¡Listo! Tu proyecto está en el aire!** 🚀

Para más detalles, lee los .md en `/docs/`
