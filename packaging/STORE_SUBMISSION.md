# Vinqelo Player - Microsoft Store

## Identidad reservada

- Package Identity Name: `irqv8.VinqeloPlayer`
- Publisher: `CN=516D3D9D-99E2-4CEF-8F75-6AE32D0DFA72`
- Publisher Display Name: `irqv8`
- Store ID: `9NDKG3757R44`
- Arquitectura: x64

## Archivo para Partner Center

Subir `dist/Vinqelo Player 0.7.3 Store x64.msix` en **Enviar el producto >
Paquetes**. Microsoft Store firma el paquete durante la publicacion.

En **Opciones de envio**, explicar `runFullTrust` asi:

> Vinqelo Player es una aplicacion de escritorio Win32 para administrar y
> reproducir archivos de audio locales elegidos por el usuario. Necesita plena
> confianza para reproducirlos, leer sus metadatos, mantener la biblioteca
> local, exportar listas y responder a las teclas multimedia de Windows.

La ficha de la tienda requiere como minimo una descripcion y una captura. Si se
declara que la aplicacion transmite informacion personal, Partner Center tambien
exigira una URL HTTPS publica de politica de privacidad.
