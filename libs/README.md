# Cairo DLL Dependencies (Windows)

This directory contains the Cairo graphics library DLLs required for artistic QR code generation.

## Required DLLs


### Core Cairo DLLs:
- `libcairo-2.dll` (main Cairo library)
- `libcairo-gobject-2.dll` (if available)

### Required Dependencies:
- `libpng16.dll` (PNG support)
- `zlib1.dll` (compression)
- `libfreetype-6.dll` (font rendering)
- `libfontconfig-1.dll` (font configuration)
- `libexpat-1.dll` (XML parsing)
- `libglib-2.0-0.dll` (GLib utilities)
- `libgobject-2.0-0.dll` (GObject system)
- `libpixman-1-0.dll` (pixel manipulation)
- `libiconv-2.dll` (character encoding)
- `libintl-8.dll` (internationalization)

## Licensing

All Cairo and GTK libraries are **LGPL 2.1** licensed:
- ✅ Redistribution allowed
- ✅ Commercial use allowed  
- ✅ No source disclosure required for your app
- ⚠️ Include LGPL-2.1.txt license file
