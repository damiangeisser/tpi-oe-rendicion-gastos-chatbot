# Casos de prueba - Bot de rendición de gastos internos

## 1. Objetivo

El presente documento registra los casos de prueba ejecutados sobre el prototipo de chatbot para la rendición de gastos internos.

Las pruebas buscan verificar:

- el camino principal del proceso;
- las validaciones de datos ingresados por el usuario;
- los caminos alternativos de derivación al supervisor;
- las cancelaciones por errores o reglas de negocio;
- la persistencia de datos en SQLite;
- la correcta exportación de resultados a CSV.

---

## 2. Evidencia general

Luego de ejecutar las pruebas, se debe generar la exportación de datos mediante:

```powershell
python exportar_datos.py
```

Reporte CSV de referencia:

```text
exportaciones/reporte_solicitudes_YYYYMMDD_HHMMSS.csv
```

Reemplazar el nombre anterior por el archivo generado efectivamente:

```text
Reporte utilizado: exportaciones/reporte_solicitudes_________________.csv
```

Capturas asociadas:

```text
Carpeta o ubicación de capturas: pruebas/
```

---

## 3. Datos de prueba

| Legajo | Usuario | Rol | Área | Estado |
|---|---|---|---|---|
| E1001 | Laura Fernández | Empleado | Ventas | Activo |
| E1002 | Diego Ramírez | Empleado | Operaciones | Activo |
| E1003 | Camila Torres | Empleado | Soporte | Activo |
| E1004 | Nicolás Herrera | Empleado | Administración | Inactivo |
| S0001 | Martín Silva | Supervisor | Finanzas | Activo |
| A0001 | Sofía Martínez | Administrador | Sistemas | Activo |

---

# A. Camino feliz

## CP-01 - Aprobación automática

**Objetivo:**  
Verificar que una solicitud válida sea aprobada automáticamente sin intervención del supervisor.

**Datos utilizados:**

| Campo | Valor |
|---|---|
| Legajo | E1001 |
| Área | Ventas |
| Categoría | Transporte |
| Fecha | Fecha del mes corriente |
| Monto | Dentro del límite de aprobación automática |
| Comprobante | JPG válido |

**Pasos:**

1. Enviar `/start`.
2. Ingresar `E1001`.
3. Seleccionar `Transporte`.
4. Ingresar una fecha del mes corriente en formato `DD/MM/YYYY`.
5. Ingresar un monto dentro del límite permitido.
6. Enviar un comprobante JPG válido.

**Resultado esperado:**

- La solicitud se registra correctamente.
- El comprobante se valida técnicamente.
- La validación OCR simulada queda aprobada.
- La política de gasto se valida correctamente.
- La solicitud queda aprobada automáticamente.

**Resultado obtenido:**

```text
- La solicitud se registra correctamente.
- El comprobante se valida técnicamente.
- La validación OCR simulada queda aprobada.
- La política de gasto se valida correctamente.
- La solicitud queda aprobada automáticamente.
```

**Estado de la prueba:** Completada.

**Evidencia:**

```text
Capturas: pruebas/evidencia_CP_01
CSV: reporte_solicitudes_20260608_191042.csv
```

---

# B. Caminos alternativos

## CP-02 - Derivación por categoría Otros

**Objetivo:**  
Verificar que una solicitud con categoría `Otros` sea derivada al supervisor.

**Datos utilizados:**

| Campo | Valor |
|---|---|
| Legajo | E1001 |
| Área | Ventas |
| Categoría | Otros |
| Fecha | Fecha del mes corriente |
| Monto | Dentro del límite |
| Comprobante | JPG válido |

**Pasos:**

1. Enviar `/start`.
2. Ingresar `E1001`.
3. Seleccionar `Otros`.
4. Ingresar una fecha del mes corriente.
5. Ingresar un monto dentro del límite.
6. Enviar comprobante JPG válido.

**Resultado esperado:**

