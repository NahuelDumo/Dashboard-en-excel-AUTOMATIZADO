import requests
import json
import os
from datetime import datetime
import streamlit as st

class LicenseManager:
    def __init__(self):
        self.license_url = "https://raw.githubusercontent.com/NahuelDumo/Dashboard-Automatizado-en-Python/refs/heads/main/Licencias.txt"
        self.license_file = "license_config.json"
        
    def save_license_locally(self, license_code):
        """Guarda el código de licencia localmente (solo el código, no el estado)"""
        license_data = {
            "license_code": license_code,
            "saved_date": datetime.now().isoformat()
        }
        with open(self.license_file, 'w') as f:
            json.dump(license_data, f)
    
    def load_local_license(self):
        """Carga el código de licencia guardado localmente"""
        if os.path.exists(self.license_file):
            try:
                with open(self.license_file, 'r') as f:
                    return json.load(f)
            except:
                return None
        return None
    
    def fetch_licenses_from_cloud(self):
        """Obtiene las licencias desde la nube"""
        try:
            response = requests.get(self.license_url, timeout=10)
            response.raise_for_status()
            
            # El archivo contiene un JSON con las licencias
            licenses_text = response.text.strip()
            
            # Parsear el JSON
            licenses_data = json.loads(licenses_text)
            return licenses_data.get("Licencias", [])
            
        except requests.exceptions.RequestException as e:
            st.error(f"❌ Error de conexión: No se pudo conectar al servidor de licencias. {str(e)}")
            return None
        except json.JSONDecodeError as e:
            st.error(f"❌ Error de formato: El archivo de licencias tiene un formato inválido. {str(e)}")
            return None
        except Exception as e:
            st.error(f"❌ Error inesperado al obtener licencias: {str(e)}")
            return None
    
    def verify_license(self, license_code):
        """Verifica si una licencia está activa"""
        licenses = self.fetch_licenses_from_cloud()
        
        if licenses is None:
            return False, "No se pudo conectar al servidor de licencias"
        
        # Buscar la licencia en la lista
        for license_item in licenses:
            if license_item.get("Codigo") == license_code:
                is_active = license_item.get("Activo", False)
                if is_active:
                    return True, "Licencia válida y activa"
                else:
                    return False, "Licencia inactiva"
        
        return False, "Código de licencia no encontrado"
    
    def check_license_status(self):
        """Verifica el estado de la licencia actual SIEMPRE contra la nube"""
        local_license = self.load_local_license()
        
        if not local_license:
            return False, "No hay licencia configurada"
        
        license_code = local_license.get("license_code")
        if not license_code:
            return False, "Código de licencia inválido"
        
        # SIEMPRE verificar con el servidor en tiempo real
        is_valid, message = self.verify_license(license_code)
        
        # NO actualizamos el estado local, solo verificamos contra la nube
        return is_valid, message
    
    def show_license_interface(self):
        """Muestra la interfaz para configurar la licencia"""
        st.markdown("# 🔐 Verificación de Licencia")
        st.markdown("---")
        
        # Verificar si ya hay una licencia configurada
        local_license = self.load_local_license()
        current_license = local_license.get("license_code", "") if local_license else ""
        
        if current_license:
            st.info(f"📋 Licencia actual: {current_license}")
            
            # Botón para verificar licencia actual
            if st.button("🔍 Verificar Licencia Actual", type="secondary"):
                with st.spinner("Verificando licencia..."):
                    is_valid, message = self.check_license_status()
                    if is_valid:
                        st.success(f"✅ {message}")
                        return True
                    else:
                        st.error(f"❌ {message}")
                        return False
        
        st.markdown("### Ingrese su código de licencia:")
        
        # Campo para ingresar nueva licencia
        new_license_code = st.text_input(
            "Código de Licencia:", 
            value="",
            placeholder="Ej: XBDC-0696-5689-54CD",
            help="Ingrese el código de licencia proporcionado"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ Verificar y Guardar Licencia", type="primary"):
                if new_license_code.strip():
                    with st.spinner("Verificando licencia..."):
                        is_valid, message = self.verify_license(new_license_code.strip())
                        
                        if is_valid:
                            self.save_license_locally(new_license_code.strip())
                            st.success(f"✅ {message}")
                            st.success("💾 Licencia guardada correctamente")
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")
                            return False
                else:
                    st.warning("⚠️ Por favor, ingrese un código de licencia")
                    return False
        
        with col2:
            if st.button("🔄 Cambiar Licencia", type="secondary"):
                if os.path.exists(self.license_file):
                    os.remove(self.license_file)
                st.info("🗑️ Licencia eliminada. Ingrese una nueva licencia.")
                st.rerun()
        
        return False
    
    def require_valid_license(self):
        """Función principal que requiere una licencia válida para continuar"""
        # Verificar licencia existente
        is_valid, message = self.check_license_status()
        
        if is_valid:
            return True
        
        # Si no es válida, mostrar interfaz de licencia
        st.error("🚫 ACCESO DENEGADO")
        st.error("❌ LICENCIA INACTIVA O NO CONFIGURADA")
        
        # Mostrar detalles del error
        if message:
            st.warning(f"📋 Detalle: {message}")
        
        st.markdown("---")
        
        # Mostrar interfaz para configurar licencia
        license_configured = self.show_license_interface()
        
        if not license_configured:
            st.markdown("---")
            st.markdown("### 📞 Contacto para Soporte")
            st.info("Si necesita una licencia o tiene problemas, contacte al administrador del sistema.")
            st.stop()
        
        return license_configured
