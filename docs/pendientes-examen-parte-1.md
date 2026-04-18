# Pendientes completos del examen (Seccion 1 - 70%)

## 1) Cumplimiento obligatorio del examen

- [X] Leer y comprender todo el documento antes de implementar.
  - Como hacerlo: hacer una lectura completa y validar dudas del equipo antes de codificar.

- [X] Mantener trabajo grupal coordinado.
  - Como hacerlo: repartir responsables por modulo (auth, CRUD, docs, pipeline, despliegue).

- [ ] Entregar solo por AV y dentro de la fecha (19/04/2026 11:59 pm).
  - Como hacerlo: subir entregables con al menos 12 horas de margen y verificar que quedaron publicados.

- [ ] Evitar plagio/copia entre grupos.
  - Como hacerlo: producir codigo, arquitectura y documentacion propias con commits del equipo.

- [X] Respetar tecnologias exigidas (Flask + Cloudinary y stack solicitado).
  - Como hacerlo: no sustituir framework ni servicios por alternativas fuera de lo pedido.

- [ ] Entregar exactamente la documentacion solicitada.
  - Como hacerlo: incluir solo README requerido + video solicitado + repo privado compartido.

- [ ] Preparar defensa tecnica total del sistema (cualquier integrante).
  - Como hacerlo: realizar simulacro de preguntas tecnicas con todo el equipo.

- [ ] Considerar integracion de la segunda parte en el dia 4.
  - Como hacerlo: dejar arquitectura extensible y documentar decisiones para poder integrar cambios rapido.

## 2) Pendientes funcionales de la API

- [X] Incluir campos minimos por registro.
  - Como hacerlo: persistir nombre paciente, identificacion/historia, referencia clinica, fecha estudio, url imagen.

- [ ] Permitir agregar campos opcionales utiles.
  - Como hacerlo: extender modelo/schemas sin romper campos obligatorios.

- [X] Implementar CRUD completo de registros radiograficos.
  - Como hacerlo: crear endpoints crear, listar, obtener, actualizar y eliminar.

- [X] Subir imagenes por multipart/form-data.
  - Como hacerlo: endpoint de creacion/actualizacion que reciba archivo e info del paciente.

- [X] Validar tipo y tamano maximo de archivo.
  - Como hacerlo: lista blanca de MIME/extensiones y limite de bytes antes de subir.

- [X] Almacenar imagen en servicio externo y guardar URL en BD.
  - Como hacerlo: subir a Cloudinary y persistir secure_url/public_id.

- [X] Servir imagenes por URL CDN, no desde la API.
  - Como hacerlo: responder con URL publica de Cloudinary en el recurso.

- [X] Implementar consulta con paginacion, filtros basicos y ordenamiento.
  - Como hacerlo: parametros page/size/sort + filtros por campos clave.

- [X] Implementar autenticacion con Google SSO.
  - Como hacerlo: configurar flujo OAuth con Google y endpoint de login/callback.

- [X] Generar JWT tras autenticacion para acceso a endpoints protegidos.
  - Como hacerlo: emitir token firmado en login y validar token en rutas privadas.

## 3) Pendientes tecnicos de implementacion

- [X] Usar Flask como framework principal.
  - Como hacerlo: mantener app factory/rutas en Flask y modularizar por blueprints.

- [X] Integrar Cloudinary para gestion de imagenes.
  - Como hacerlo: centralizar en servicio dedicado y usar variables de entorno.

- [X] Mantener arquitectura por capas.
  - Como hacerlo: separar routers, services, repositories y schemas sin mezclar responsabilidades.

- [X] Usar SQLite como base de datos.
  - Como hacerlo: configurar cadena de conexion SQLite en entorno de desarrollo.

- [X] Usar SQLAlchemy para modelos/consultas.
  - Como hacerlo: definir modelos ORM y acceso a datos por repositorios.

- [X] Gestionar cambios con Alembic.
  - Como hacerlo: crear y aplicar migraciones por cada cambio de esquema.