- La solicitud queda derivada al supervisor.
- El mensaje informa como motivo que la categoría seleccionada requiere revisión manual.

**Resultado obtenido:**

```text
- La solicitud queda derivada al supervisor.
- El mensaje informa como motivo que la categoría seleccionada requiere revisión manual.
```

**Estado de la prueba:** Completada.

**Evidencia:**

```text
Capturas: pruebas/evidencia_CP_02
CSV: reporte_solicitudes_20260608_191428.csv
```

---

## CP-03 - Derivación por monto excedido

**Objetivo:**  
Verificar que una solicitud sea derivada cuando el monto supera el límite de aprobación automática.

**Datos utilizados:**

| Campo | Valor |
|---|---|
| Legajo | E1001 |
| Área | Ventas |
| Categoría | Transporte |
| Fecha | Fecha del mes corriente |
| Monto | Superior al límite de la política |
| Comprobante | JPG válido |

**Pasos:**

1. Enviar `/start`.
2. Ingresar `E1001`.
3. Seleccionar `Transporte`.
4. Ingresar una fecha del mes corriente.
5. Ingresar un monto superior al límite.
6. Enviar comprobante JPG válido.

**Resultado esperado:**

- La solicitud queda derivada al supervisor.
- El mensaje informa que el monto supera el límite de aprobación automática.

**Resultado obtenido:**

```text
- La solicitud queda derivada al supervisor.
- El mensaje informa que el monto supera el límite de aprobación automática.
```

**Estado de la prueba:** Completada.

**Evidencia:**

```text
Captura: pruebas/evidencia_CP_03
CSV: reporte_solicitudes_20260608_192104.csv
```

---

## CP-04 - Derivación por fecha fuera del mes corriente

**Objetivo:**  
Verificar que una solicitud sea derivada cuando la fecha del gasto no corresponde al mes corriente.

**Datos utilizados:**

| Campo | Valor |
|---|---|
| Legajo | E1001 |
| Área | Ventas |
| Categoría | Transporte |
| Fecha | Fecha de un mes anterior |
| Monto | Dentro del límite |
| Comprobante | JPG válido |

**Pasos:**

1. Enviar `/start`.
2. Ingresar `E1001`.
3. Seleccionar `Transporte`.
4. Ingresar una fecha válida que no corresponda al mes corriente.
5. Ingresar un monto dentro del límite.
6. Enviar comprobante JPG válido.

**Resultado esperado:**

- La solicitud queda derivada al supervisor.
- El mensaje informa que la fecha del gasto no corresponde al mes corriente.

**Resultado obtenido:**

```text
- La solicitud queda derivada al supervisor.
- El mensaje informa que la fecha del gasto no corresponde al mes corriente.
```

**Estado de la prueba:** Completada.

**Evidencia:**

```text
Captura: pruebas/evidencia_CP_04
CSV: reporte_solicitudes_20260608_192810.csv
```

---

## CP-05 - Derivación por múltiples motivos

**Objetivo:**  
Verificar que el sistema acumule y muestre todos los motivos de derivación aplicables.

**Datos utilizados:**

| Campo | Valor |
|---|---|
| Legajo | E1001 |
| Área | Ventas |
| Categoría | Otros |
| Fecha | Fecha fuera del mes corriente |
| Monto | Superior al límite |
| Comprobante | JPG válido |

**Pasos:**

1. Enviar `/start`.
2. Ingresar `E1001`.
3. Seleccionar `Otros`.
4. Ingresar una fecha válida que no corresponda al mes corriente.
5. Ingresar un monto superior al límite.
6. Enviar comprobante JPG válido.

**Resultado esperado:**

- La solicitud queda derivada al supervisor.
- El mensaje lista todos los motivos:
  - La categoría seleccionada requiere revisión manual.
  - El monto supera el límite de aprobación automática.
  - La fecha del gasto no corresponde al mes corriente.

**Resultado obtenido:**

