# UNIVERSIDAD NACIONAL
**Sede Regional Brunca**  
**EIF209 Programación IV**  
**Profesores:** Daniel Granados Murillo, Ruben Mora Vargas, Juan Gamboa Abarca

# Examen Programación IV
**Fecha de entrega:** 19/04/2026 11:59 pm  
**Tema:** Desarrollo de API con Flask, Autenticación SSO y Gestión de Archivos con Cloudinary

## Instrucciones generales
1. Lea y comprenda cuidadosamente todo el documento antes de iniciar la actividad.
2. La actividad es de carácter grupal.
3. El trabajo deberá entregarse en el AV, no se aceptarán trabajos por otros medios, además si el trabajo se entrega de forma tardía tendrá una nota de 0.
4. Aunque sea una actividad de carácter grupal, si se encuentra plagia/copia entre grupos, a los grupos involucrados se les colocará un 0 en la nota.
5. Este examen estará segmentado en dos secciones, en el presente documento se presenta la primera sección la cual tiene un valor del 70%.
6. Este examen deberá realizarse con las tecnologías descritas, el uso de otra tecnología o tecnologías conllevará a colocar una nota de 0.
7. Si se entrega otra documentación que no sea la solicitada se penalizará a será directamente una nota 0.
8. Deberá conocer el 100% del sistema, el examen puede estar sujeto a preguntas por parte del profesor en la siguiente clase a cualquier participante del grupo.

## Descripción general
En este examen, los estudiantes deberán diseñar, implementar y desplegar una API utilizando Flask orientada a la gestión de placas radiográficas de pacientes.  
El sistema deberá integrar autenticación mediante Google (SSO), manejo de sesiones con JWT, carga de archivos mediante `multipart/form-data` y almacenamiento de imágenes utilizando un servicio que exponga los recursos a través de un CDN.  
El objetivo de este examen es evaluar la capacidad de integrar múltiples componentes modernos del desarrollo backend, estructurar un proyecto de forma clara, resolver problemas reales de implementación y comunicar de manera efectiva las decisiones técnicas tomadas.  
El trabajo se realizará en grupos de proyecto a la fecha.

## Contexto del sistema
El sistema a desarrollar corresponde a una plataforma para la gestión de placas radiográficas de pacientes. Cada registro deberá permitir almacenar la información básica del paciente, una referencia clínica breve y la imagen radiográfica asociada.  
La API deberá permitir que los usuarios autenticados registren pacientes, suban placas radiográficas, consulten la información almacenada y actualicen los registros existentes. Las imágenes deberán almacenarse en un servicio externo y ser accesibles mediante una URL pública servida por CDN.  
**IMPORTANTE:** Deben realizar el API nada más.  
Aunque el contexto del proyecto es clínico, el examen se centrará en la construcción técnica de la API, en la organización del proyecto y en la calidad de la solución implementada.

## Alcance del sistema
El sistema deberá permitir:
- Autenticación de usuarios mediante Google SSO
- Generación y uso de tokens JWT para acceso a la API
- Creación, consulta, actualización y eliminación de registros de pacientes y de sus placas radiográficas asociadas
- Asociación de imágenes radiográficas a los registros creados
- Carga de archivos mediante solicitudes `multipart/form-data`
- Almacenamiento de imágenes en un servicio externo que exponga las URLs mediante CDN
- Consulta de información con soporte de paginación, filtros básicos y ordenamiento

## Requerimientos funcionales
### Autenticación
El sistema deberá permitir el inicio de sesión mediante Google. Una vez autenticado el usuario, la API deberá generar un JWT que será utilizado para acceder a los endpoints protegidos.  
No se requiere manejo de roles o permisos, para facilidad de la prueba.

### Gestión de contenido
Se deberá implementar un CRUD completo para la entidad principal del sistema, correspondiente al registro de placas radiográficas de pacientes.  
Cada registro deberá incluir, como mínimo:
- nombre completo del paciente
- número de identificación o código de historia clínica
- descripción o referencia clínica breve
- fecha del estudio
- imagen radiográfica asociada  
El equipo podrá agregar campos adicionales si los considera útiles para su diseño.

