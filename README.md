# lab-1-bda
# Laboratorio 1: Cassandra - UniversiaCluster

Este proyecto implementa un clúster de Cassandra con 3 nodos usando Docker y carga datos de postulaciones universitarias para su análisis en Power BI.

## 📋 Requisitos Previos
* Docker Desktop instalado y configurado en Windows.
* Python 3.9 o superior.
* Archivo de datos `postulaciones.xlsx` en la carpeta raíz.

## 🚀 Guía de Instalación

### Paso 1: Configuración del Sistema (Windows/WSL2)
Cassandra requiere límites de memoria virtual específicos. Abre una terminal de PowerShell como administrador y ejecuta:
```bash
wsl -d docker-desktop
sysctl -w vm.max_map_count=1048575
exit



### Levantar el cluster

# Levantar el nodo semilla primero
docker-compose up -d cassandra-node1

# Esperar 30 segundos y levantar el resto
docker-compose up -d

# Crear esquema de datos
docker exec -i cassandra-node1 cqlsh < esquema.cql

# instalar dependencias python
pip install -r requirements.txt


# poblar la base de datos
python poblar_cassandra.py
