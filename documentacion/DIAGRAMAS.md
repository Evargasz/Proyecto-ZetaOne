# Diagramas del Sistema ZetaOne

Este archivo contiene diagramas en formato Mermaid que pueden ser renderizados como imágenes.

## Cómo Convertir a Imágenes

### Opción 1: Mermaid Live Editor (Online)
1. Visita: https://mermaid.live/
2. Copia el código del diagrama
3. Pégalo en el editor
4. Click en "PNG" o "SVG" para descargar

### Opción 2: VS Code
1. Instala extensión: "Markdown Preview Mermaid Support"
2. Abre este archivo en VS Code
3. Click derecho en el diagrama → "Copy Mermaid Diagram as PNG"

### Opción 3: CLI (Requiere Node.js)
```bash
npm install -g @mermaid-js/mermaid-cli
mmdc -i diagrama.mmd -o diagrama.png
```

---

## 1. Arquitectura de Alto Nivel

```mermaid
graph TB
    subgraph Presentación
        A[PantallaInicio]
        B[Credenciales]
        C[Dashboard Admin]
        D[Dashboard Básico]
    end
    
    subgraph Lógica
        E[controladorVentanas]
        F[Handler Catalogación]
        G[Handler Validación]
        H[Handler Migración]
    end
    
    subgraph Datos
        I[(Sybase ASE)]
        J[(SQL Server)]
        K[Archivos JSON]
        L[Archivos .sp]
    end
    
    A --> E
    B --> E
    E --> C
    E --> D
    C --> F
    C --> G
    D --> H
    F --> I
    F --> J
    F --> L
    G --> I
    G --> K
    H --> I
    H --> J
```

**Guardar como:** `imagenes/arquitectura_alto_nivel.png`

---

## 2. Flujo de Validación

```mermaid
sequenceDiagram
    actor Usuario
    participant UI as Validación UI
    participant Thread as Worker Thread
    participant Handler as catalogacion.py
    participant BD as Base de Datos

    Usuario->>UI: Click "Validar"
    UI->>Thread: Iniciar worker
    
    loop Para cada archivo
        Thread->>Handler: obtener_fecha_desde_sp_help()
        Handler->>BD: SELECT crdate FROM sysobjects
        BD-->>Handler: Fecha compilación
        Handler-->>Thread: (fecha, bd_real)
        Thread->>UI: Callback actualizar progreso
        UI-->>Usuario: "Buscando en: cob_workflow"
    end
    
    Thread->>UI: Completado
    UI-->>Usuario: Mostrar resultados
```

**Guardar como:** `imagenes/flujo_validacion.png`

---

## 3. Flujo de Catalogación

```mermaid
sequenceDiagram
    actor Usuario
    participant UI as Validación Dialog
    participant Handler as catalogacion.py
    participant BD as Base de Datos
    participant Archivo as Sistema Archivos

    Usuario->>UI: Click "Ejecutar Catalogación"
    UI->>Handler: catalogar_plan_ejecucion()
    
    loop Para cada archivo
        Handler->>Archivo: Leer encabezado original
        Archivo-->>Handler: Comentarios
        
        Handler->>BD: EXEC sp_helptext 'sp_name'
        BD-->>Handler: Código compilado
        
        Handler->>Archivo: Guardar respaldo
        Handler->>Archivo: Guardar catalogado
        Archivo-->>Handler: OK
    end
    
    Handler-->>UI: Resultados
    UI-->>Usuario: Mostrar ventana de resultados
```

**Guardar como:** `imagenes/flujo_catalogacion.png`

---

## 4. Algoritmo de Búsqueda Inteligente

```mermaid
flowchart TD
    Start([Iniciar Búsqueda]) --> Direct{Probar BD<br/>especificada}
    Direct -->|Encontrado| ReturnDirect[Retornar fecha, None]
    Direct -->|No encontrado| Intelligent[Generar combinaciones<br/>inteligentes]
    
    Intelligent --> Loop1{Para cada<br/>combinación}
    Loop1 -->|Probar| Check1{¿Existe SP?}
    Check1 -->|Sí| ReturnSmart[Retornar fecha, bd_real]
    Check1 -->|No| Loop1
    Loop1 -->|Sin más| Exhaustive[Obtener todas<br/>las BDs del servidor]
    
    Exhaustive --> Loop2{Para cada BD}
    Loop2 -->|Probar| Check2{¿Existe SP?}
    Check2 -->|Sí| ReturnExh[Retornar fecha, bd_real]
    Check2 -->|No| Loop2
    Loop2 -->|Sin más| NotFound[Retornar None, None]
    
    ReturnDirect --> End([Fin])
    ReturnSmart --> End
    ReturnExh --> End
    NotFound --> End
    
    style Start fill:#e1f5e1
    style ReturnDirect fill:#90EE90
    style ReturnSmart fill:#90EE90
    style ReturnExh fill:#90EE90
    style NotFound fill:#ffcccc
    style End fill:#e1f5e1
```

**Guardar como:** `imagenes/algoritmo_busqueda_inteligente.png`

---

## 5. Componentes del Sistema