```text
- La solicitud queda derivada al supervisor.
- El mensaje lista todos los motivos:
  - La categoría seleccionada requiere revisión manual.
  - El monto supera el límite de aprobación automática.
  - La fecha del gasto no corresponde al mes corriente.
```

**Estado de la prueba:** Completada.

**Evidencia:**

```text
Captura: pruebas/evidencia_CP_05
CSV: reporte_solicitudes_20260608_193418.csv
```

---

## CP-06 - Supervisor aprueba solicitud derivada

**Objetivo:**  
Verificar que el supervisor pueda aprobar una solicitud derivada.

**Precondición:**

Debe existir una solicitud derivada al supervisor para el legajo `E1001`.

**Datos utilizados:**

| Campo | Valor |
|---|---|
| Supervisor | S0001 |
| Solicitud a aprobar | E1001 |

**Pasos:**

1. Enviar `/finalizar` si se requiere cambiar de usuario.
2. Enviar `/start`.
3. Ingresar `S0001`.
4. Enviar `/pendientes`.
5. Verificar que figure una solicitud pendiente para `E1001`.
6. Enviar `/aprobar E1001`.

**Resultado esperado:**

- El supervisor recibe confirmación de aprobación.
- El empleado recibe notificación.
- La solicitud queda en estado `Aprobada`.

**Resultado obtenido:**

```text
- El supervisor recibe confirmación de aprobación.
- El empleado recibe notificación.
- La solicitud queda en estado `Aprobada`.
```

**Estado de la prueba:** Completada.

**Evidencia:**

```text
Captura: pruebas/evidencia_CP_06
CSV: reporte_solicitudes_20260608_194658.csv
```

---

## CP-07 - Supervisor rechaza solicitud derivada

**Objetivo:**  
Verificar que el supervisor pueda rechazar una solicitud derivada indicando un motivo.

**Precondición:**

Debe existir una solicitud derivada al supervisor para el legajo `E1001`.

**Datos utilizados:**

| Campo | Valor |
|---|---|
| Supervisor | S0001 |
| Solicitud a rechazar | E1001 |
| Motivo | El comprobante no corresponde al gasto informado |

**Pasos:**

1. Enviar `/finalizar` si se requiere cambiar de usuario.
2. Enviar `/start`.
3. Ingresar `S0001`.
4. Enviar `/pendientes`.
5. Verificar que figure una solicitud pendiente para `E1001`.
6. Enviar `/rechazar E1001 El comprobante no corresponde al gasto informado`.

**Resultado esperado:**

- El supervisor recibe confirmación de rechazo.
- El empleado recibe notificación con el motivo.
- La solicitud queda en estado `Rechazada`.
- El motivo queda registrado.

**Resultado obtenido:**

```text
- El supervisor recibe confirmación de rechazo.
- El empleado recibe notificación con el motivo.
- La solicitud queda en estado `Rechazada`.
- El motivo queda registrado.
```

**Estado de la prueba:** Completada.

**Evidencia:**

```text
Captura: pruebas/evidencia_CP_07
CSV: reporte_solicitudes_20260608_195647.csv
```

---

# C. Caminos de error y estrés

## CP-08 - Legajo inexistente

**Objetivo:**  
Verificar que el sistema cancele la solicitud cuando se ingresa un legajo inexistente.

**Datos utilizados:**

| Campo | Valor |
|---|---|
| Legajo | X9999 |

**Pasos:**

1. Enviar `/start`.
2. Ingresar `X9999`.

**Resultado esperado:**

- La solicitud se cancela.
- El mensaje informa que el legajo es inválido o que el usuario no está habilitado.

**Resultado obtenido:**

```text
- La solicitud se cancela.
- El mensaje informa que el legajo es inválido o que el usuario no está habilitado.
```

**Estado de la prueba:** Completada.

**Evidencia:**

```text
Captura: pruebas/evidencia_CP_08
CSV: reporte_solicitudes_20260608_195647.csv
```

---

## CP-09 - Usuario inactivo

**Objetivo:**  
Verificar que el sistema rechace a un usuario existente pero inactivo.

