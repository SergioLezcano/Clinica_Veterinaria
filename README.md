# - Sistema de Gestión para Clínica Veterinaria

## Descripción

Sistema web desarrollado como proyecto académico para la administración integral de una clínica veterinaria.

El sistema permite gestionar el flujo de atención de pacientes, historias clínicas, operadores, reportes y procesos administrativos mediante una interfaz web desarrollada con Django.

---


# Objetivos

* Gestionar la atención clínica de mascotas.
* Registrar propietarios y pacientes.
* Administrar historias clínicas.
* Gestionar operadores y médicos veterinarios.
* Obtener reportes estadísticos.
* Centralizar la información de la clínica.

---

# Funcionalidades

### Inicio de sesión

* Autenticación de usuarios.
* Roles diferenciados.
* Redirección automática según permisos.

### Administración

* Panel administrativo.
* Gestión de operadores.
* Gestión del personal.

### Recepción y Operación

* Registro de dueños.
* Registro de mascotas.
* Preconsulta y derivación médica.
* Gestión de Turnos y Citas con Calendario interactivo (FullCalendar).
* Check-in de citas en 1 clic con derivación automática a la Sala de Espera del médico.
* Envío automatizado de confirmaciones por correo electrónico a los propietarios.
* Cobro y facturación de consultas y productos.

### Atención médica

* Historia clínica.
* Evolución del paciente.
* Registro de consultas y recetas.

### Reportes

* Consultas realizadas.
* Estadísticas generales.
* Información administrativa.

---

# Tecnologías utilizadas

## Backend

* Python 3.12 / 3.13
* Django 4.2 LTS
* MariaDB / MySQL (compatible con MariaDB 10.4.32+)

## Dependencias principales

* Django
* mysqlclient
* asgiref
* sqlparse
* tzdata
* django-anymail[resend] (Comunicación transaccional HTTPS para Render)

---

# Estructura del proyecto

```
Clinica_Veterinaria/
│
├── clinica_veterinaria_proyecto/
├── gestion_veterinaria/
├── pagos/
├── productos/
├── turnos/
│   ├── migrations/
│   ├── services/
│   │   └── turno_service.py
│   ├── templates/turnos/
│   ├── forms.py
│   ├── models.py
│   ├── urls.py
│   └── views.py
│
├── manage.py
├── requirements.txt
└── README.md
```

---

# Instalación

## 1. Clonar el repositorio

```bash
git clone https://github.com/SergioLezcano/Clinica_Veterinaria.git
```

## 2. Crear entorno virtual

```bash
python -m venv venv
```

## 3. Activar entorno

Windows

```bash
venv\Scripts\activate
```

Linux / macOS

```bash
source venv/bin/activate
```

## 4. Instalar dependencias

```bash
pip install -r requirements.txt
```

## 5. Configurar la base de datos

Crear una base de datos MySQL:

```
clinica_veterinaria
```

Editar `settings.py` con las credenciales locales de MySQL.

## 6. Ejecutar migraciones

```bash
python manage.py migrate
```

## 7. Crear un usuario administrador

```bash
python manage.py createsuperuser
```

## 8. Ejecutar el servidor

```bash
python manage.py runserver
```

---

# Roles del sistema

## Administrador

* Gestión de operadores.
* Reportes.
* Historias clínicas.
* Sala de espera.

## Operador

* Registro de dueños.
* Registro de mascotas.
* Preconsulta.
* Agenda y asignación de Turnos con calendario.
* Facturación.

---

# Configuración de Correo Electrónico (Render & Local)

El sistema soporta envío híbrido de correos electrónicos transaccionales:

### 1. Entorno de Desarrollo Local
Por defecto (si la variable `RESEND_API_KEY` no está configurada), Django utiliza el backend de consola:
```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```
Todos los correos electrónicos generados al confirmar un turno se imprimen formateados directamente en la terminal, permitiendo probar sin necesidad de credenciales ni internet.

### 2. Despliegue en Render (Cloud)
Render bloquea las conexiones salientes por los puertos SMTP estándar (puertos 25, 465 y 587). Para evitar bloqueos, el sistema implementa **`django-anymail`** conectado a la API HTTPS (puerto 443) de **[Resend](https://resend.com/)**.

Para activarlo en el panel de **Environment Variables** en Render, simplemente agregue:
```env
RESEND_API_KEY=re_tu_api_key_de_resend
DEFAULT_FROM_EMAIL=Clínica Veterinaria <turnos@tudominio.com>
```
Al detectar `RESEND_API_KEY`, Django conmuta automáticamente a:
```python
EMAIL_BACKEND = 'anymail.backends.resend.EmailBackend'
```

---

# Flujo general

```
Login

↓

Administrador
│
├── Sala de espera
├── Historias clínicas
├── Reportes
├── Agenda de turnos
└── Gestión de operadores

Operador
│
├── 1. Nuevo dueño
├── 2. Nueva mascota
├── 3. Preconsulta
├── 4. Módulo Caja / Facturación
└── 5. Gestión de Turnos (Calendario + Notificación Email)
```

---

# Estado del proyecto

Proyecto académico en desarrollo.

Actualmente se encuentra en proceso de mejora de:

* identidad visual;
* experiencia de usuario (UX);
* diseño de interfaz (UI);
* organización del código;
* documentación.

---

# Equipo de desarrollo

* Sergio Lezcano
* Oscar Roth

---

# Licencia

Proyecto desarrollado con fines académicos.
