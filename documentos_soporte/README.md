# Corpus de soporte técnico

Documentación interna para el asistente RAG (Caso 2: Soporte Técnico).

## Archivos incluidos

| Archivo | Contenido |
|---------|-----------|
| `manual_docker_demo.txt` | Contenedores, puertos, daemon, volúmenes |
| `manual_linux_demo.txt` | Permisos, procesos, disco, systemd, red |
| `manual_git_demo.txt` | Merge conflicts, ramas, stash, autenticación |
| `procedimientos_soporte_demo.txt` | Clasificación tickets, escalamiento N1/N2 |
| `faq_soporte_demo.txt` | Preguntas frecuentes Docker/Linux/Git |

## Agregar documentación

Coloca archivos `.pdf`, `.txt` o `.md` en esta carpeta y ejecuta:

```bash
make reindex
```

O usa el botón **Reindexar RAG** en el panel web.