**Datos utilizados:**

| Campo | Valor |
|---|---|
| Legajo | E1004 |
| Usuario | Nicolás Herrera |
| Estado | Inactivo |

**Pasos:**

1. Enviar `/start`.
2. Ingresar `E1004`.

**Resultado esperado:**

- La solicitud se cancela.
- El sistema informa que el legajo es inválido o que el usuario no está habilitado.

**Resultado obtenido:**

```text
- La solicitud se cancela.
- El sistema informa que el legajo es inválido o que el usuario no está habilitado.
```

**Estado de la prueba:** Completada.

**Evidencia:**

```text
Captura: pruebas/evidencia_CP_09
CSV: reporte_solicitudes_20260608_201742.csv
```

---

## CP-10 - Fecha inválida hasta cancelar

**Objetivo:**  
Verificar el control de intentos en la carga de fecha.

**Datos utilizados:**

| Campo | Valor |
|---|---|
| Legajo | E1001 |
| Categoría | Transporte |
| Fechas inválidas | `abc`, `31/02/2026`, `2026-06-15` |

**Pasos:**

1. Enviar `/start`.
2. Ingresar `E1001`.
3. Seleccionar `Transporte`.
4. Ingresar `abc`.
5. Ingresar `31/02/2026`.
6. Ingresar `2026-06-15`.

**Resultado esperado:**

- Cada fecha inválida incrementa el contador de intentos.
- Al tercer intento inválido, la solicitud se cancela.
- El motivo de cancelación queda registrado.

**Resultado obtenido:**

```text
- Cada fecha inválida incrementa el contador de intentos.
- Al tercer intento inválido, la solicitud se cancela.
- El motivo de cancelación queda registrado.
```

**Estado de la prueba:** Completada.

**Evidencia:**

```text
Captura: pruebas/evidencia_CP_10
CSV: reporte_solicitudes_20260608_202136.csv
```

---

## CP-11 - Monto inválido hasta cancelar

**Objetivo:**  
Verificar el control de intentos en la carga de monto.

**Datos utilizados:**

| Campo | Valor |
|---|---|
| Legajo | E1001 |
| Categoría | Transporte |
| Fecha | Fecha válida |
| Montos inválidos | `abc`, `-100`, `0` |

**Pasos:**

1. Enviar `/start`.
2. Ingresar `E1001`.
3. Seleccionar `Transporte`.
4. Ingresar una fecha válida.
5. Ingresar `abc`.
6. Ingresar `-100`.
7. Ingresar `0`.

**Resultado esperado:**

- Cada monto inválido incrementa el contador de intentos.
- Al tercer intento inválido, la solicitud se cancela.
- El motivo de cancelación queda registrado.

**Resultado obtenido:**

```text
- Cada monto inválido incrementa el contador de intentos.
- Al tercer intento inválido, la solicitud se cancela.
- El motivo de cancelación queda registrado.
```

**Estado de la prueba:** Completada.

**Evidencia:**

```text
Captura: pruebas/evidencia_CP_11
CSV: reporte_solicitudes_20260608_202633.csv
```

---

## CP-12 - Comprobante inválido hasta cancelar

**Objetivo:**  
Verificar el control de intentos en la carga de comprobante.

**Datos utilizados:**

| Campo | Valor |
|---|---|
| Legajo | E1001 |
| Categoría | Transporte |
| Fecha | Fecha válida |
| Monto | Monto válido |
| Comprobantes inválidos | PDF, PNG, texto/sticker |

**Pasos:**

1. Enviar `/start`.
2. Ingresar `E1001`.
3. Seleccionar `Transporte`.
4. Ingresar una fecha válida.
5. Ingresar un monto válido.
6. Enviar un archivo PDF.
7. Enviar un archivo PNG.
8. Enviar texto, sticker u otro contenido no válido.

**Resultado esperado:**

