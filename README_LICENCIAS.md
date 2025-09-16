# 🔐 Sistema de Licencias - Dashboard CCU

## Descripción General

El Dashboard CCU ahora incluye un sistema de licencias que verifica la validez de cada usuario antes de permitir el acceso a la aplicación. Cada vez que se ejecuta el programa, se conecta automáticamente a la nube para verificar que el código de licencia esté **ACTIVO**.

## 🚀 Funcionamiento

### Al Iniciar la Aplicación
1. **Verificación Automática**: El sistema busca si hay un código de licencia guardado localmente
2. **Conexión a la Nube**: SIEMPRE se conecta al servidor para verificar en tiempo real si la licencia está ACTIVA
3. **Control de Acceso**: 
   - ✅ **Licencia ACTIVA en la nube**: Permite el acceso completo al dashboard
   - ❌ **Licencia INACTIVA en la nube**: Bloquea el acceso y muestra mensaje de error

**IMPORTANTE**: El código se guarda localmente para comodidad, pero el estado ACTIVO/INACTIVO se verifica SIEMPRE contra la nube en cada ejecución.

### Primera Vez / Sin Licencia
Si no hay licencia configurada o está inactiva, aparecerá una interfaz para:
- Ingresar el código de licencia
- Verificar y guardar la licencia
- Cambiar licencia existente

## 📋 Formato de Códigos de Licencia

Los códigos de licencia tienen el formato: `XXXX-XXXX-XXXX-XXXX`

**Ejemplo**: `XBDC-0696-5689-54CD`

## 🛠️ Gestión de Licencias

### Para Administradores

#### Generar Nueva Licencia
```bash
python generate_license.py
```

El script permite:
1. **Crear nueva licencia** - Genera código único automáticamente
2. **Listar licencias** - Ver todas las licencias existentes
3. **Cambiar estado** - Activar/desactivar licencias
4. **Salir** - Terminar el programa

#### Estructura del Archivo de Licencias (`Licencias.txt`)
```json
{
  "Licencias": [
    {
      "Codigo": "XBDC-0696-5689-54CD",
      "Activo": true,
      "Creada": "2025-01-15 10:30:00",
      "Descripcion": "Cliente principal"
    }
  ]
}
```

### Para Usuarios

#### Configurar Licencia por Primera Vez
1. Ejecutar `streamlit run app.py`
2. Ingresar el código de licencia proporcionado
3. Hacer clic en "✅ Verificar y Guardar Licencia"
4. El sistema guardará la licencia localmente para futuros usos

#### Cambiar Licencia
1. En la pantalla de licencias, hacer clic en "🔄 Cambiar Licencia"
2. Ingresar el nuevo código de licencia
3. Verificar y guardar

## 🔧 Configuración Técnica

### Archivos del Sistema
- `utils/license_manager.py` - Módulo principal de gestión de licencias
- `generate_license.py` - Script para crear y gestionar licencias
- `Licencias.txt` - Archivo en la nube con todas las licencias
- `license_config.json` - Configuración local del usuario (se crea automáticamente)

### URL de Licencias en la Nube
```
https://raw.githubusercontent.com/NahuelDumo/Dashboard-en-excel-AUTOMATIZADO/refs/heads/main/Licencias.txt
```

### Dependencias Agregadas
- `requests>=2.31.0` - Para conexiones HTTP a la nube

## 🚨 Mensajes de Error Comunes

### "LICENCIA INACTIVA"
- **Causa**: La licencia existe pero está desactivada en el servidor
- **Solución**: Contactar al administrador para activar la licencia

### "Código de licencia no encontrado"
- **Causa**: El código ingresado no existe en el sistema
- **Solución**: Verificar el código o solicitar una licencia válida

### "No se pudo conectar al servidor de licencias"
- **Causa**: Problemas de conectividad a internet
- **Solución**: Verificar conexión a internet y reintentar

## 📞 Soporte

Para obtener una licencia o resolver problemas:
1. Contactar al administrador del sistema
2. Proporcionar información sobre el uso previsto
3. Recibir código de licencia válido

## 🔒 Seguridad

- Las licencias se verifican en tiempo real contra el servidor
- No es posible usar licencias offline o modificadas
- Cada código es único e irrepetible
- El sistema registra intentos de acceso no autorizados

---

**Nota**: Este sistema garantiza que solo usuarios autorizados puedan acceder al Dashboard CCU, manteniendo la seguridad y control de acceso necesarios.
