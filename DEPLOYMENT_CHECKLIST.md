# CHECKLIST DE DESPLIEGUE - SSEMI en Render + Railway

## Estado actual
- ✅ Panel admin cargando correctamente
- ⚠️ Panel instructor corregido (agregados scripts config.js + api.js)
- ⚠️ Email en background pero no se entrega (SMTP bloqueado por red en Render)
- ✅ Login y 2FA funcionando (sin bloqueos)
- ✅ Bitácora funcionando

## Pasos para Render - COMPLETAR AHORA

### 1. Variables de entorno requeridas
En Render dashboard → Service → Environment, asegúrate que estos existan (copia exacta):

```
DATABASE_URL = mysql://usuario:password@nozomi.proxy.rlwy.net:40321/railway
SECRET_KEY = tu_clave_secreta_segura
EMAIL_USER = ssemicompany@gmail.com
EMAIL_PASSWORD = xdmr pgni xeif foxw
SMTP_HOST = smtp.gmail.com
SMTP_PORT = 587
SMTP_TIMEOUT = 10
```

**IMPORTANTE**: `EMAIL_PASSWORD` debe SER exactamente tu App Password de Gmail (sin espacios).
Si lo pegaste con espacios, elimínalos y guarda.

### 2. Si SMTP sigue fallando (Red inalcanzable)
Reemplaza las últimas 3 líneas SMTP por SendGrid:

**Opción A (RECOMENDADA - SendGrid)**
```
SENDGRID_API_KEY = SG.tu_api_key_aqui
```
- El backend automáticamente usará SendGrid como fallback si SMTP falla.
- Crear API Key gratis en: https://sendgrid.com (crear cuenta, ir a Settings > API Keys > Create API Key).

**Opción B (Si quieres usar Gmail pero SMTP está bloqueado)**
- Contactar a Render support para saber si puerto 587 está permitido.
- O usar SMTP diferente (ej. Office 365 si tienes).

### 3. Redeploy después de agregar variables
- Render Dashboard → Service → Manual Deploy → Redeploy latest commit
- O ir a Overview y presionar Restart

### 4. Verificar después del redeploy
```bash
# Test login
curl -X POST https://ssemi.onrender.com/login \
  -H "Content-Type: application/json" \
  -d '{"correo":"tu@correo.com","contraseña":"tu_pass"}'

# Esperado: 200 OK con {"mensaje":"Código de verificación enviado correctamente"}
# Si 503: email aún no configurado

# Debería llegar email con código 2FA
# Luego: POST /2fa/verify con el código
```

## Cambios realizados en este commit

### Backend
- ✅ `Backend/app/auth/email_utils.py`: Añadido SMTP_TIMEOUT, fallback SendGrid, manejo correcto de excepciones.
- ✅ `Backend/app/auth/routes.py`: `/login` y `/password/forgot` ahora usan BackgroundTasks (no bloquean).
- ✅ `Backend/app/comite_nacional/routes.py`: Activar/desactivar evaluadores ahora en background.
- ✅ `Backend/app/database.py`: Fallback `MYSQL_URL` → `DATABASE_URL` si no existe.

### Frontend
- ✅ `frontend/static/config.js`: Creado con API_URL.
- ✅ `frontend/static/api.js`: Limpiado, incluye Authorization header automaticamente.
- ✅ `frontend/templates/admin.html`: Apunta a `/static/config.js` (no `/js/config.js`).
- ✅ `frontend/templates/evaluador.html`: Apunta a `/static/config.js`.
- ✅ `frontend/templates/instructor.html`: Agregados scripts config.js + api.js al final.

## Testing local antes de producción

### 1. Activar el servidor local
```powershell
$env:DATABASE_URL="mysql://root:TU_PASSWORD@localhost:3306/ssemi"
$env:SECRET_KEY="test_key_segura"
$env:EMAIL_USER="ssemicompany@gmail.com"
$env:EMAIL_PASSWORD="xdmr pgni xeif foxw"
uvicorn Backend.app.main:app --reload --host 0.0.0.0 --port 10000
```

### 2. Pruebas rápidas
```bash
# Login
curl -X POST http://localhost:10000/login \
  -H "Content-Type: application/json" \
  -d '{"correo":"admin@test.com","contraseña":"admin123"}'

# 2FA verify (usa el código de la respuesta anterior)
curl -X POST http://localhost:10000/2fa/verify \
  -H "Content-Type: application/json" \
  -d '{"correo":"admin@test.com","codigo":"123456"}'

# Recuperación de contraseña (background task - verifica logs)
curl -X POST http://localhost:10000/password/forgot \
  -H "Content-Type: application/json" \
  -d '{"correo":"admin@test.com"}'
```

### 3. Ver logs de envío de email
- Los logs deberían mostrar `✅ Correo enviado correctamente` o `❌ Error al enviar correo vía SMTP: ...` seguido de `✅ Correo enviado vía SendGrid correctamente`.

## Troubleshooting

### Error: "Network is unreachable" al enviar email
**Causa**: Render no puede conectar a smtp.gmail.com:587.
**Solución**: Usar SendGrid (agregar `SENDGRID_API_KEY`).

### Error: "401 Unauthorized" en admin endpoints
**Causa**: Token no enviado o `config.js` no cargado.
**Solución**: 
- Verificar DevTools → Network → XHR → Headers incluyen `Authorization: Bearer ...`
- Verificar que `/static/config.js` carga sin 404.

### Instructor panel no carga datos
**Causa**: `config.js` + `api.js` no cargaban.
**Solución**: Ya arreglado en este commit. Redeploy.

### Email no se entrega pero backend no da error
**Causa**: Email está en background pero falla silenciosamente.
**Solución**: Ver logs de Render para mensajes de error de SMTP/SendGrid.

## Commit recomendado
```bash
git add -A
git commit -m "Fix: Backend email background tasks, frontend scripts loading, Render compatibility

- Add SMTP_TIMEOUT and SendGrid fallback to email_utils
- Move send_email to BackgroundTasks in login, password recovery, comite_nacional
- Fix frontend: instructor.html loads config.js + api.js
- Create frontend/static/config.js for static serving
- Update admin + evaluador templates to use /static/config.js
- Add DATABASE_URL/MYSQL_URL fallback in database.py
- Tested: admin panel loads, 401s fixed, instructor panel loads"
git push
```

## Próximas mejoras (no urgentes)
- [ ] Implementar migraciones con Alembic (reemplazar create_all())
- [ ] Webhook para recordatorios en lugar de APScheduler
- [ ] Logs estructurados con request IDs
- [ ] Monitoring de delivery de emails