- Cada comprobante inválido incrementa el contador de intentos.
- Al tercer intento inválido, la solicitud se cancela.
- El motivo de cancelación queda registrado.

**Resultado obtenido:**

```text
- Cada comprobante inválido incrementa el contador de intentos.
- Al tercer intento inválido, la solicitud se cancela.
- El motivo de cancelación queda registrado.
```

**Estado de la prueba:** Completada.

**Evidencia:**

```text
Captura: pruebas/evidencia_CP_12
CSV: reporte_solicitudes_20260608_203831.csv
```

---

## CP-13 - Archivo no JPG

**Objetivo:**  
Verificar que el sistema rechace comprobantes que no cumplan con el formato JPG/JPEG.

**Datos utilizados:**

| Campo | Valor |
|---|---|
| Legajo | E1001 |
| Categoría | Transporte |
| Fecha | Fecha válida |
| Monto | Monto válido |
| Archivo | PDF o PNG |

**Pasos:**

1. Enviar `/start`.
2. Ingresar `E1001`.
3. Seleccionar `Transporte`.
4. Ingresar fecha válida.
5. Ingresar monto válido.
6. Enviar un archivo que no sea JPG/JPEG.

**Resultado esperado:**

- El sistema rechaza el archivo.
- El sistema solicita reenviar un comprobante JPG válido.
- Se incrementa `intentos_comprobante`.

**Resultado obtenido:**

```text
- El sistema rechaza el archivo.
- El sistema solicita reenviar un comprobante JPG válido.
- Se incrementa `intentos_comprobante`.
```

**Estado de la prueba:** Completada.

**Evidencia:**

```text
Captura: pruebas/evidencia_CP_13
CSV: reporte_solicitudes_20260608_204404.csv
```

---

## CP-14 - Categoría no permitida para el área

**Objetivo:**  
Verificar que el sistema cancele la solicitud cuando la categoría seleccionada no está permitida para el área del empleado.

**Datos utilizados:**

| Campo | Valor |
|---|---|
| Legajo | E1003 |
| Área | Soporte |
| Categoría | Viáticos |
| Fecha | Fecha válida |
| Monto | Monto válido |
| Comprobante | JPG válido |

**Pasos:**

1. Enviar `/start`.
2. Ingresar `E1003`.
3. Seleccionar `Viáticos`.
4. Ingresar una fecha válida.
5. Ingresar un monto válido.
6. Enviar comprobante JPG válido.

**Resultado esperado:**

- La solicitud se cancela.
- El mensaje informa:
  - área del empleado;
  - categoría seleccionada;
  - categorías válidas para el área;
  - indicación de consultar a RR. HH.
- El motivo de cancelación queda registrado.

**Resultado obtenido:**

```text
- La solicitud se cancela.
- El mensaje informa:
  - área del empleado;
  - categoría seleccionada;
  - categorías válidas para el área;
  - indicación de consultar a RR. HH.
- El motivo de cancelación queda registrado.
```

**Estado de la prueba:** Completada.

**Evidencia:**

```text
Captura: pruebas/evidencia_CP_14
CSV: reporte_solicitudes_20260608_204806.csv
```

---

## CP-15 - Mensajes inesperados durante el flujo

**Objetivo:**  
Verificar que el bot maneje entradas no esperadas sin romper el flujo.

**Datos utilizados:**

| Campo | Valor |
|---|---|
| Legajo | E1003 |
| Entradas no esperadas | stickers, emojis, archivos o mensajes fuera del campo esperado |

**Pasos:**

1. Enviar `/start`.
2. Durante la carga de legajo, fecha, monto o comprobante, enviar una entrada no esperada.
3. Observar la respuesta del bot.

**Resultado esperado:**

- El bot responde con un mensaje controlado.
- No se produce error de ejecución.
- No se guarda información inválida.
- En los campos con intentos, se incrementa el contador correspondiente.

**Resultado obtenido:**

```text
- El bot responde con un mensaje controlado.
- No se produce error de ejecución.
- No se guarda información inválida.
- En los campos con intentos, se incrementa el contador correspondiente.
```

