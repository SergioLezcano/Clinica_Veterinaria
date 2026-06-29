# 🩺 VetHub - Sistema de Gestión para Clínica Veterinaria

## Descripción

VetHub es un sistema web desarrollado como proyecto académico para la administración integral de una clínica veterinaria.

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

### Recepción

* Registro de dueños.
* Registro de mascotas.
* Preconsulta.
* Sala de espera.

### Atención médica

* Historia clínica.
* Evolución del paciente.
* Registro de consultas.

### Reportes

* Consultas realizadas.
* Estadísticas generales.
* Información administrativa.

---

# Tecnologías utilizadas

## Backend

* Python 3.12
* Django 4.2
* MySQL

## Dependencias principales

* Django
* mysqlclient
* asgiref
* sqlparse
* tzdata

---

# Estructura del proyecto

```
Clinica_Veterinaria/

│
├── clinica_veterinaria_proyecto/
├── gestion_veterinaria/
├── pagos/
├── productos/
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
* Facturación.

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
└── Gestión de operadores

Operador
│
├── Nuevo dueño
├── Nueva mascota
├── Preconsulta
└── Caja
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
