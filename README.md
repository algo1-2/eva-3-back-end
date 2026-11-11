# SaludVital – Plataforma de Pre-agendamiento de Exámenes y Prestaciones Médicas

## Ficha de registro y aprobación de la propuesta

| Campo | Detalle |
|---|---|
| **Nombre de la Organización o Plataforma** | SaludVital |
| **Modelo de Negocio / Giro** | Centro de atención médica ambulatoria |
| **Integrantes del Equipo** | Benjamín Rivas Bustos – RUT: 21460164-8 |
| **Entidad de Contexto / Agrupación (ORM)** | `Especialidad` |
| **Entidad Principal Gestionable (ORM)** | `Prestacion` |
| **Propósito de la Sesión (`request.session`)** | Canasta de exámenes: pre-agendamiento temporal de prestaciones con control de cupos y cálculo de copago estimado según previsión (Fonasa / Isapre / Particular) |
| **Asignatura** | Programación Back End (TI3041) – Evaluación Sumativa N° 3, Unidad 2: Framework Back End |

## 1. Descripción

SaludVital es una aplicación web desarrollada con **Django 4.2 LTS** que permite a los pacientes explorar un catálogo público de prestaciones clínicas (organizadas por especialidad), acumular exámenes en una **canasta guardada en sesión** y obtener un cálculo de copago antes de confirmar un pre-agendamiento simulado. El personal autorizado administra el ciclo de vida de las prestaciones mediante un **panel operativo protegido** y un **Django Admin personalizado**.

### Pilares funcionales

1. **Catálogo público**: tarjetas Bootstrap, búsqueda multi-campo (`Q`), filtro por especialidad, ordenamiento y paginación (`Paginator`), ficha de detalle por *slug*.
2. **Canasta en sesión** (`request.session`): agregar, modificar cantidad, quitar y vaciar, con validación de cupos/estado, desglose económico (subtotal, bonificación, copago), *Context Processor* global para el contador del navbar y comprobante simulado que vacía la sesión.
3. **Backoffice protegido**: CRUD completo en el frontend (solo `is_staff`) y Django Admin con identidad corporativa.

## 2. Arquitectura

```
saludvital/
├── config/                  # settings (lee .env), urls, wsgi
├── catalogo/                # Especialidad, Prestacion, CRUD, canasta en sesión
│   ├── canasta.py           # lógica de la canasta (sesión) y cálculo de copago
│   ├── context_processors.py
│   ├── management/commands/poblar_datos.py
│   └── tests.py
├── cuentas/                 # Perfil (RUT, teléfono, rol, previsión), registro, login, logout
├── templates/               # base.html + plantillas de catalogo/ y cuentas/
├── static/css/style.css
├── requirements.txt
├── .env.example
└── .gitignore
```

### Modelo de datos

- **Especialidad**: `nombre` (único), `descripcion`, `icono`, `activa`.
- **Prestacion**: `especialidad` (**ForeignKey `on_delete=PROTECT`**), `codigo` (único), `slug` (único, automático), `nombre`, `descripcion`, `requisitos`, `arancel` (`MinValueValidator(0)`), `duracion_minutos` (`MinValueValidator(1)`), `cupos_diarios` (`MinValueValidator(0)`), `estado` (**choices**: Disponible, Suspendida, Sin cupos, En mantención), `imagen` (**ImageField**), `activo` (**baja lógica**).
- **Perfil** (1–1 con `User`): `rut` (validado con módulo 11), `telefono`, `rol` (Paciente, Administrativo, Profesional), `prevision`.

### Cálculo del copago

Cobertura referencial: Fonasa 60 %, Isapre 70 %, Particular 0 %.
`subtotal = arancel × cantidad` · `bonificación = subtotal × cobertura` · `copago = subtotal − bonificación`.
Las prestaciones de salud se consideran exentas de IVA.

## 3. Instalación paso a paso (Windows / PowerShell)

```powershell
# 1. Clonar el repositorio y entrar a la carpeta
git clone <URL_DEL_REPOSITORIO> saludvital
cd saludvital

# 2. Crear y activar el entorno virtual
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Variables de entorno
Copy-Item .env.example .env      # editar DJANGO_SECRET_KEY

# 5. Migraciones y datos iniciales
python manage.py migrate
python manage.py poblar_datos

# 6. Ejecutar
python manage.py runserver
```

En Linux/macOS: `source .venv/bin/activate` y `cp .env.example .env`.
Abrir <http://127.0.0.1:8000/> (admin en <http://127.0.0.1:8000/admin/>).

Pruebas automatizadas: `python manage.py test` (13 pruebas: modelos, catálogo, canasta, roles y registro).

## 4. Credenciales de prueba

| Usuario | Contraseña | Rol |
|---|---|---|
| `admin` | `Admin12345!` | Superusuario / personal (acceso a Gestión y Django Admin) |
| `paciente` | `Paciente12345!` | Paciente estándar (previsión Fonasa) |

> Credenciales solo para entorno de desarrollo.

## 5. Seguridad

- Secretos y configuración de BD en `.env` (no versionado) con `python-dotenv`; se incluye `.env.example`.
- `@login_required` + `@user_passes_test(is_staff)` en crear, editar, dar de baja y reactivar.
- `{% csrf_token %}` en todos los formularios POST; logout y acciones de canasta solo por POST (`require_POST`).
- Validación del parámetro `next` para evitar *open redirect*.
- Validaciones `clean_*` (código único, valores no negativos, tamaño de imagen) y validación de RUT.

## 6. Bitácora de uso de Inteligencia Artificial

Se usó un asistente de IA para generar el código base del proyecto a partir de las instrucciones de la evaluación. Los prompts de abajo corresponden a las consultas realizadas; el resultado fue revisado y probado antes de entregarse.

| N° | Área | Prompt utilizado | Respuesta técnica | Adaptación y revisión |
|---|---|---|---|---|
| 1 | Arquitectura | "Necesito realizar este trabajo completo" (adjuntando la pauta de la Evaluación Sumativa 3) y elección del tema: centro médico con canasta de exámenes y copago. | Estructura en dos apps (`catalogo` y `cuentas`), lógica de la canasta separada en `canasta.py` y *context processor* para el contador del navbar. | Se eligió el tema y la previsión como base del copago. Se verificó que cumpliera los módulos de la pauta. |
| 2 | ORM | Mismo requerimiento, módulo 1: modelos con relación, validadores, estados, imagen y baja lógica. | Modelos `Especialidad` y `Prestacion` con `ForeignKey(PROTECT)`, `MinValueValidator`, `choices`, `ImageField`, `activo` y `select_related` en las consultas. | Se revisaron los campos para el giro médico y se probó el comando `poblar_datos` y las migraciones. |
| 3 | Seguridad | Mismo requerimiento, módulo 4: autenticación, roles y CSRF. | Registro, login y logout (este último por POST), `@login_required`, `@user_passes_test(is_staff)`, `require_POST`, validación de RUT y del parámetro `next`. | Se ejecutaron las pruebas automáticas (13) que comprueban el acceso por rol y el flujo de sesión. |
## 7. Control de versiones

Repositorio Git con commits descriptivos por módulo (entorno, modelos, admin, CRUD, sesión/canasta, autenticación, documentación y pruebas).

## 8. Autor

Benjamín Rivas Bustos – Proyecto académico, Programación Back End (TI3041).
