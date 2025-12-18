# Guía Completa de Ejecución - Sistema Distribuido con 3 Workers Heterogéneos

Esta guía explica cómo ejecutar el sistema completo con **3 workers en diferentes lenguajes** (Python, Go, Kotlin) y cómo entrenar modelos usando **imágenes reales**.

---

## Tabla de Contenidos

1. [Preparación del Entorno](#preparación-del-entorno)
2. [Compilación de Componentes](#compilación-de-componentes)
3. [Ejecución de Workers](#ejecución-de-workers)
4. [Entrenamiento con Imágenes](#entrenamiento-con-imágenes)
5. [Consumo de Modelos](#consumo-de-modelos)
6. [Monitoreo y Verificación](#monitoreo-y-verificación)

---

## 1. Preparación del Entorno

### 1.1. Requisitos Previos

- Python 3.8+ (con venv activado)
- Java JDK 8+ (`java` y `javac` en PATH)
- Go 1.18+ (`go` en PATH)
- Kotlin (`kotlinc` en PATH) o usar el JAR compilado

### 1.2. Instalar Dependencias Python

```powershell
# En la raíz del proyecto
cd C:\Users\luisa\Desktop\UNI\7-CICLO\Concurrente\Laboratorios\Final

# Activar entorno virtual
.\.venv\Scripts\Activate.ps1

# Instalar dependencias básicas
pip install -r requirements.txt

# Instalar librerías para procesamiento de imágenes (opcional, para el script de conversión)
pip install pillow numpy
```

---

## 2. Compilación de Componentes

### 2.1. Compilar Módulo Java (OBLIGATORIO)

```powershell
cd java
javac TrainingModule.java NeuralNetwork.java
cd ..
```

**Verificar:**
```powershell
java -cp java TrainingModule demo
# Debe ejecutar la demo XOR sin errores
```

### 2.2. Compilar Worker Go

```powershell
cd go
go build -o worker.exe .
cd ..
```

**Verificar:**
```powershell
.\go\worker.exe --help
# Debe mostrar la ayuda del comando
```

### 2.3. Compilar Worker Kotlin

**Opción A: Compilar con kotlinc**
```powershell
cd kotlin
kotlinc src\main\kotlin\*.kt -include-runtime -d worker.jar
cd ..
```

**Opción B: Usar JAR ya compilado**
Si ya existe `kotlin\worker.jar`, puedes usarlo directamente.

**Verificar:**
```powershell
java -jar kotlin\worker.jar --help
# Debe mostrar información del worker
```

---

## 3. Ejecución de Workers

### 3.1. Configuración de Puertos

| Worker | Lenguaje | Puerto TCP | Puerto Monitor | Puerto RAFT |
|--------|----------|------------|----------------|--------------|
| Nodo 0 | Python   | 9000       | 8000           | 10000        |
| Nodo 1 | Go       | 9001       | 8001           | 10001        |
| Nodo 2 | Kotlin   | 9002       | 8002           | 10002        |

### 3.2. Iniciar Workers (3 Terminales Separadas)

**Terminal 1 - Worker Python (Nodo 0):**
```powershell
python -m src.worker --host 127.0.0.1 --port 9000 --monitor-port 8000 --raft-port 10000 --peers 127.0.0.1:9001 127.0.0.1:9002 --storage-dir node0_storage --java-dir java
```

**Terminal 2 - Worker Go (Nodo 1):**
```powershell
.\go\worker.exe --host 127.0.0.1 --port 9001 --monitor-port 8001 --raft-port 10001 --peers 127.0.0.1:9000,127.0.0.1:9002 --storage-dir node1_storage --java-dir java
```

**Terminal 3 - Worker Kotlin (Nodo 2):**
```powershell
java -jar kotlin\worker.jar --host 127.0.0.1 --port 9002 --monitor-port 8002 --raft-port 10002 --peers 127.0.0.1:9000,127.0.0.1:9001 --storage-dir node2_storage --java-dir java
```

**Nota:** 
- Python usa espacios para separar peers: `--peers 127.0.0.1:9001 127.0.0.1:9002`
- Go y Kotlin usan comas: `--peers 127.0.0.1:9000,127.0.0.1:9002`

### 3.3. Verificar que los Workers Están Activos

Espera **5-10 segundos** para que Raft elija un líder. Luego:

**Abrir monitores web:**
- Nodo 0 (Python): http://127.0.0.1:8000/
- Nodo 1 (Go): http://127.0.0.1:8001/
- Nodo 2 (Kotlin): http://127.0.0.1:8002/

**Verificar estado RAFT:**
```powershell
# Ver estado del nodo Python
curl http://127.0.0.1:8000/status

# Ver estado del nodo Go
curl http://127.0.0.1:8001/status

# Ver estado del nodo Kotlin
curl http://127.0.0.1:8002/status
```

Debes ver que **uno de los nodos es `leader`** y los otros son `follower`.

---

## 4. Entrenamiento con Imágenes

### 4.1. Preparar Imágenes para Entrenamiento

**Opción A: Usar una imagen existente (ej: Fases.png)**

```powershell
# Convertir Fases.png a vectores CSV
python tools\image_to_csv.py --image Fases.png --output inputs_img.csv outputs_img.csv
```

**Opción B: Usar múltiples imágenes de un directorio**

```powershell
# Crear directorio con imágenes de ejemplo
mkdir images
# Copiar algunas imágenes PNG/JPG a ./images/

# Convertir todas las imágenes
python tools\image_to_csv.py --input-dir images --output inputs_img.csv outputs_img.csv
```

**Opción C: Entrenamiento rápido con datos numéricos (sin imágenes)**

```powershell
# Entrenar directamente con datos inline (ejemplo XOR)
python -m src.train_client --host 127.0.0.1 --port 9000 train-inline "0,0;0,1;1,0;1,1" "0;1;1;0"
```

### 4.2. Entrenar Modelo con CSV de Imágenes

```powershell
python -m src.train_client --host 127.0.0.1 --port 9000 train inputs_img.csv outputs_img.csv
```

**Qué ocurre internamente:**

1. **Cliente envía datos al worker** (puede ser cualquier nodo)
2. **Si no es líder, redirección automática** al líder
3. **Líder detecta múltiples nodos** → activa entrenamiento distribuido
4. **División de datos:**
   - Líder entrena chunk 0 localmente
   - Envía chunk 1 al worker Go (puerto 9001)
   - Envía chunk 2 al worker Kotlin (puerto 9002)
5. **Cada worker entrena en paralelo:**
   - Python: ejecuta `java TrainingModule train ...`
   - Go: ejecuta `java TrainingModule train ...`
   - Kotlin: ejecuta `java TrainingModule train ...`
6. **Agregación:** Líder entrena modelo final con todos los datos
7. **Replicación:** Modelo `.bin` se replica vía Raft a todos los nodos

**Salida esperada:**
```
Training complete!
Model ID: 09736bce
```

### 4.3. Verificar Modelos Entrenados

**En disco:**
```powershell
# Ver modelos en cada nodo
dir node0_storage\models\*.bin
dir node1_storage\models\*.bin
dir node2_storage\models\*.bin
```

**Con cliente:**
```powershell
python -m src.test_client --host 127.0.0.1 --port 9000 list
```

**En monitores web:**
- Abrir http://127.0.0.1:8000/models (o :8001, :8002)
- Debe mostrar lista de modelos en JSON

---

## 5. Consumo de Modelos

### 5.1. Listar Modelos Disponibles

```powershell
python -m src.test_client --host 127.0.0.1 --port 9000 list
```

**Salida esperada:**
```
Available models (2):
  - 09736bce
  - 01ffd72d_chunk0
```

### 5.2. Hacer Predicción

**Con datos numéricos (ejemplo XOR):**
```powershell
python -m src.test_client --host 127.0.0.1 --port 9000 predict 09736bce 0,1
```

**Con vector de imagen (mismo formato que entrenaste):**
```powershell
# Primero convierte la imagen a vector
python tools\image_to_csv.py --image nueva_imagen.png --output test_input.csv test_output.csv

# Extrae el vector de la primera línea (o usa el formato inline)
# Ejemplo: si test_input.csv tiene "0.0,0.1,0.9,..."
python -m src.test_client --host 127.0.0.1 --port 9000 predict 09736bce 0.0,0.1,0.9,...
```

**Qué ocurre internamente:**

1. Cliente envía `PREDICT` con `model_id` y `input` vector
2. Si el worker no es líder → redirección al líder
3. Líder busca modelo `.bin` en su `models/`
4. Ejecuta: `java -cp java TrainingModule predict model_<id>.bin "0.0,0.1,..."`
5. Java carga modelo, hace forward pass, devuelve `PREDICTION:...`
6. Worker parsea y devuelve `{'status':'OK','output':[...]}`

**Salida esperada:**
```
Prediction: [0.523456]
```

---

## 6. Monitoreo y Verificación

### 6.1. Monitores Web

**Dashboard principal:**
- Python: http://127.0.0.1:8000/
- Go: http://127.0.0.1:8001/
- Kotlin: http://127.0.0.1:8002/

**Endpoints JSON:**
- Estado RAFT: http://127.0.0.1:8000/status
- Lista de modelos: http://127.0.0.1:8000/models
- Logs: http://127.0.0.1:8000/logs

### 6.2. Verificar Replicación de Modelos

**Comando PowerShell:**
```powershell
# Verificar que todos los nodos tienen el mismo modelo
Get-ChildItem node0_storage\models\*.bin | Select-Object Name, Length
Get-ChildItem node1_storage\models\*.bin | Select-Object Name, Length
Get-ChildItem node2_storage\models\*.bin | Select-Object Name, Length
```

**Debe mostrar:** Los mismos archivos `.bin` en los 3 nodos (mismo nombre y tamaño).

### 6.3. Verificar Entrenamiento Distribuido

**Revisar logs de cada worker:**

**Nodo 0 (Python):**
```powershell
Get-Content node0_storage\worker.log -Tail 20
```

**Buscar líneas como:**
```
Starting DISTRIBUTED training across 3 nodes
Chunk 0: samples 0-2 (3 total)
Sending SUB_TRAIN to peer 127.0.0.1:9001, chunk 1, 2 samples
Sending SUB_TRAIN to peer 127.0.0.1:9002, chunk 2, 2 samples
Distributed training complete: 3 partial models
RAFT applied STORE_FILE: wrote node0_storage/models/model_...bin
```

**Nodo 1 (Go):**
```powershell
Get-Content node1_storage\worker.log -Tail 20
```

**Buscar:**
```
SUB_TRAIN request: chunk 1, 2 samples
Chunk 1: Training successful
```

**Nodo 2 (Kotlin):**
```powershell
Get-Content node2_storage\worker.log -Tail 20
```

**Buscar:**
```
SUB_TRAIN request: chunk 2, 2 samples
Chunk 2: Training successful
```

---

## 7. Flujo Completo Resumido

### Diagrama de Flujo

```
1. PREPARACIÓN
   ├─ Compilar Java (TrainingModule)
   ├─ Compilar Go worker
   └─ Compilar Kotlin worker

2. INICIO DE CLUSTER
   ├─ Terminal 1: Worker Python (puerto 9000)
   ├─ Terminal 2: Worker Go (puerto 9001)
   └─ Terminal 3: Worker Kotlin (puerto 9002)
   
   → Esperar 5-10s para elección de líder Raft

3. ENTRENAMIENTO (Fase 1)
   ├─ Cliente → Worker (cualquiera)
   ├─ Si no es líder → REDIRECT al líder
   ├─ Líder divide datos en 3 chunks
   ├─ Chunk 0 → Entrenado en Python (líder)
   ├─ Chunk 1 → Enviado a Go → Entrenado
   ├─ Chunk 2 → Enviado a Kotlin → Entrenado
   ├─ Líder agrega resultados → Modelo final
   └─ Modelo replicado vía Raft → Todos los nodos

4. CONSUMO (Fase 2)
   ├─ Cliente → LIST_MODELS → Ver modelos disponibles
   ├─ Cliente → PREDICT (model_id, input_vector)
   ├─ Si no es líder → REDIRECT
   ├─ Líder carga modelo .bin
   ├─ Ejecuta Java TrainingModule predict
   └─ Devuelve predicción al cliente

5. MONITOREO
   ├─ Dashboard web: http://127.0.0.1:8000/
   ├─ Estado RAFT: /status
   ├─ Modelos: /models
   └─ Logs: /logs
```

---

## 8. Solución de Problemas

### Error: "No leader available"
- **Causa:** Los workers aún no han elegido líder
- **Solución:** Esperar 5-10 segundos más

### Error: "Model not found"
- **Causa:** El modelo no se replicó correctamente
- **Solución:** Verificar logs de Raft, asegurar que hay mayoría de nodos activos

### Error: "Connection refused" al iniciar Go/Kotlin
- **Causa:** Puerto ya en uso o comando incorrecto
- **Solución:** Verificar que no hay otro proceso usando los puertos, revisar sintaxis de comandos

### Los modelos no aparecen en todos los nodos
- **Causa:** Replicación Raft falló
- **Solución:** Verificar que todos los nodos están conectados, revisar logs de Raft

---

## 9. Ejemplo Completo de Sesión

```powershell
# === PREPARACIÓN ===
cd C:\Users\luisa\Desktop\UNI\7-CICLO\Concurrente\Laboratorios\Final
.\.venv\Scripts\Activate.ps1

cd java
javac *.java
cd ..

cd go
go build -o worker.exe .
cd ..

# === INICIAR WORKERS (3 terminales) ===
# Terminal 1:
python -m src.worker --host 127.0.0.1 --port 9000 --monitor-port 8000 --raft-port 10000 --peers 127.0.0.1:9001 127.0.0.1:9002 --storage-dir node0_storage --java-dir java

# Terminal 2:
.\go\worker.exe --host 127.0.0.1 --port 9001 --monitor-port 8001 --raft-port 10001 --peers 127.0.0.1:9000,127.0.0.1:9002 --storage-dir node1_storage --java-dir java

# Terminal 3:
java -jar kotlin\worker.jar --host 127.0.0.1 --port 9002 --monitor-port 8002 --raft-port 10002 --peers 127.0.0.1:9000,127.0.0.1:9001 --storage-dir node2_storage --java-dir java

# === ENTRENAR CON IMAGEN ===
# Terminal 4 (nueva):
python tools\image_to_csv.py --image Fases.png --output inputs_img.csv outputs_img.csv
python -m src.train_client --host 127.0.0.1 --port 9000 train inputs_img.csv outputs_img.csv

# === CONSUMIR MODELO ===
python -m src.test_client --host 127.0.0.1 --port 9000 list
python -m src.test_client --host 127.0.0.1 --port 9000 predict <model_id> 0.0,0.1,0.2,...
```

---

**Última actualización:** Guía completa para ejecución con 3 workers heterogéneos

