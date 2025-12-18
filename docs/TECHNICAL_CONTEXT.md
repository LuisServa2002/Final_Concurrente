# Proyecto Final - Programación Concurrente

## Contexto Técnico

Este documento describe la arquitectura y componentes del sistema distribuido de entrenamiento de redes neuronales.

---

## 1. OBJETIVO DEL PROYECTO

Sistema distribuido para entrenamiento y consumo de modelos de IA (redes neuronales) usando:
- **Entrenamiento distribuido** entre múltiples nodos worker (SUB_TRAIN)
- **Algoritmo RAFT** para consenso, replicación de logs y archivos .bin
- **4 lenguajes de programación**: Java (obligatorio para IA), Python, Go, Kotlin
- **Solo sockets nativos** (prohibido: frameworks web, WebSocket, RabbitMQ, etc.)
- **Persistencia RAFT** en disco (raft_state.json)

---

## 2. ARQUITECTURA

```
┌─────────────────┐     ┌─────────────────┐
│  train_client   │     │   test_client   │
│    (Python)     │     │    (Python)     │
└────────┬────────┘     └────────┬────────┘
         │ TCP/JSON              │ TCP/JSON
         ▼                       ▼
┌─────────────────────────────────────────┐
│           Worker Cluster (RAFT)         │
│  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │Worker Py │◄─┤►Worker Go│◄─┤►Kotlin │ │
│  │ :9000    │  │  :9001   │  │ :9002  │ │
│  │ (Líder)  │  │(Follower)│  │(Follower)│
│  └─────┬────┘  └────┬─────┘  └────┬───┘ │
│        │ SUB_TRAIN  │ SUB_TRAIN   │     │
│        └────────────┴─────────────┘     │
└─────────────────────────────────────────┘
         │
         ▼ subprocess
┌─────────────────┐
│ Java Training   │
│ Module (MLP)    │
└─────────────────┘
```

---

## 3. COMPONENTES IMPLEMENTADOS ✅

### 3.1 Red Neuronal (Java) ✅
- `java/NeuralNetwork.java` - MLP con sigmoid, backpropagation
- `java/TrainingModule.java` - CLI para train/predict/demo
- **Paralelización:** Fork/Join Pool con todos los cores
- UUID único por modelo, serialización nativa (.bin)

### 3.2 Worker Python ✅
- `src/worker.py` - Servidor TCP + HTTP monitor
- `src/raft.py` - Consenso RAFT completo
- **Entrenamiento distribuido:** Divide datos y envía SUB_TRAIN
- **Replicación .bin:** STORE_FILE vía RAFT
- **Persistencia:** raft_state.json

### 3.3 Worker Go ✅
- `go/main.go` - Servidor TCP, handlers, HTTP monitor
- `go/raft.go` - Consenso RAFT con goroutines
- **SUB_TRAIN:** Recibe chunks y entrena localmente
- **Replicación .bin:** applyCallback para STORE_FILE
- **Persistencia:** raft_state.json

### 3.4 Worker Kotlin ✅
- `kotlin/src/main/kotlin/Main.kt` - Servidor TCP, handlers, HTTP monitor  
- `kotlin/src/main/kotlin/Raft.kt` - Consenso RAFT
- **SUB_TRAIN:** Recibe chunks y entrena localmente
- **Replicación .bin:** applyCallback para STORE_FILE
- **Persistencia:** raft_state.json

### 3.5 Clientes Python ✅
- `src/train_client.py` - Envía TRAIN con inputs/outputs
- `src/test_client.py` - Envía PREDICT, LIST_MODELS

---

## 4. FLUJO DE ENTRENAMIENTO DISTRIBUIDO

