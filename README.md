# Proyecto Concurrente — Esqueleto

Estructura inicial con ejemplos de ejecución concurrente por fases.

Uso rápido:

1. Crear un entorno virtual e instalar dependencias:

```bash
python -m venv .venv
.
# Windows
.venv\Scripts\activate
pip install -r requirements.txt
```

2. Ejecutar en modo hilo:

```bash
python -m src.main --mode thread
```

3. Ejecutar en modo async:

```bash
python -m src.main --mode async
```

Pruebas:

```bash
pip install -r requirements.txt
pytest -q
```

Siguientes pasos: integrar reglas y límites del PDF `Final_cc4P1-252_v03.pdf`.

Implementación actual (resumen):

- `src/worker.py`: Servidor TCP que recibe archivos desde clientes, los almacena en `worker_storage/` y los replica a peers (solo sockets, sin frameworks). También levanta un monitor HTTP simple en `--monitor-port` para ver logs en `/logs`.
- `src/client.py`: Cliente CLI que sube archivos a un worker usando sockets.
- `java/TrainingModule.java`: Módulo de entrenamiento (simulador) compatible con JDK 8.
- `tools/benchmark.py`: Script para generar y subir 1000 archivos (configurable) y medir tiempo.

Compilar módulo Java:

```bash
cd java
javac TrainingModule.java
cd ..
```

Para ejecutar el worker y que corra el entrenamiento Java automáticamente, iniciar con `--run-train`:

```bash
python -m src.worker --host 127.0.0.1 --port 9000 --monitor-port 8000 --raft-port 10000 --peers 127.0.0.1:9001 127.0.0.1:9002 --run-train
```

Notas sobre reglas del enunciado:
- Solo se usan sockets y librerías estándar del lenguaje.
- El módulo de entrenamiento está en Java (mínimo JDK 8) como exige la consigna.
- Se utiliza hilos en los workers y en el benchmark para concurrencia.

Cómo arrancar tres workers (ejemplo local) con puertos Raft explícitos:

```bash
# worker 1 (expected leader candidate)
python -m src.worker --host 127.0.0.1 --port 9000 --monitor-port 8000 --raft-port 10000 --peers 127.0.0.1:9001 127.0.0.1:9002

# worker 2
python -m src.worker --host 127.0.0.1 --port 9001 --monitor-port 8001 --raft-port 10001 --peers 127.0.0.1:9000 127.0.0.1:9002

# worker 3
python -m src.worker --host 127.0.0.1 --port 9002 --monitor-port 8002 --raft-port 10002 --peers 127.0.0.1:9000 127.0.0.1:9001
```

Notes:
- The `--raft-port` argument specifies the port used by Raft RPCs for each node. Clients that send files to a non-leader worker will be redirected to the current leader's worker port.

Subir un archivo desde el cliente:

```bash
python -m src.client --host 127.0.0.1 --port 9000 put path/to/file.txt
```

Ver monitor del worker (logs):

Open http://127.0.0.1:8000/logs in a browser to see replication logs.

---

## 📚 Documentación Adicional

Para un análisis completo del proyecto, mejoras sugeridas y guías detalladas, consulta:

- **[Guía Completa de Ejecución](docs/GUIA_EJECUCION_COMPLETA.md)** - Guía paso a paso con 3 workers (Python, Go, Kotlin) e imágenes
- **[Flujo de Ejecución](docs/EXECUTION_FLOW.md)** - Flujo básico de ejecución
- **[Contexto Técnico](docs/TECHNICAL_CONTEXT.md)** - Arquitectura y diseño del sistema

## 🖼️ Entrenamiento con Imágenes

Para entrenar modelos usando imágenes reales:

```powershell
# Convertir imagen a vectores CSV
python tools\image_to_csv.py --image Fases.png --output inputs_img.csv outputs_img.csv

# Entrenar con los vectores generados
python -m src.train_client --host 127.0.0.1 --port 9000 train inputs_img.csv outputs_img.csv
```

Ver [Guía Completa de Ejecución](docs/GUIA_EJECUCION_COMPLETA.md) para más detalles.

