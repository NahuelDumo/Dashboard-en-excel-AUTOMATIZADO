#!/usr/bin/env python3
"""
Script para generar nuevas licencias para el Dashboard CCU
Uso: python generate_license.py
"""

import json
import random
import string
from datetime import datetime
import os

class LicenseGenerator:
    def __init__(self):
        self.licenses_file = "Licencias.txt"
        
    def generate_license_code(self):
        """Genera un código de licencia único en formato XXXX-XXXX-XXXX-XXXX"""
        def generate_segment():
            # Combina letras mayúsculas y números
            chars = string.ascii_uppercase + string.digits
            return ''.join(random.choice(chars) for _ in range(4))
        
        # Genera 4 segmentos separados por guiones
        segments = [generate_segment() for _ in range(4)]
        return '-'.join(segments)
    
    def load_existing_licenses(self):
        """Carga las licencias existentes desde el archivo"""
        if os.path.exists(self.licenses_file):
            try:
                with open(self.licenses_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        return json.loads(content)
                    else:
                        return {"Licencias": []}
            except (json.JSONDecodeError, FileNotFoundError):
                return {"Licencias": []}
        else:
            return {"Licencias": []}
    
    def save_licenses(self, licenses_data):
        """Guarda las licencias en el archivo"""
        with open(self.licenses_file, 'w', encoding='utf-8') as f:
            json.dump(licenses_data, f, indent=2, ensure_ascii=False)
    
    def license_exists(self, license_code, licenses_list):
        """Verifica si un código de licencia ya existe"""
        return any(lic.get("Codigo") == license_code for lic in licenses_list)
    
    def create_license(self, active=True, description=""):
        """Crea una nueva licencia"""
        # Cargar licencias existentes
        licenses_data = self.load_existing_licenses()
        licenses_list = licenses_data.get("Licencias", [])
        
        # Generar código único
        while True:
            license_code = self.generate_license_code()
            if not self.license_exists(license_code, licenses_list):
                break
        
        # Crear nueva licencia
        new_license = {
            "Codigo": license_code,
            "Activo": active,
            "Creada": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Descripcion": description
        }
        
        # Agregar a la lista
        licenses_list.append(new_license)
        licenses_data["Licencias"] = licenses_list
        
        # Guardar archivo
        self.save_licenses(licenses_data)
        
        return license_code, new_license
    
    def list_licenses(self):
        """Lista todas las licencias existentes"""
        licenses_data = self.load_existing_licenses()
        licenses_list = licenses_data.get("Licencias", [])
        
        if not licenses_list:
            print("No hay licencias registradas.")
            return
        
        print(f"\n{'='*60}")
        print(f"{'LISTADO DE LICENCIAS':^60}")
        print(f"{'='*60}")
        
        for i, license_item in enumerate(licenses_list, 1):
            status = "🟢 ACTIVA" if license_item.get("Activo") else "🔴 INACTIVA"
            print(f"\n{i}. Código: {license_item.get('Codigo')}")
            print(f"   Estado: {status}")
            print(f"   Creada: {license_item.get('Creada', 'N/A')}")
            if license_item.get('Descripcion'):
                print(f"   Descripción: {license_item.get('Descripcion')}")
        
        print(f"\n{'='*60}")
        print(f"Total de licencias: {len(licenses_list)}")
    
    def toggle_license_status(self, license_code):
        """Cambia el estado de una licencia (activa/inactiva)"""
        licenses_data = self.load_existing_licenses()
        licenses_list = licenses_data.get("Licencias", [])
        
        for license_item in licenses_list:
            if license_item.get("Codigo") == license_code:
                old_status = license_item.get("Activo")
                license_item["Activo"] = not old_status
                license_item["Modificada"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Guardar cambios
                self.save_licenses(licenses_data)
                
                new_status = "ACTIVA" if license_item["Activo"] else "INACTIVA"
                old_status_text = "ACTIVA" if old_status else "INACTIVA"
                
                print(f"✅ Licencia {license_code} cambiada de {old_status_text} a {new_status}")
                return True
        
        print(f"❌ No se encontró la licencia {license_code}")
        return False

def main():
    generator = LicenseGenerator()
    
    while True:
        print(f"\n{'='*50}")
        print(f"{'GENERADOR DE LICENCIAS - DASHBOARD CCU':^50}")
        print(f"{'='*50}")
        print("\n1. 🆕 Crear nueva licencia")
        print("2. 📋 Listar todas las licencias")
        print("3. 🔄 Cambiar estado de licencia")
        print("4. 🚪 Salir")
        
        try:
            choice = input("\nSeleccione una opción (1-4): ").strip()
            
            if choice == "1":
                print("\n--- CREAR NUEVA LICENCIA ---")
                description = input("Descripción (opcional): ").strip()
                
                active_input = input("¿Licencia activa? (s/N): ").strip().lower()
                active = active_input in ['s', 'si', 'sí', 'y', 'yes']
                
                license_code, license_data = generator.create_license(active, description)
                
                status = "🟢 ACTIVA" if active else "🔴 INACTIVA"
                print(f"\n✅ Licencia creada exitosamente!")
                print(f"📋 Código: {license_code}")
                print(f"📊 Estado: {status}")
                print(f"📅 Creada: {license_data['Creada']}")
                
            elif choice == "2":
                generator.list_licenses()
                
            elif choice == "3":
                print("\n--- CAMBIAR ESTADO DE LICENCIA ---")
                license_code = input("Ingrese el código de licencia: ").strip().upper()
                generator.toggle_license_status(license_code)
                
            elif choice == "4":
                print("\n👋 ¡Hasta luego!")
                break
                
            else:
                print("❌ Opción inválida. Por favor, seleccione 1-4.")
                
        except KeyboardInterrupt:
            print("\n\n👋 ¡Hasta luego!")
            break
        except Exception as e:
            print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()