```
1. Cliente → TRAIN al Líder (4 samples)
2. Líder divide: chunk0 (2), chunk1 (1), chunk2 (1)
3. Líder entrena chunk0 localmente
4. Líder → SUB_TRAIN chunk1 → Worker Go
5. Líder → SUB_TRAIN chunk2 → Worker Kotlin
6. Go y Kotlin entrenan sus chunks con Java
7. Retornan model paths al Líder
8. Líder agrega: entrena modelo final con 4 samples
9. Líder replica .bin vía RAFT (STORE_FILE)
10. Responde al cliente: {model_id: ...}
```

---

## 5. PROTOCOLO DE COMUNICACIÓN

### Cliente → Worker (TCP JSON + newline)
```json
{"type": "TRAIN", "inputs": [[0,0], [0,1]], "outputs": [[0], [1]]}
{"type": "PREDICT", "model_id": "abc123", "input": [1, 0]}
{"type": "LIST_MODELS"}
```

### Worker → Worker (SUB_TRAIN)
```json
{"type": "SUB_TRAIN", "chunk_id": 1, "inputs": [...], "outputs": [...]}
```

### RAFT RPCs (Worker ↔ Worker)
```json
{"type": "REQUEST_VOTE", "term": 5, "candidate_id": "node1"}
{"type": "APPEND_ENTRIES", "term": 5, "leader_id": ["host", port], "entries": [...]}
```

### RAFT Log Entry (STORE_FILE)
```json
{"action": "STORE_FILE", "filename": "model_xxx.bin", "data_b64": "..."}
```

---

## 6. PERSISTENCIA

### Archivos por nodo:
```
nodeX_storage/
├── models/
│   └── model_*.bin          # Modelos entrenados
├── raft_state.json          # Estado RAFT persistido
└── worker_XXXX.log          # Logs del worker
```

### raft_state.json:
```json
{
  "current_term": 5,
  "voted_for": "127.0.0.1:9000",
  "log": [...]
}
```

---

## 7. ARCHIVOS CLAVE

```
Final_Concurrente/
├── java/
│   ├── NeuralNetwork.java    # Red neuronal MLP
│   └── TrainingModule.java   # CLI de entrenamiento
├── go/
│   ├── main.go               # Worker Go
│   ├── raft.go               # RAFT Go
│   └── worker                # Binario compilado
├── kotlin/
│   ├── src/main/kotlin/
│   │   ├── Main.kt           # Worker Kotlin
│   │   └── Raft.kt           # RAFT Kotlin
│   └── worker.jar            # JAR compilado
├── src/
│   ├── raft.py               # RAFT Python
│   ├── worker.py             # Worker Python
│   ├── train_client.py       # Cliente entrenamiento
│   └── test_client.py        # Cliente testeo
└── docs/
    ├── CHECKLIST_PROYECTO.md # Estado del proyecto
    └── EXECUTION_FLOW.md     # Guía de ejecución
```

---

## 8. ESTADO DEL PROYECTO

### Completado ✅
- [x] Cluster heterogéneo (Python + Go + Kotlin)
- [x] Entrenamiento distribuido (SUB_TRAIN)
- [x] Replicación de archivos .bin vía RAFT
- [x] Persistencia RAFT en disco (3 lenguajes)
- [x] Benchmark 1000 requests (~51 req/s)
- [x] Predicciones XOR funcionando

### Pendiente (Opcional)
- [ ] Tests unitarios de RAFT
- [ ] Sincronización de nuevos nodos
- [ ] Compresión de modelos

---

## 9. RESTRICCIONES DEL EXAMEN

| Permitido | Prohibido |
|-----------|-----------|
| Sockets nativos | WebSocket, Socket.IO |
| Threads/concurrencia | Frameworks web |
| Librerías estándar | RabbitMQ, Redis |
| subprocess para Java | Contenedores como dependencia |

---

## 10. MÉTRICAS

| Métrica | Valor |
|---------|-------|
| Completitud | 98% |
| Benchmark | 51 req/s |
| Lenguajes | 4 (Java, Python, Go, Kotlin) |
| Persistencia | ✅ Implementada |
| Replicación .bin | ✅ Implementada |

---

**Última actualización:** 2025-12-18

