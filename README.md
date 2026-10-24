# Salarios, inflación e IRPF en España · Trabajo Práctico 08MBID

Repositorio del Trabajo Práctico de la asignatura **08MBID · Visualización de Datos** (máster). Contiene los datos originales, el cuaderno que los prepara, el modelo fiscal y las imágenes de los gráficos del reportaje.

[![Abrir en Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/sortaria24-max/08MBID_TrabajoPractico/blob/main/notebooks/TP_08MBID_preparacion_datos.ipynb)

## Cómo está organizado

| Carpeta | Contenido |
|---|---|
| `data/raw/` | Tablas originales tal como se descargaron del INE y de la AEAT, sin modificar. |
| `data/processed/` | Tablas de trabajo que genera el cuaderno. Son las que usan los gráficos. |
| `notebooks/` | Cuaderno de Colab que explica la selección, limpieza y transformación de los datos. |
| `src/` | `modelo_fiscal.py`: cálculo de Seguridad Social e IRPF de un asalariado, con 8 pruebas. |
| `imagenes/` | Capturas de los gráficos del reportaje. |

## Cómo repetir el proceso
Abre el cuaderno en Colab (botón de arriba) y ejecuta todas las celdas. El cuaderno descarga este repositorio, lee `data/raw` y vuelve a escribir `data/processed`.

## Fuentes de los datos
| Archivo en `data/raw` | Origen |
|---|---|
| `Salario_anual.csv` | INE · Encuesta Anual de Estructura Salarial (EAES). Media, mediana y percentiles por comunidad. [Tabla 28191](https://www.ine.es/jaxiT3/Datos.htm?t=28191) |
| `Distribucion_salarial_tramos.csv` | INE · EAES. Trabajadores por múltiplos del SMI. [Tabla 28182](https://www.ine.es/jaxiT3/Datos.htm?t=28182) |
| `IPC.csv` | INE · Índice de Precios de Consumo, base 2021, índice general por comunidad. [Tabla 50913](https://www.ine.es/jaxiT3/Tabla.htm?t=50913) |
| `modelo100.csv` y `AyudaCSV_AnuarioTotal.pdf` | Agencia Tributaria · Anuario estadístico, [descarga masiva de datos](https://sede.agenciatributaria.gob.es/Sede/estadisticas/anuario-estadistico/acceso-descarga-masiva-datos.html). Declaraciones del IRPF (Modelo 100). |

## Notas de método
- **Ambos sexos.** Usamos siempre el total: el reportaje habla de personas que cobran un sueldo.
- **Jornadas.** La tabla de salarios incluye todas las jornadas; el INE no permite separar la parcial en ella.
- **Modelo fiscal.** Es una estimación sobre un asalariado tipo (régimen general, sin deducciones personales). No incluye País Vasco ni Navarra (regímenes forales). Supuestos y límites, en el cuaderno (paso 7) y en el código.
- **Modelo 100.** Sirve solo para contrastar la tendencia del tipo medio; no incluye regímenes forales ni Ceuta y Melilla.

## Autoría
Trabajo realizado por sortaria24-max para la asignatura 08MBID. Los datos pertenecen a sus organismos de origen (INE, AEAT).
