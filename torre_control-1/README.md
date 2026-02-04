# Verifica creación
ls -la src/ tests/
```

### Explicación de los comandos:

- `mkdir -p`: Crea un directorio y, si es necesario, también crea los directorios padre. La opción `-p` evita errores si el directorio ya existe.
- `ls -la`: Lista los archivos y directorios en el directorio especificado, mostrando detalles como permisos, propietario, tamaño y fecha de modificación.

### Resultado esperado:

Después de ejecutar estos comandos, deberías ver una salida similar a la siguiente al ejecutar `ls -la src/ tests/`:

```
src/:
total 0
drwxr-xr-x  2 user group  4096 date time etl

tests/:
total 0
drwxr-xr-x  2 user group  4096 date time fixtures
```

Esto confirmará que los directorios se han creado correctamente.