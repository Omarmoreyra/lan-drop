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

## Seguridad

* Diseñado para uso en red local
* No exponer a internet
* Autenticación básica incluida

## Notas

* HTTPS utiliza certificado auto-firmado
* El navegador puede mostrar advertencias de seguridad

## Licencia

MIT

