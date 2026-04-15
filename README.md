# LAN Drop (Local File Transfer)

Servidor local simple para compartir archivos entre dispositivos en la misma red.

## Características

* Subida de archivos desde el celular
* Descarga desde PC
* Interfaz web simple
* Generación de QR para acceso rápido
* Autenticación básica
* Funciona en red local

## Requisitos

* Python 3
* Linux o Windows

## Instalación

```bash
git clone https://github.com/Omarmoreyra/lan-drop.git
cd lan-drop
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Uso

```bash
python3 compartir.py
```

Abrir en el navegador:

```
http://IP_LOCAL:5000
```

## Configuración

Crear un archivo `.env` en la raíz del proyecto:

```
USERNAME=usuario
PASSWORD=contraseña

UPLOAD_FOLDER=/ruta/a/compartidos
DOWNLOAD_FOLDER=/ruta/a/descargas
```
## Scripts de ejecución (opcional)

Para facilitar el uso, se pueden crear scripts que automaticen el arranque del servidor.

### Linux (.sh)

Crear un archivo `iniciar.sh`:

```bash
#!/bin/bash

cd "$(dirname "$0")"
source venv/bin/activate
python3 (Ruta del archivo)/compartir.py
```

Dar permisos de ejecución:

```bash
chmod +x iniciar.sh
```

Ejecutar:

```bash
./iniciar.sh
```


### Windows (.bat)

Crear un archivo `iniciar.bat`:

```bat
@echo off
cd /d %~dp0
call venv\Scripts\activate
python (Ruta del archivo)/compartir.py
pause
```

Ejecutar con doble click.


## Seguridad

* Diseñado para uso en red local
* No exponer a internet
* Autenticación básica incluida

## Notas

* HTTPS utiliza certificado auto-firmado
* El navegador puede mostrar advertencias de seguridad
* Asegurarse de haber creado previamente el entorno virtual (`venv`)
* Instalar dependencias con `pip install -r requirements.txt`
* En Linux, puede ser necesario ejecutar el script desde una terminal si el entorno gráfico no lo permite directamente


## Licencia

MIT