```mermaid
graph TB
    subgraph ZLauncher
        ZL[ZLauncher.py<br/>Punto de Entrada]
        CV[controladorVentanas<br/>Orquestador]
    end
    
    subgraph Admin[Usuario Administrador]
        UA[usu_admin_main.py<br/>Ventana Principal]
        VD[validacion_dialog.py<br/>Diálogo Validación]
        
        subgraph Handlers
            HC[catalogacion.py]
            HV[validacion.py]
            HR[repetidos.py]
        end
        
        subgraph Widgets
            AT[archivo_tree.py]
            AL[ambiente_list.py]
        end
    end
    
    subgraph Basico[Usuario Básico]
        UB[usu_basico_main.py<br/>Dashboard]
        MIG[Migracion.py]
        MOD[Modificaciones_varias.py]
        MT[migrar_tabla.py]
        MG[migrar_grupo.py]
    end
    
    subgraph Datos[Capa de Datos]
        SYB[(Sybase ASE)]
        SQL[(SQL Server)]
        JSON[Archivos JSON]
        SP[Archivos .sp]
    end
    
    ZL --> CV
    CV --> UA
    CV --> UB
    UA --> VD
    UA --> HC
    UA --> HV
    UA --> HR
    UA --> AT
    UA --> AL
    UB --> MIG
    UB --> MOD
    MIG --> MT
    MIG --> MG
    HC --> SYB
    HC --> SQL
    HC --> SP
    HV --> JSON
    MT --> SYB
    MG --> SYB
    MOD --> SYB
```

**Guardar como:** `imagenes/componentes_sistema.png`

---

## 6. Flujo de Migración de Grupo

```mermaid
flowchart TD
    Start([Iniciar Migración Grupo]) --> LoadCat[Leer catálogo JSON]
    LoadCat --> ShowVars[Mostrar variables<br/>requeridas]
    ShowVars --> InputVars[Usuario ingresa valores<br/>cod_oficina = 100]
    
    InputVars --> LoopTables{Para cada tabla}
    
    LoopTables --> ReplaceVars[Reemplazar :cod_oficina → 100<br/>en cláusula WHERE]
    ReplaceVars --> BuildQuery[Construir SELECT]
    BuildQuery --> ConnOrigen[Conectar a Origen]
    ConnOrigen --> ExecSelect[Ejecutar SELECT]
    
    ExecSelect --> FetchBatch{Fetch lote<br/>1000 filas}
    FetchBatch -->|Hay datos| ConnDest[Conectar a Destino]
    ConnDest --> ExecInsert[Ejecutar INSERT batch]
    ExecInsert --> Commit[COMMIT]
    Commit --> UpdateProg[Actualizar progreso]
    UpdateProg --> FetchBatch
    
    FetchBatch -->|Sin datos| NextTable[Siguiente tabla]
    NextTable --> LoopTables
    
    LoopTables -->|Completado| SaveHist[Guardar historial]
    SaveHist --> ShowResult[Mostrar resumen]
    ShowResult --> End([Fin])
    
    style Start fill:#e1f5e1
    style End fill:#e1f5e1
    style Commit fill:#90EE90
    style SaveHist fill:#87CEEB
```

**Guardar como:** `imagenes/flujo_migracion_grupo.png`

---

## 7. Modelo de Datos (Entidades)

```mermaid
erDiagram
    USUARIO ||--o{ AMBIENTE : usa
    USUARIO {
        string usuario PK
        string contrasena
        string rol
    }
    
    AMBIENTE ||--o{ ARCHIVO : valida
    AMBIENTE {
        string nombre PK
        string ip
        string puerto
        string usuario
        string clave
        string base
        string driver
    }
    
    ARCHIVO ||--o{ CATALOGO : pertenece_a
    ARCHIVO {
        string ruta PK
        string sp_name
        string bd_original
        string db_override
        string fecha_compilacion
        string estado
    }
    
    CATALOGO ||--|{ TABLA : contiene
    CATALOGO {
        string nombre PK
        string descripcion
        array variables
    }
    
    TABLA {
        string base
        string tabla
        string where
    }
```

**Guardar como:** `imagenes/modelo_datos.png`

---

## 8. Arquitectura de 3 Capas

```mermaid
graph TB
    subgraph Capa1[" CAPA DE PRESENTACIÓN "]
        direction LR
        UI1[PantallaInicio]
        UI2[Credenciales]
        UI3[Dashboard]
        UI4[Validación UI]
        UI5[Catalogación UI]
        UI6[Migración UI]
    end
    
    subgraph Capa2[" CAPA DE LÓGICA DE NEGOCIO "]
        direction LR
        CV[Controlador<br/>Ventanas]
        HC[Handler<br/>Catalogación]
        HV[Handler<br/>Validación]
        HM[Handler<br/>Migración]
        SU[Sybase<br/>Utils]
        FU[File<br/>Utils]
    end
    
    subgraph Capa3[" CAPA DE DATOS "]
        direction LR
        DB1[(Sybase<br/>ASE)]
        DB2[(SQL<br/>Server)]
        FS1[JSON]
        FS2[Archivos<br/>.sp]
    end
    
    Capa1 --> Capa2
    Capa2 --> Capa3
    
    style Capa1 fill:#e3f2fd
    style Capa2 fill:#fff3e0
    style Capa3 fill:#f1f8e9
```

**Guardar como:** `imagenes/arquitectura_3_capas.png`

---

## 9. Patrones de Diseño Utilizados

```mermaid
mindmap
  root((Patrones<br/>de Diseño))
    MVC
      Modelo: JSON, BD
      Vista: tkinter
      Controlador: handlers
    Observer
      Callbacks
      Progreso en tiempo real
      Actualización UI
    Strategy
      Búsqueda Directa
      Búsqueda Inteligente
      Búsqueda Exhaustiva
    Template Method
      Migración Base
      Migración Tabla
      Migración Grupo
    Singleton
      Configuración
      Una instancia
      Carga única
```

**Guardar como:** `imagenes/patrones_diseno.png`

---

## Uso en la Documentación

Reemplace los placeholders `[IMAGEN: descripción]` con:

```markdown
![Arquitectura de Alto Nivel](imagenes/arquitectura_alto_nivel.png)

![Flujo de Validación](imagenes/flujo_validacion.png)

![Algoritmo de Búsqueda Inteligente](imagenes/algoritmo_busqueda_inteligente.png)
```
