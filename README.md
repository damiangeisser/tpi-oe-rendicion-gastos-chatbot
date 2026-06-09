# Automatización del proceso de rendición de gastos internos mediante chatbot

Trabajo Práctico Integrador — Organización Empresarial  
Tecnicatura Universitaria en Programación

---

## Descripción del proyecto

Este proyecto implementa un chatbot de Telegram que automatiza el proceso interno de rendición de gastos de una organización. El bot guía a los empleados en la carga de sus solicitudes de reembolso y permite a los supervisores revisar, aprobar o rechazar las solicitudes que requieren intervención manual.

El sistema persiste todos los datos en una base de datos SQLite y aplica políticas de gasto configuradas por área y categoría.

---

## Objetivo

Modelar y automatizar mediante un chatbot conversacional el proceso de rendición de gastos internos, incorporando validaciones, políticas de negocio, derivación a supervisor y trazabilidad completa de cada solicitud.

---

## Proceso automatizado

El flujo principal comprende las siguientes etapas:

1. El empleado se identifica con su número de legajo.
2. El bot valida que el usuario esté activo en el sistema.
3. El empleado selecciona la categoría del gasto, la fecha, el monto y adjunta el comprobante en formato JPG.
4. El bot valida el formato de los datos y aplica límites de reintentos.
5. Se simula una validación por OCR del comprobante.
6. Se aplica la política de gastos correspondiente al área del empleado y la categoría seleccionada:
   - Si la solicitud cumple todas las reglas, se aprueba automáticamente.
   - Si la categoría es *Otros*, el monto supera el límite de la política o la fecha está fuera del mes en curso, la solicitud se deriva a un supervisor.
   - Si no existe una política para la combinación área-categoría, la solicitud se cancela.
7. El supervisor puede consultar las solicitudes pendientes e indicar su resolución.

---

## Alcance del prototipo

- Gestión completa del flujo de rendición para empleados activos.
- Identificación de supervisores y resolución de solicitudes derivadas.
- Persistencia en SQLite con integridad referencial.
- Exportación de datos a CSV.
- Modelado del proceso en BPMN 2.0 (situación actual y situación objetivo).
- Validación de entradas con reintentos y cancelación automática por exceso de intentos.
- Vinculación de identidad Telegram con usuario interno mediante la tabla `usuarios_telegram`.

---

## Stack técnico

| Componente | Detalle |
|---|---|
| Lenguaje | Python 3.13 |
| Framework del bot | python-telegram-bot 22.7 |
| Base de datos | SQLite 3 (stdlib) |
| Variables de entorno | python-dotenv 1.0.1 |
| API de mensajería | Telegram Bot API |
| Modelado de procesos | BPMN 2.0 |

---

## Estructura del repositorio

```
.
├── main.py                        # Punto de entrada del bot
├── configuracion.py               # Carga y validación de variables de entorno
├── base_datos.py                  # Gestión de conexiones SQLite
├── estados.py                     # Constantes de estados y códigos del dominio
├── validadores.py                 # Validaciones de formato (fecha, monto, archivo)
├── servicios.py                   # Capa de acceso a datos y lógica de negocio
├── manejadores_bot.py             # Manejadores de comandos y mensajes de Telegram
├── exportar_datos.py              # Exportación de tablas y reportes a CSV
├── inicializar_bd.py              # Inicialización y carga de datos de prueba
├── requirements.txt
├── db/
│   ├── esquema.sql                # Definición del esquema de la base de datos
│   └── datos_iniciales.sql        # Datos de referencia y usuarios de prueba
├── documentacion/
│   └── bpmn/
│       ├── rendicion_gastos_as_is.bpmn
│       ├── rendicion_gastos_as_is.png
│       ├── rendicion_gastos_to_be.bpmn
│       └── rendicion_gastos_to_be.png
└── pruebas/
    ├── casos_prueba.md
    └── evidencia_CP_01/ … evidencia_CP_17/
```

---

## Requisitos previos