### Carga de archivos
El sistema deberá aceptar archivos mediante `multipart/form-data`. Se deberá validar al menos:
- tipo de archivo
- tamaño máximo  
Las imágenes deberán almacenarse en un servicio externo y la URL resultante deberá persistirse en la base de datos.

### Uso de CDN
Las imágenes no deben servirse directamente desde la API. Se debe utilizar un servicio que permita acceder a los archivos mediante una URL pública (CDN).

## Requerimientos técnicos
### Tecnologías
- Flask
- Cloudinary

### Arquitectura
El proyecto debe estar organizado en capas, incluyendo al menos:
- routers
- services
- repositories
- schemas

### Base de datos
- Uso de SQLite
- Uso de SQLAlchemy
- Migraciones con Alembic

### Validación
- Uso de Pydantic para validación de datos de entrada y salida

### Documentación
- Documentación automática con Swagger
- Inclusión de ejemplos claros en los endpoints principales

### Pipeline
Se debe configurar un pipeline básico que:
- instale dependencias
- verifique que la aplicación pueda ejecutarse correctamente

### Despliegue
El sistema debe estar desplegado en un servicio gratuito accesible públicamente.

## Entrega
Cada grupo deberá:
1. Compartir un repositorio privado con el profesor.
2. Incluir un `README` con:
   - instrucciones de instalación
   - descripción del sistema
   - decisiones técnicas relevantes
3. Entregar un video de entre 15 y 20 minutos donde se explique:
   - Funcionamiento del sistema
   - Arquitectura implementada
   - Problemas encontrados y cómo fueron resueltos
   - Resultados obtenidos
   - Conclusiones del proyecto
   *El incumplimiento del tiempo establecido en el video afectará la calificación.*

## Rúbrica de Evaluación
La evaluación se realizará según la siguiente tabla:

| Criterio | Peso | Nulo o Malo (0% – 50%) | Bueno (51% – 80%) | Excelente (81% – 100%) |
|:---|:---:|:---|:---|:---|
| **Arquitectura y organización** | 15% | No existe estructura por capas o está mal implementada | Se aplica arquitectura por capas, pero con inconsistencias | Arquitectura clara, consistente y correctamente separada |
| **Autenticación (SSO + JWT)** | 15% | No funciona o está incompleta la autenticación | Funciona, pero con errores menores o inconsistencias | Flujo completo, funcional y correctamente integrado |
| **CRUD y lógica de negocio** | 15% | CRUD incompleto o con errores críticos | CRUD completo, pero con validaciones o lógica limitada | CRUD completo, consistente y correctamente validado |
| **Manejo de archivos y CDN** | 15% | No se suben archivos o no se integran con CDN | Subida funcional, pero con validaciones incompletas | Subida correcta, validada y con integración real a CDN |
| **Validaciones (Pydantic)** | 10% | No se utilizan validaciones o son incorrectas | Validaciones básicas implementadas | Validaciones completas, correctas y bien estructuradas |
| **Pipeline** | 10% | No existe pipeline o no ejecuta correctamente | Pipeline ejecuta parcialmente | Pipeline funcional que valida ejecución del proyecto |
| **Documentación** | 10% | No existe o no permite entender el proyecto | Documentación básica suficiente | Documentación clara, completa y bien estructurada |
| **Presentación en video** | 10% | No explica el sistema o excede el tiempo permitido | Explica parcialmente con problemas de claridad o tiempo | Explicación clara, completa y dentro del tiempo establecido |

## Consideraciones finales
- Se espera que el trabajo refleje no solo la implementación funcional, sino también la capacidad de diseñar un sistema coherente, tomar decisiones técnicas fundamentadas y comunicar el proceso de desarrollo de forma clara.
- El uso de herramientas externas está permitido, pero cada grupo debe demostrar comprensión total de lo implementado.
- Si no presenta video o no presenta código en tiempo y forma, la calificación es nula sin derecho a reclamo. La nota es para todos los integrantes del equipo, sean proactivos, empoderados y profesionales.
- El examen cuenta con 7 días para su realización, al inicio del 4° día, se les entregará a los estudiantes la segunda parte, la cual deberá integrarse al sistema inicial que tiene en ese momento, por lo cual, el video y presentación final del documento deberá incluir esta nueva sección que se agregará en el día 4.