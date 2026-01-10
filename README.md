# Guía de uso: vine_config.py

## ¿Qué es vine_config.py?

`vine_config.py` es una herramienta para ajustar (fit) vine copulas usando estructuras predefinidas desde Chimera y datos de entrada. Permite procesar grandes cantidades de estructuras vine dividiendo el trabajo en "chunks" (fragmentos).

## Configuración inicial

### 1. Crear un archivo YAML de configuración

Crea un archivo YAML (ej: `mi_config.yaml`) con los siguientes parámetros:

```yaml
data_file: inputs/input7_500_gauss_high.txt  # Ruta al archivo de datos de entrada
chunk_size: 27000                             # Número de vines por chunk
output_dir: fit_results                       # Directorio donde se guardarán los resultados
```

**Parámetros opcionales:**
- `chimera_url`: URL del archivo Zarr de Chimera (por defecto: `https://geoocean.sci.unican.es/chimera/chimera.zarr`)

### 2. Preparar archivo de datos

Tu archivo de datos debe ser un `.txt` con una matriz donde:
- Cada fila = una observación
- Cada columna = una variable
- Valores separados por espacios o tabuladores

Ejemplo: `inputs/input7_500_gauss_high.txt` con 7 variables y 500 observaciones

## Uso básico

### Importar y cargar configuración

```python
from vine_config import VineConfig

# Cargar configuración desde YAML
config = VineConfig("mi_config.yaml")
```

### Métodos principales

#### 1. **Estimar tiempo de procesamiento**
Antes de procesar todos los chunks, estima cuánto tiempo tomará:

```python
tiempo_estimado = config.measure_fitting_time()
# Imprime: "Estimated time for full chunk (27000): X.XX minutes"
```

Este método ajusta 100 vines de prueba y proyecta el tiempo para un chunk completo.

#### 2. **Ajustar un chunk y guardar resultados**
Procesa un chunk específico y guarda los resultados en CSV:

```python
config.fit_vinecop_chunk_to_file(chunk_index=0)
# Guarda: fit_results/fit_chunk_0000_27000.csv
```

El archivo CSV contiene:
- `vine_id`: Identificador del vine
- `n_parameters`: Número de parámetros del modelo ajustado
- `aic`: Criterio de información de Akaike

#### 3. **Obtener información sobre chunks**

```python
# Total de matrices disponibles en Chimera
total_matrices = config.get_number_of_chimera_matrices()

# Número de chunks necesarios
n_chunks = config.get_number_of_chunks()

# ¿En qué chunk está una matriz específica?
chunk_id = config.get_id_chunk_from_matrix_id(15000)
```

#### 4. **Monitorear progreso**
Verifica qué chunks ya se han procesado:

```python
progreso = config.monitor_fitting_progress()
# Retorna: {0: 27000, 1: 27000, 2: 15000, ...}
# Donde la clave es el chunk_index y el valor es el número de vines procesados
```

#### 5. **Acceder a datos y matrices**

```python
# Cargar datos de entrada
datos = config.get_data_from_file()

# Cargar una matriz específica de Chimera
matriz = config.get_matrix_from_id(100)

# Cargar un rango de matrices
matrices = config.load_matrices_from_zarr(start=0, end=100)
```

## Workflow recomendado

### Paso 1: Configuración mínima para prueba
Crea `test.yaml`:
```yaml
data_file: inputs/input7_500_gauss_high.txt
chunk_size: 100
output_dir: test_results
```

### Paso 2: Estimar tiempo
```python
config = VineConfig("test.yaml")
config.measure_fitting_time()
```

### Paso 3: Procesar un chunk de prueba
```python
config.fit_vinecop_chunk_to_file(chunk_index=0)
```

### Paso 4: Ajustar chunk_size y escalar
Basándote en el tiempo estimado, ajusta `chunk_size` en tu YAML para producción:
```yaml
chunk_size: 27000  # Tamaño óptimo según tus recursos
```

### Paso 5: Procesar todos los chunks
```python
config = VineConfig("produccion.yaml")
n_chunks = config.get_number_of_chunks()

for chunk_id in range(n_chunks):
    config.fit_vinecop_chunk_to_file(chunk_id)
    print(f"Completado chunk {chunk_id}/{n_chunks}")
```

## Procesamiento paralelo (experimental)

El método `fit_vinecop_chunk_parallel()` está disponible pero requiere ajustes según tus necesidades:

```python
config.fit_vinecop_chunk_parallel()
```

Nota: Este método actualmente procesa 8 chunks en paralelo con 8 workers. Personaliza según tu hardware.

## Estructura de archivos de salida

Los resultados se guardan en formato CSV:
```
fit_results/
├── fit_chunk_0000_27000.csv
├── fit_chunk_0001_27000.csv
├── fit_chunk_0002_27000.csv
└── ...
```

Formato del CSV:
```
vine_id,n_parameters,aic
0,21,1234.567890
1,18,1156.234567
...
```

## Configuración avanzada

El ajuste de vine copulas usa estos parámetros por defecto:
- `family_set`: Familias con un parámetro (`pv.one_par`)
- `selection_criterion`: AIC (Akaike Information Criterion)
- `parametric_method`: MLE (Maximum Likelihood Estimation)

Para modificar estos parámetros, edita el método `_fit_vinecop_chunk_internal()` en `vine_config.py`.

## Solución de problemas

- **Error "Data file not found"**: Verifica que la ruta en `data_file` sea correcta
- **Tiempo excesivo**: Reduce `chunk_size` para chunks más pequeños
- **Memoria insuficiente**: Reduce `chunk_size` o procesa menos vines por chunk

---

## Resumen de métodos disponibles

| Método | Descripción |
|--------|-------------|
| `measure_fitting_time()` | Estima el tiempo de procesamiento para un chunk completo |
| `fit_vinecop_chunk_to_file(chunk_index)` | Ajusta un chunk y guarda resultados en CSV |
| `fit_vinecop_chunk(chunk_index)` | Ajusta un chunk y retorna resultados (sin guardar) |
| `get_number_of_chimera_matrices()` | Obtiene el total de matrices disponibles |
| `get_number_of_chunks()` | Calcula el número de chunks necesarios |
| `load_matrices_from_zarr(start, end)` | Carga un rango de matrices desde Chimera |
| `get_matrix_from_id(matrix_id)` | Obtiene una matriz específica por ID |
| `get_data_from_file()` | Carga los datos de entrada |
| `get_id_chunk_from_matrix_id(matrix_id)` | Obtiene el chunk que contiene una matriz |
| `monitor_fitting_progress()` | Muestra el progreso de chunks procesados |
| `fit_vinecop_chunk_parallel()` | Procesa múltiples chunks en paralelo (experimental) |

---

¿Necesitas ayuda con algún aspecto específico del uso de `vine_config.py`?