**Estado de la prueba:** Completada.

**Evidencia:**

```text
Captura: pruebas/evidencia_CP_15
CSV: reporte_solicitudes_20260608_210704.csv
```

---

## CP-16 - Cancelación manual durante la carga

**Objetivo:**  
Verificar que el usuario pueda cancelar una solicitud en curso.

**Datos utilizados:**

| Campo | Valor |
|---|---|
| Legajo | E1001 |
| Comando | `/cancelar` |

**Pasos:**

1. Enviar `/start`.
2. Ingresar `E1001`.
3. Antes de completar toda la solicitud, enviar `/cancelar`.

**Resultado esperado:**

- La solicitud se cancela.
- El estado queda en `Cancelada`.
- El bot informa que se puede enviar `/start` para iniciar una nueva solicitud.

**Resultado obtenido:**

```text
- La solicitud se cancela.
- El estado queda en `Cancelada`.
- El bot informa que se puede enviar `/start` para iniciar una nueva solicitud.
```

**Estado de la prueba:** Completada.

**Evidencia:**

```text
Captura: pruebas/evidencia_CP_16
CSV: reporte_solicitudes_20260608_211332.csv
```

---

## CP-17 - Finalizar sesión y cambiar de usuario

**Objetivo:**  
Verificar que `/finalizar` cierre la sesión de Telegram sin afectar indebidamente las solicitudes.

**Datos utilizados:**

| Campo | Valor |
|---|---|
| Usuario inicial | E1001 |
| Nuevo usuario | S0001 |
| Comando | `/finalizar` |

**Pasos:**

1. Identificarse con `/start` y `E1001`.
2. Completar o dejar una solicitud derivada al supervisor.
3. Enviar `/finalizar`.
4. Enviar `/start`.
5. Ingresar `S0001`.

**Resultado esperado:**

- La sesión anterior se finaliza.
- El bot vuelve a pedir legajo.
- El supervisor puede identificarse correctamente.
- Si había solicitud pendiente, esta permanece en revisión.

**Resultado obtenido:**

```text
- La sesión anterior se finaliza.
- El bot vuelve a pedir legajo.
- El supervisor puede identificarse correctamente.
- Si había solicitud pendiente, esta permanece en revisión.
```

**Estado de la prueba:** Completada.

**Evidencia:**

```text
Captura: pruebas/evidencia_CP_17
CSV: reporte_solicitudes_20260608_211942.csv
```

---

## 4. Resumen de ejecución

Completar luego de ejecutar las pruebas.

| ID | Caso | Estado | Evidencia |
|---|---|---|---|
| CP-01 | Aprobación automática | Pendiente | |
| CP-02 | Derivación por categoría Otros | Pendiente | |
| CP-03 | Derivación por monto excedido | Pendiente | |
| CP-04 | Derivación por fecha fuera del mes corriente | Pendiente | |
| CP-05 | Derivación por múltiples motivos | Pendiente | |
| CP-06 | Supervisor aprueba solicitud derivada | Pendiente | |
| CP-07 | Supervisor rechaza solicitud derivada | Pendiente | |
| CP-08 | Legajo inexistente | Pendiente | |
| CP-09 | Usuario inactivo | Pendiente | |
| CP-10 | Fecha inválida hasta cancelar | Pendiente | |
| CP-11 | Monto inválido hasta cancelar | Pendiente | |
| CP-12 | Comprobante inválido hasta cancelar | Pendiente | |
| CP-13 | Archivo no JPG | Pendiente | |
| CP-14 | Categoría no permitida para el área | Pendiente | |
| CP-15 | Mensajes inesperados durante el flujo | Pendiente | |
| CP-16 | Cancelación manual durante la carga | Pendiente | |
| CP-17 | Finalizar sesión y cambiar de usuario | Pendiente | |

---

## 5. Observaciones generales

```text
Pendiente de completar luego de ejecutar las pruebas.
```