- Python 3.11 o superior.
- Un bot de Telegram creado mediante [@BotFather](https://t.me/BotFather) con su token correspondiente.
- Acceso a internet para la comunicación con la API de Telegram.

---

## Configuración del entorno

Crear y activar el entorno virtual, luego instalar las dependencias:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

Crear el archivo `.env` en la raíz del proyecto con el siguiente contenido:

```
TELEGRAM_BOT_TOKEN=tu_token_de_telegram
DATABASE_PATH=db/rendicion_gastos.db
MAX_COMPROBANTE_SIZE_MB=5
```

Las tres variables son obligatorias. El bot no arranca si alguna falta o tiene un valor inválido.

---

## Inicialización de la base de datos

```powershell
python inicializar_bd.py
```

Crea el archivo de base de datos, aplica el esquema y carga los datos iniciales (roles, áreas, categorías, políticas y usuarios de prueba). Si la base de datos ya existe, la sobreescribe.

---

## Ejecución del bot

```powershell
python main.py
```

El bot inicia el polling y queda a la espera de mensajes. Para detenerlo, presionar `Ctrl+C`.

---

## Comandos disponibles

| Comando | Descripción |
|---|---|
| `/start` | Identificar usuario e iniciar el flujo según el rol. |
| `/cancelar` | Cancelar la solicitud en curso. |
| `/finalizar` | Finalizar la sesión actual y permitir identificarse nuevamente. |
| `/pendientes` | Ver solicitudes pendientes de revisión (solo supervisores). |
| `/aprobar LEGAJO` | Aprobar una solicitud pendiente del legajo indicado. |
| `/rechazar LEGAJO MOTIVO` | Rechazar una solicitud pendiente indicando el motivo. |
| `/ayuda` | Ver instrucciones de uso. |

---

## Usuarios de prueba

| Legajo | Nombre | Rol | Área | Estado |
|---|---|---|---|---|
| E1001 | Laura Fernández | Empleado | Ventas | Activo |
| E1002 | Diego Ramírez | Empleado | Operaciones | Activo |
| E1003 | Camila Torres | Empleado | Soporte | Activo |
| E1004 | Nicolás Herrera | Empleado | Administración | Inactivo |
| S0001 | Martín Silva | Supervisor | Finanzas | Activo |
| A0001 | Sofía Martínez | Administrador | Sistemas | Activo |

> El bot implementa los flujos de empleado y supervisor. E1004 está inactivo y no puede identificarse. A0001 existe en la base de datos pero el rol Administrador no tiene un flujo diferenciado en este prototipo.

---

## Flujo de uso para empleado

1. Enviar `/start`.
2. Ingresar el número de legajo (por ejemplo, `E1001`).
3. Seleccionar la categoría del gasto desde el menú de botones.
4. Ingresar la fecha del gasto en formato `DD/MM/AAAA`.
5. Ingresar el monto del gasto.
6. Adjuntar el comprobante como foto o archivo JPG.
7. El bot informa el resultado: aprobación automática, derivación a supervisor o cancelación.

En cualquier momento, `/cancelar` cancela la solicitud en curso. `/finalizar` cierra la sesión de identidad sin cancelar ninguna solicitud.

---

## Flujo de uso para supervisor

1. Enviar `/start`.
2. Ingresar el número de legajo de supervisor (por ejemplo, `S0001`).
3. Usar `/pendientes` para listar las solicitudes que requieren revisión.
4. Usar `/aprobar LEGAJO` o `/rechazar LEGAJO MOTIVO` para resolver cada solicitud.

El empleado que originó la solicitud recibe una notificación automática con el resultado.

---

## Validaciones implementadas

| Campo | Validación |
|---|---|
| Legajo | Usuario activo en la base de datos. Cancelación inmediata si no es válido. |
| Categoría | Debe pertenecer a las categorías activas del sistema. |
| Fecha | Formato `DD/MM/AAAA`, fecha real en el calendario. Hasta 3 intentos. |
| Monto | Número positivo con hasta dos decimales. Hasta 3 intentos. |
| Comprobante | Foto (Telegram convierte a JPEG) o documento `.jpg`/`.jpeg` con MIME `image/jpeg`. Tamaño máximo configurable. Hasta 3 intentos. |

Superado el límite de intentos en cualquier campo, la solicitud se cancela automáticamente.

---

## Exportación de datos

```powershell
python exportar_datos.py
```

Genera archivos CSV en la carpeta `exportaciones/`. Cada ejecución produce un conjunto de archivos identificados por timestamp:

- Un CSV por cada tabla de la base de datos.
- Un archivo `reporte_solicitudes_TIMESTAMP.csv` con los datos de solicitudes enriquecidos mediante joins (usuario, área, categoría, estados).

---

## Casos de prueba

Los casos de prueba se documentan en `pruebas/casos_prueba.md`. Cada caso cuenta con evidencia en su carpeta correspondiente (`evidencia_CP_01` a `evidencia_CP_17`), incluyendo capturas de pantalla del bot y del estado de la base de datos.

---

## Diagramas BPMN

Los diagramas del proceso se encuentran en `documentacion/bpmn/`:

| Archivo | Descripción |
|---|---|
| `rendicion_gastos_as_is.bpmn` | Proceso actual (situación sin automatización). |
| `rendicion_gastos_as_is.png` | Vista previa del diagrama as-is. |
| `rendicion_gastos_to_be.bpmn` | Proceso objetivo (con chatbot). |
| `rendicion_gastos_to_be.png` | Vista previa del diagrama to-be. |

Los archivos `.bpmn` pueden abrirse con [bpmn.io](https://bpmn.io/) u otra herramienta compatible con BPMN 2.0.

---

## Uso de IA en el proyecto

Se utilizó inteligencia artificial (Claude de Anthropic) como asistente de desarrollo durante la implementación del prototipo. Todo el código fue revisado, probado y ajustado por mi persona. La IA actuó como herramienta de apoyo; las decisiones de diseño y el modelado del proceso son propios del trabajo práctico y por lo tanto no se utilizó la IA en esa etapa.

---

## Consideraciones del prototipo

- **OCR simulado.** La validación del comprobante por reconocimiento óptico de caracteres es intencional y simulada. El foco del trabajo está en la automatización del proceso, no en visión por computadora.
- **SQLite.** Se eligió por ser liviana y suficiente para un prototipo académico. No requiere instalación de servidor.
- **Almacenamiento de comprobantes.** El bot no descarga ni almacena los archivos localmente. Guarda el `file_id` de Telegram, que permite recuperar el archivo desde la API si fuera necesario.
- **Autenticación.** La vinculación de identidad entre una cuenta de Telegram y un usuario interno se realiza a través de la tabla `usuarios_telegram`. No es un sistema de autenticación apto para producción.
- **Roles.** El bot implementa los flujos de empleado (carga de solicitud) y supervisor (resolución). El rol Administrador existe en la base de datos pero no tiene comandos diferenciados en este prototipo.
- **Este prototipo no está diseñado para uso en producción.** Su propósito es demostrar el modelado BPMN, la automatización mediante chatbot, la persistencia, las validaciones y la trazabilidad del proceso.