- [X] Validar entrada y salida con Pydantic.
  - Como hacerlo: definir schemas request/response y validar en endpoints.

- [X] Publicar documentacion automatica con Swagger.
  - Como hacerlo: configurar Flasgger/OpenAPI y exponer endpoint de docs.

- [X] Agregar ejemplos claros en endpoints principales.
  - Como hacerlo: incluir ejemplos de request/response y errores comunes en la documentacion.

- [X] Configurar pipeline basico CI.
  - Como hacerlo: workflow que instale dependencias y levante/verifique la app sin errores.

- [ ] Desplegar en servicio gratuito con acceso publico.
  - Como hacerlo: usar plataforma free tier, configurar variables y publicar URL funcional.

## 4) Pendientes de entrega obligatoria

- [ ] Compartir repositorio privado con el profesor.
  - Como hacerlo: agregar permisos al repo y validar acceso del profesor antes de cierre.

- [X] Completar README con lo requerido.
  - Como hacerlo: incluir instalacion, descripcion del sistema y decisiones tecnicas.

- [ ] Grabar video de 15 a 20 minutos.
  - Como hacerlo: guion por secciones y ensayo para no exceder ni quedar corto.

- [ ] Explicar en video: funcionamiento del sistema.
  - Como hacerlo: demo end-to-end de login, CRUD y consulta.

- [ ] Explicar en video: arquitectura implementada.
  - Como hacerlo: mostrar estructura por capas y flujo router -> service -> repository.

- [ ] Explicar en video: problemas y soluciones.
  - Como hacerlo: listar 3-5 bloqueos reales y como se resolvieron.

- [ ] Explicar en video: resultados obtenidos.
  - Como hacerlo: evidenciar API operativa, docs, CI y despliegue publico.

- [ ] Explicar en video: conclusiones del proyecto.
  - Como hacerlo: cerrar con aprendizajes tecnicos y mejoras futuras.

## 5) Checklist alineado a rubrica (para maximo puntaje)

- [X] Arquitectura y organizacion (15%).
  - Como hacerlo: mantener capas claras, naming consistente y baja dependencia cruzada.

- [X] Autenticacion SSO + JWT (15%).
  - Como hacerlo: flujo completo sin atajos, validacion robusta y pruebas de error.

- [X] CRUD y logica de negocio (15%).
  - Como hacerlo: operaciones completas con validaciones y manejo correcto de casos borde.

- [X] Manejo de archivos y CDN (15%).
  - Como hacerlo: subida estable, validada, con URL publica real y persistencia correcta.

- [X] Validaciones con Pydantic (10%).
  - Como hacerlo: constraints por campo, mensajes claros y schemas de respuesta.

- [X] Pipeline (10%).
  - Como hacerlo: ejecutar instalacion y verificacion de arranque en cada push.

- [X] Documentacion (10%).
  - Como hacerlo: docs navegables, completas y con ejemplos utiles.

- [ ] Presentacion en video (10%).
  - Como hacerlo: exposicion clara, ordenada y dentro del tiempo.

## 6) Verificacion final antes de entregar

- [ ] API responde en entorno local y en despliegue publico.
  - Como hacerlo: correr prueba de endpoints clave en ambos entornos.

- [X] Endpoints protegidos exigen JWT valido.
  - Como hacerlo: probar casos con token valido, invalido y ausente.

- [X] Subida de imagen rechaza archivos invalidos o grandes.
  - Como hacerlo: pruebas negativas de formato y tamano.

- [X] URL de imagen es externa/CDN y persiste correctamente.
  - Como hacerlo: verificar URL en BD y acceso desde navegador.

- [X] Migraciones aplicadas y base consistente.
  - Como hacerlo: ejecutar migraciones limpias y revisar esquema final.

- [ ] README y video cumplen exactamente lo solicitado.
  - Como hacerlo: checklist final de requisitos contra documento del examen.

- [ ] Entrega efectuada en AV dentro del plazo.
  - Como hacerlo: subir y confirmar evidencia de entrega antes del cierre.
