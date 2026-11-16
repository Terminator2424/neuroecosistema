# NeuroEcosistema: contexto completo para continuar y terminar el proyecto

Fecha del traspaso: 16 de noviembre de 2026.
Autor del proyecto: Edison Javier Gonzalez Velosa, trabaja solo, estudiante de Ingeniería de Sistemas, Universidad Santo Tomás, Seccional Tunja.

## 0. Instrucciones para Kiro

Eres quien continúa y termina este proyecto. Lee todo este documento antes de actuar. No rehagas lo que ya está hecho: verifica el estado (sección 11) y continúa con los pendientes (sección 10). No inventes resultados: toda cifra del informe debe salir de los archivos de results/ y models/. Este documento describe el trabajo hecho hasta ahora con un asistente de IA (Claude, de Anthropic) bajo dirección de Edison; el código existe, está probado y funciona, pero Edison necesita entenderlo para sustentarlo, así que explica siempre lo que hagas.

## 1. Cómo trabajar con Edison (preferencias que él mismo declaró)

- Idioma: español. Él escribe informal, en español colombiano. Respuestas directas, honestas, sin sobreexplicar. Si algo es incorrecto, lo dice y espera que lo corrijas sin rodeos.
- No dejarlo esperando en silencio: ya se frustró por una espera de horas. Si algo toma tiempo, avisa en pocas palabras qué estás haciendo y sigue.
- Código: entregarlo como comandos de PowerShell que crean los archivos desde la terminal de VS Code (no como archivos sueltos para copiar a mano). Convención usada hasta ahora: una función Write-File que escribe en UTF-8 sin BOM, archivos completos (no fragmentos), un primer renglón con throw si no se está en la raíz del proyecto, y cambios sobre archivos existentes de forma idempotente. En PowerShell la continuación de línea es el acento grave, no el signo ^; es mejor dar los comandos en una sola línea.
- Documentos académicos (informe, talleres): normas APA, Times New Roman 12, sin líneas divisorias decorativas, negrilla y cursiva solo en los títulos, títulos sin tamaño grande, portada muy bien cuidada. Si falta contexto, avisarle.
- Estadística: quiere el desarrollo completo paso a paso, listo para notebook, no solo la respuesta final.
- Prefiere archivos completos y listos para pegar, adaptados a lo que pide el profesor o la rúbrica.
- Modelos 3D: él se ofreció a buscar modelos 3D. Se decidió que NO entran en el núcleo porque no suman puntos en la rúbrica (la simulación pedida es 2D). Solo como extra al final si sobra tiempo.
- Quiere ir paso a paso y entender todo, porque la sustentación y el dominio individual son clave.
- PEDIDO EXPLÍCITO PARA EL FINAL: cuando el programa esté terminado, un documento que explique cada frase del código y todo lo que pueda tener que explicar, para demostrarle al profesor que hizo el código y entendió el tema (ver pendiente P10).

## 2. El encargo (propuesta del profesor)

Documento: Propuesta de Proyecto Final Integrador NeuroEcosistema, Tunja, 8 de noviembre de 2026. Espacio académico: Electiva I de Profundización, Inteligencia Artificial. Docente: Diego Alejandro Vela Beltrán. Facultad de Ingeniería de Sistemas.

Pregunta orientadora: en qué condiciones los agentes controlados por redes neuronales desarrollan comportamientos de búsqueda, persecución y evasión que mejoran su desempeño frente a estrategias sin aprendizaje.

Alcance mínimo (cada fila debe ser verificable):

| Componente | Requisito |
|------------|-----------|
| Entorno | Simulación 2D con alimento, presas, depredadores, consumo de energía, reglas de movimiento, captura y finalización de episodios |
| Agentes | Dos tipos con objetivos diferenciados; las decisiones de movimiento las generan efectivamente redes neuronales |
| Redes | Una arquitectura multicapa por especie, al menos dos capas ocultas; entradas, salidas, activaciones y parámetros documentados |
| Entrenamiento | Procedimiento real (neuroevolución o supervisado); evidencia de cambios en los parámetros |
| Experimentación | Comparar al menos dos configuraciones y un agente neuronal contra una referencia aleatoria o por reglas |
| Visualización | Ejecución observable, estadísticas y consulta de decisiones o variables relevantes de los agentes |
| Reproducibilidad | Código ejecutable, dependencias, instrucciones de instalación, semillas y registro de configuraciones |

Evaluación obligatoria: al menos tres escenarios (a) recursos suficientes y pocos depredadores, (b) escasez de alimento, (c) más presión de depredación u obstáculos. Varias ejecuciones con semillas registradas y condiciones comparables. Métricas: supervivencia media de presas, alimento consumido, capturas, energía final, tiempo hasta captura y variabilidad entre repeticiones. No se exige que la red sea superior siempre, pero las conclusiones deben coincidir con los datos. Mínimo: una comparación antes y después del entrenamiento, una entre dos arquitecturas o configuraciones y una contra un agente de referencia; cada una con hipótesis, variables controladas, tabla o gráfica, análisis y conclusión.

Decisiones que deben justificar (bitácora): representación del entorno, diseño de las redes, aprendizaje (qué se optimiza y qué comportamientos podría favorecer indebidamente), diseño experimental, interpretación (qué contradice las expectativas) y mejora (qué modificarían primero y con qué evidencia).

Productos de entrega:

1. Repositorio GitHub con código, README, instrucciones y dependencias.
2. Aplicación funcional y modelos entrenados o forma de reproducir el entrenamiento.
3. Informe técnico de máximo 10 páginas sin anexos: problema, arquitectura, decisiones justificadas, metodología, resultados, discusión, fallos y recomendaciones.
4. Bitácora de decisiones: mínimo seis, con alternativas, evidencia y criterio de selección.
5. Evidencia experimental: configuraciones, semillas, datos y gráficas que permitan revisar las conclusiones.
6. Sustentación con demostración en vivo y preguntas individuales sobre red neuronal, entrenamiento, resultados y decisiones.

Uso de IA: permitido, pero el informe debe incluir una declaración breve de herramientas, para qué se usaron, qué recomendaciones se aceptaron o rechazaron y qué validaciones se hicieron. En la sustentación pueden pedir explicar una decisión, modificar de forma controlada un parámetro, leer una gráfica o interpretar un comportamiento inesperado. No poder explicar la solución afecta la nota.

Rúbrica: análisis del problema y decisiones de diseño 20 %; diseño experimental y rigor de la comparación 25 %; interpretación crítica y propuestas de mejora 20 %; desarrollo funcional e integración neuronal 20 %; documentación y reproducibilidad 5 %; sustentación y dominio individual 10 %.

Condiciones de aceptación: las decisiones de al menos una población deben salir de la red neuronal; las dos especies con modelos diferenciados o entrenamientos justificados; no se aceptan animaciones que aparenten aprendizaje ni una interfaz sin entrenamiento comprobable. Los resultados negativos, los modelos que no convergen y los ecosistemas desequilibrados son válidos si están documentados. Se valora la honestidad experimental por encima de resultados vistosos pero no verificables.

## 3. Estado en una tabla

| Entregable o requisito | Estado |
|------------------------|--------|
| Entorno 2D | Hecho y probado |
| Dos especies con redes diferenciadas (presa 6-12-8-2, depredador 5-10-8-2) | Hecho |
| Entrenamiento real por neuroevolución con evidencia de cambio de pesos | Hecho; modelos entrenados por Edison (100 generaciones) |
| Agentes de referencia (aleatorio, por reglas, perseguidor, interceptor) | Hecho |
| Calibración del mundo con criterios y validación | Hecho (9 de 9 criterios en la máquina de Edison) |
| Infraestructura de evaluación y análisis estadístico (Fase 4) | Entregada y probada en un entorno de prueba; NO se sabe si Edison ya la ejecutó con los modelos reales |
| Modelos de la comparación de arquitecturas (presa pequeña y grande) | Pendiente de entrenar (comandos en sección 10) |
| Evaluación final con semillas 5000 a 5029 y análisis | Pendiente de ejecutar |
| Hipótesis escritas antes de evaluar (docs/hipotesis.md) | Hecho (columnas de resultado en "pendiente") |
| Bitácora con mínimo 6 decisiones | Hecho: D1 a D14; falta actualizar evidencia con resultados reales |
| Visualización | PARCIAL: visor en tiempo real con paneles básicos; FALTA la consulta de decisiones de los agentes, estadísticas en vivo y el modo de modificación de parámetros |
| README y reproducibilidad | Mayormente hecho; falta fijar versiones de dependencias y revisar qué se sube a GitHub |
| Declaración de uso de IA (docs/uso_ia.md) | Solo plantilla vacía; PENDIENTE y obligatoria |
| Análisis cualitativo de comportamientos y de trucos aprendidos | Pendiente |
| Informe técnico (máximo 10 páginas) | Pendiente |
| Documento de defensa (explicar cada frase del código) | Pendiente, pedido explícito de Edison |
| Sustentación y ensayo | Pendiente |

## 4. Arquitectura y flujo

Flujo de una simulación: configuración (YAML) -> World (entorno) -> cada paso: observaciones normalizadas -> controlador de cada especie (red o referencia) -> acciones (giro, velocidad) -> World.step -> métricas del episodio -> fitness.

Flujo de entrenamiento (experiments/entrenar.py -> training.train): se crea una población de genomas (vectores de pesos); en cada generación todos los genomas se evalúan con las mismas semillas en episodios contra un oponente de referencia fijo; se calcula el fitness; el algoritmo genético (élite, torneo, mutación gaussiana) genera la siguiente población; al final se re-evalúan los mejores con semillas de validación y se guarda el ganador.

Flujo de evaluación (experiments/evaluar.py -> evaluation.evaluate_jobs): cada condición se corre en los escenarios A, B y C con 30 semillas de evaluación final; se guarda results/fase4/episodios.csv. Luego experiments/analizar.py calcula tablas, pruebas pareadas, veredictos y figuras.

Contratos de interfaz (no romperlos):

- Observación de presa: matriz (n, 6). Columnas: 0 energía propia entre 0 y 1; 1 ángulo a la planta más cercana (dividido por pi, entre -1 y 1); 2 distancia a la planta más cercana (dividida por la visión, 1 si no ve); 3 ángulo al depredador más cercano; 4 distancia al depredador más cercano; 5 distancia a la pared al frente. Si no ve un objetivo: ángulo 0 y distancia 1.
- Observación de depredador: matriz (n, 5). Columnas: 0 energía; 1 ángulo a la presa más cercana; 2 distancia a la presa más cercana; 3 rumbo de la presa respecto a la línea de visión depredador-presa (dividido por pi); 4 distancia a la pared al frente.
- Acción de cada agente: matriz (n, 2). Columna 0 giro entre -1 y 1 (se multiplica por max_turn en radianes por paso); columna 1 velocidad entre 0 y 1 (se multiplica por max_speed).
- Controlador: cualquier objeto con act(obs, rng) que devuelve la matriz de acciones. Las redes (NeuralController) y los de referencia cumplen la misma interfaz. NeuralController tiene además decide(obs) que devuelve las activaciones de cada capa (pensado para la consulta de decisiones del visor).
- Genoma: vector con W1, b1, W2, b2, W3, b3 concatenados; Wi tiene forma (entradas, salidas). Presa 206 parámetros, depredador 166.

Reglas del mundo (orden de cada paso de World.step):

1. Movimiento: giro y velocidad de cada agente vivo; las posiciones se recortan a los bordes (hay paredes). Gasto de energía por paso = energy_cost_base + energy_cost_move por la velocidad real.
2. Alimentación: cada planta activa la toma la presa viva más cercana si está a menos de eat_radius (10); gana energy_value (30), con tope en max_energy. Una presa puede comer varias plantas en un mismo paso.
3. Captura: cada presa viva la captura el depredador vivo más cercano si está a menos de capture_radius (8); la presa muere y el depredador gana energy_gain_capture (35), con tope.
4. Muerte por energía menor o igual a 0 (presas y depredadores).
5. Reaparición: con probabilidad respawn_rate por paso aparece una planta nueva en una posición aleatoria si hay cupo.

Fin de episodio: se llega a max_steps (1500) o mueren todas las presas. Si mueren todos los depredadores el episodio continúa (decisión D8, para no sesgar las métricas de las presas). Las poblaciones son fijas durante un episodio (no hay reproducción); la evolución ocurre entre episodios.

Semillas y aleatoriedad (todo reproducible):

- Mundo: numpy default_rng([semilla, 0]). Controladores de referencia: default_rng([semilla, 1]) dentro de runner.run_episode.
- Algoritmo evolutivo: default_rng([seed de la configuración (42), 2 para presa o 3 para depredador]).
- Entrenamiento: en la generación g, con K episodios por genoma, las semillas son 1000 + g*K + j. Validación final: 1900 a 1909 (train_start + 900). Calibración y desarrollo: 2000 en adelante. Evaluación final: 5000 a 5029 (no usar nunca para ajustar nada).

Neuroevolución: un genoma por especie y por episodio, compartido por todos los individuos de esa especie (reduce el ruido, supuesto declarado en D3). Élite 3, torneo de 3, mutación gaussiana por gen (tasa 0.1, sigma 0.2), cruce desactivado, población 30, 100 generaciones, 3 episodios por genoma. Pesos iniciales Normal(0, 1/entradas), sesgos en cero. Activaciones: tanh en capas ocultas; salida de giro con tanh; salida de velocidad con sigmoide.

Fitness (configs/base.yaml, sección fitness): presa = 0.7 por supervivencia (prey_survival, pasos vivos promedio entre max_steps) + 0.3 por comida (food_eaten_per_prey dividido por 8, con tope 1). Depredador = 0.7 por capturas (capturas totales divididas por el número de presas, con tope 1) + 0.3 por energía final normalizada (promedio sobre todos los depredadores; los muertos cuentan 0). Variantes para ablación: variant_prey "supervivencia" y variant_predator "capturas".

Entrenamiento por etapas: la presa aprende contra el depredador perseguidor (training.prey_opponent). El depredador aprende en dos etapas: etapa 1 contra presa aleatoria (--oponente aleatorio) y etapa 2 contra la presa por reglas (--oponente reglas --desde models/depre_A_etapa1), partiendo de la población final de la etapa 1 (decisión D12).

Agentes de referencia:

- aleatorio (ambas especies): giro uniforme entre -1 y 1, velocidad uniforme entre 0 y 1.
- reglas (presa): huye si el depredador está a menos de 0.6 de la visión; si no, va a la planta más cercana a velocidad máxima; si no ve nada deambula. Si la pared está muy cerca gira y reduce la velocidad.
- perseguidor (depredador, estilo Blinky): va hacia la presa más cercana.
- interceptor (depredador, estilo Pinky): apunta al punto de encuentro exacto suponiendo que la presa avanza en línea recta a su velocidad máxima. Con r = velocidad presa / velocidad depredador y phi el rumbo relativo de la presa: tau = (r cos(phi) + raíz(1 - r^2 sin^2(phi))) / (1 - r^2); el punto de encuentro en el sistema de la línea de visión es (1 + r tau cos(phi), r tau sin(phi)). Si r >= 1 usa tau = 1.

## 5. Estructura del repositorio

Raíz: la carpeta neuroecosistema (la que contiene configs, docs, src), dentro de C:\Users\ediso\Proyecto_Integrador_IA_2026... Verificar la ruta exacta con Get-Location. Entorno virtual en .venv; Python 3.12.0; NumPy 2.5.4 en la máquina de Edison.

    configs/base.yaml                 parámetros base (calibrados)
    configs/escenarios/A.yaml B.yaml C.yaml
    src/neuroeco/                     paquete (ver sección 6)
    experiments/                      scripts de línea de comandos (ver sección 6)
    tests/                            test_world.py, test_entrenamiento.py, test_evaluacion.py (44 pruebas)
    docs/diseno.md                    especificación de diseño v0.1 más sección 12 (detalles de la Fase 3)
    docs/bitacora.md                  bitácora D1 a D14
    docs/hipotesis.md                 hipótesis y protocolo de evaluación (pre-registro)
    docs/uso_ia.md                    declaración de uso de IA (plantilla vacía, pendiente)
    docs/CONTEXTO_PARA_KIRO.md        este documento
    models/<nombre>/                  una carpeta por entrenamiento (ver abajo)
    results/                          CSV y figuras (fase2_referencias.csv, fase2b_calibracion.csv, fase4/)
    README.md, requirements.txt, pytest.ini, .gitignore

Contenido de cada carpeta de models/<nombre>/: best_genome.npy (modelo final elegido por validación), best_gen0.npy (mejor genoma de la generación 0), population_gen0.npy (población inicial), population_final.npy, history.csv (columnas generacion, mejor, media, desviacion, minimo, metrica_clave_media, metrica_clave_del_mejor, segundos), config.yaml (configuración completa con la arquitectura usada), resumen.json.

Nombres de modelos esperados: models/presa_A_base, models/depre_A_etapa1, models/depre_A_base (más presa_A_pequena y presa_A_grande por entrenar). Verificar en models/ cómo los nombró Edison. Puede haber también una corrida rápida de prueba de la presa (8 generaciones); no usarla.

## 6. Inventario de módulos y funciones

Paquete src/neuroeco:

- config.py: merge_config(base, over) combina diccionarios de forma recursiva; load_config(*paths) carga YAML en orden desde la raíz; load_scenario(name) devuelve base más escenario A, B o C.
- world.py: wrap_angle(a). Clase World(cfg, seed): observe_prey(), observe_predator(), step(prey_out, pred_out), metrics(), propiedad done; auxiliares _random_positions, _dist_matrix, _nearest, _wall_ahead, _move. Estado en arreglos NumPy: plant_pos/plant_active, prey_pos/prey_heading/prey_energy/prey_alive/prey_steps_alive/prey_food, pred_pos/pred_heading/pred_energy/pred_alive/pred_captures, t, capture_steps.
- controllers.py: Controller (interfaz), RandomController, PreyRules, PredatorChaser, PredatorInterceptor, base _RuleBase (_finish evita quedarse contra la pared); make_prey_controller(name, cfg) con nombres aleatorio y reglas; make_predator_controller(name, cfg) con aleatorio, perseguidor e interceptor.
- runner.py: run_episode(cfg, prey_controller, predator_controller, seed, callback=None) corre un episodio completo y devuelve el diccionario de métricas.
- network.py: sigmoid; Network(sizes) con random_genome(rng), unpack(genome), forward(obs, layers, return_activations); NeuralController(sizes, genome) con act(obs, rng) y decide(obs); layer_sizes(cfg, species); load_model(path, species, cfg) que devuelve (tamaños, genoma) leyendo la arquitectura del config.yaml de la corrida; load_neural_controller(path, species, cfg).
- fitness.py: fitness_prey(metrics, cfg), fitness_predator(metrics, cfg), fitness_for(species, metrics, cfg).
- evolution.py: Evolution(evo_cfg) con next_population(population, fitness, rng) (élite, torneo, mutación; cruce opcional).
- training.py: evaluate_genome(job) evalúa un genoma en varias semillas y devuelve (fitness medio, métrica clave media); _Evaluator evalúa en serie o en paralelo (multiprocessing con contexto spawn); train(cfg, species, scenario, run_dir, processes, log, init_population, desde) entrena y guarda todo; _git_commit().
- evaluation.py: build_controller(spec, species, cfg); run_job(job) devuelve una fila con metadatos, métricas y fitness; evaluate_jobs(jobs, processes, log) en serie o paralelo con el mismo resultado.
- estadistica.py: holm(pvalues); mean_ci95(x); paired_comparison(a, b) devuelve diferencia media, IC 95 % (t), d_z, correlación biserial por rangos y p de Wilcoxon pareado.
- viewer.py: run_viewer(cfg, prey_controller, predator_controller, seed, fps, max_frames, screenshot, title) con pygame; teclas ESPACIO pausa, ARRIBA y ABAJO velocidad, N otra semilla, R reiniciar, ESC salir; HUD con semilla, paso, presas, depredadores, plantas y capturas. No tiene aún consulta de decisiones.

Scripts en experiments/ (todos se corren desde la raíz con el entorno virtual activo):

- ver_episodio.py: abre el visor. Opciones --escenario A, B o C; --presa aleatorio o reglas; --depredador aleatorio, perseguidor o interceptor; --modelo-presa y --modelo-depredador (carpeta o .npy); --semilla; --fps; --max-frames y --captura para pruebas sin ventana.
- revisar_referencias.py: rendimiento de los agentes de referencia con semillas de desarrollo; guarda results/fase2_referencias.csv.
- calibrar_mundo.py: criterios K1 a K9 con semillas de desarrollo (2000 en adelante); guarda results/fase2b_calibracion.csv.
- entrenar.py: entrena una especie. Opciones --especie, --escenario, --generaciones, --poblacion, --episodios, --procesos (por defecto núcleos menos uno; el resultado no depende de este número), --oponente, --desde, --ocultas (por ejemplo 6,4), --semilla, --nombre, --rapido.
- evaluar.py: evaluación final con las semillas 5000 a 5029 (opciones --presa-base, --depre-etapa1, --depre-base, --presa-pequena, --presa-grande, --semillas, --escenarios, --procesos, --salida). Guarda results/fase4/episodios.csv y configuracion_evaluacion.json.
- analizar.py: define las comparaciones y los criterios de H1 a H4 (más exploratorias), calcula pruebas con corrección de Holm por familia, guarda comparaciones.csv, resumen_condiciones.csv, hipotesis_resultados.md y figuras (curvas_aprendizaje, presa_fitness_perseguidor, presa_fitness_interceptor, depredador_fitness, depredador_capturas, diferencias_pareadas).

Métricas por episodio (World.metrics): steps, prey_survival, prey_alive_final, pred_alive_final, food_eaten_total, food_eaten_per_prey, captures_total, captures_per_pred, pred_final_energy (energía media normalizada, muertos en 0), prey_final_energy, first_capture_step, mean_time_to_capture (NaN si no hubo capturas). Las filas de evaluación añaden fitness_presa y fitness_depredador.

## 7. Parámetros actuales (valores calibrados)

Mundo 800 por 600, 1500 pasos. Plantas: valor de energía 30, radio de consumo 10. Presas: 30, velocidad máxima 3.0, giro máximo 0.25 rad por paso, energía inicial 100 y máxima 150, costo base 0.03 más 0.05 por velocidad, visión 150. Depredadores: velocidad máxima 3.1 (calibrado, antes 3.4), giro máximo 0.20, energía inicial 150 y máxima 200, costo base 0.05 más 0.08 por velocidad, visión 180, radio de captura 8, energía por captura 35 (calibrado, antes 60).

| Escenario | Plantas iniciales | Máximo de plantas | Reaparición | Depredadores |
|-----------|-------------------|-------------------|-------------|--------------|
| A (recursos suficientes, pocos depredadores; es el de entrenamiento) | 80 | 150 | 0.10 | 3 |
| B (escasez de alimento) | 40 | 60 | 0.02 | 3 |
| C (más presión de depredación) | 80 | 150 | 0.10 | 10 |

B y C difieren de A en una sola variable (hay una prueba automática que lo verifica). Los modelos se entrenan solo en A y se evalúan en A, B y C.

## 8. Bitácora de decisiones (resumen; el detalle con alternativas y evidencia está en docs/bitacora.md)

- D1: percepción relativa (ángulo y distancia al objetivo más cercano, energía, pared al frente); se excluyen posición absoluta, mapa global y estado de otros agentes. Alternativa descartada: rayos de visión.
- D2: redes presa 6-12-8-2 y depredador 5-10-8-2, tanh oculto, salidas de giro (tanh) y velocidad (sigmoide).
- D3: neuroevolución por etapas contra oponente fijo; un genoma compartido por especie en cada episodio.
- D4: fitness mixto (ver sección 4); riesgos documentados de trucos (quedarse quieto, pegarse a paredes, orbitar).
- D5: entrenar en A y evaluar en A, B y C; 30 semillas distintas de las de entrenamiento; mismas semillas en todas las condiciones.
- D6: métricas (supervivencia, comida, capturas, energía final, tiempo hasta captura, variabilidad).
- D7: agentes de referencia aleatorio, por reglas, perseguidor e interceptor; roles de depredador neuronales diferenciados quedan como extensión.
- D8: fin de episodio solo por max_steps o por extinción de presas.
- D9: calibración del mundo (cambios de la sección 7) con criterios K1 a K9 validados en semillas distintas.
- D10: interceptor con solución exacta de intercepción; en episodios completos no supera al perseguidor.
- D11: protocolo de semillas del entrenamiento (mismas semillas por generación, rotación, validación final separada).
- D12: entrenamiento por etapas del depredador (primero contra presa aleatoria).
- D13: arquitecturas de la comparación C2 (presa 6-4, 12-8 y 24-16 de neuronas ocultas; 80, 206 y 602 parámetros).
- D14: protocolo de evaluación final (hipótesis previas, pareadas, Wilcoxon, Holm, equivalencia por IC, exploratorio separado).

## 9. Resultados hasta la fecha

### 9.1 Calibración (máquina de Edison, semillas 2000 a 2019): 9 de 9 criterios cumplidos

K1 presas vivas en A sin depredación efectiva 0.86 (umbral 0.85); K2 presas vivas en B 0.37 (entre 0.25 y 0.60); K3 supervivencia con referencia en A 0.62 (entre 0.45 y 0.75); K4 capturas por depredador en A 6.15 (entre 3 y 10); K5 depredadores vivos al final en A 0.42 (mínimo 0.30); K6 ventaja de la presa por reglas sobre la aleatoria 0.38 (mínimo 0.20); K7 capturas del perseguidor frente al aleatorio 18.45 veces (mínimo 5); K8 caída de supervivencia en C respecto a A 0.27 (mínimo 0.20, con 1.5 presas o más vivas); K9 caída de supervivencia en B respecto a A 0.04 (cumple por margen estrecho). En otro entorno de prueba salieron valores casi iguales (por ejemplo K1 0.87): las diferencias de centésimas entre máquinas son normales. K1 está cerca de su umbral.

### 9.2 Referencias (entorno de prueba, semillas 2000 a 2019 salvo indicación)

- Escenario A, presa por reglas contra el perseguidor: 19.1 capturas (desviación 3.8), supervivencia 0.60; contra el interceptor: 16.1 (3.9), supervivencia 0.67. Escenario C: perseguidor 26.6 (2.1), supervivencia 0.35; interceptor 27.9 (2.4), supervivencia 0.31. Conclusión honesta: el interceptor no supera al perseguidor en episodios completos.
- Duelos con presa que avanza recta (pruebas automáticas): el interceptor captura en unos 31, 31 y 34 pasos frente a 140, 140 y 110 del perseguidor. La fórmula es correcta; lo que falla en el mundo completo es el supuesto de línea recta (las presas giran, huyen y evitan paredes).
- Fitness del depredador en A contra presa por reglas (semillas 1000 a 1007): aleatorio 0.003, quieto 0.112 (el fitness premia quedarse quieto por la energía final), perseguidor 0.518. Contra presa aleatoria: aleatorio 0.219 y perseguidor 0.811.

### 9.3 Entrenamientos completos (máquina de Edison; 100 generaciones, población 30, 3 episodios por genoma, 9050 episodios cada uno)

| Modelo | Oponente | Población inicial | Fitness de validación (semillas 1900 a 1909) | Tiempo | Cambio de pesos |
|--------|----------|-------------------|-----------------------------------------------|--------|-----------------|
| Presa (206 parámetros) | perseguidor | aleatoria | 0.807 (finalistas 0.807, 0.736, 0.785, 0.792, 0.783) | 806 s | norma 10.66, 100 % de los pesos modificados |
| Depredador etapa 1 (166) | presa aleatoria | aleatoria | 0.885 (finalistas 0.776, 0.777, 0.787, 0.885, 0.820) | 810 s | norma 9.85 |
| Depredador etapa 2 (166) | presa por reglas | models/depre_A_etapa1 | 0.539 (finalistas 0.406, 0.423, 0.375, 0.491, 0.539) | 917 s | norma 7.52 |

Contexto: el perseguidor por reglas tiene fitness 0.518 en semillas de desarrollo, así que el depredador entrenado queda aproximadamente a su nivel (no se puede afirmar nada sin la evaluación final con las semillas 5000 a 5029). La presa por reglas contra el perseguidor ronda un fitness de 0.69 estimado (supervivencia 0.60); la presa entrenada la supera en validación, pendiente de confirmar. Entorno de ejecución: Python 3.12.0, NumPy 2.5.4, commit 789f8b9.

### 9.4 Pilotos cortos (8 generaciones, 12 genomas, 2 episodios; sustentan la decisión D12)

Presa: fitness medio de 0.215 a unos 0.30. Depredador desde cero contra la presa por reglas: fitness medio entre 0.003 y 0.019 y validación 0.014 (casi no aprende). Depredador contra presa aleatoria: fitness medio de 0.165 a 0.322 y capturas de 6.1 a 11.1. Etapa 2 partiendo de ese resultado: validación 0.082 en el piloto corto. Cuenta como evidencia preliminar, no concluyente.

### 9.5 Pruebas automáticas: 44 pasan (python -m pytest -q, unos 15 a 20 segundos)

- tests/test_world.py (17): reproducibilidad por semilla, observaciones en rango y forma, agentes dentro del mundo y energía acotada, mecánica de alimentación y de captura, muerte por energía, fin de episodio, continuidad si mueren los depredadores, interceptor contra perseguidor en duelos, perseguidor contra aleatorio, escenarios B y C difieren de A en una sola variable, comportamiento del interceptor sin adelanto.
- tests/test_entrenamiento.py (17): número de parámetros (206 y 166), forma y rango de salidas de la red, determinismo, error con genoma de tamaño incorrecto, forward contra cálculo manual, activaciones, guardar y cargar modelos, fitness y variantes, élite del algoritmo genético, mutación, mejora en un problema sencillo, entrenamiento mínimo de ambas especies con todos los archivos, mismo resultado con 1 o 2 procesos, semillas de entrenamiento que no invaden las de validación, entrenamiento por etapas, error con población inicial de forma incorrecta.
- tests/test_evaluacion.py (10): Holm contra cálculo a mano, IC 95 % con valores conocidos, comparación pareada con diferencia clara y sin diferencia, caso idéntico, error con semillas distintas, fila de evaluación, serie igual a paralelo, carga de redes de distinto tamaño.

### 9.6 Fase 4 (evaluación final): NO ejecutada con los modelos reales hasta donde se sabe

El flujo evaluar.py y analizar.py se probó de punta a punta con modelos de prueba y 4 semillas (resultados sin ningún valor científico). No existen todavía resultados de las hipótesis.

### 9.7 Hallazgos y advertencias a tener presentes

- Reward hacking confirmado en el depredador: quedarse quieto gana más fitness que moverse al azar (la energía final lo premia). Es material para el informe (sección de fallos).
- El depredador no aprende desde cero contra una presa que huye: la señal de aprendizaje es casi nula; el currículo de dos etapas lo resuelve parcialmente.
- El interceptor correcto no supera al perseguidor en el mundo completo.
- K9 cumple por poco: la escasez de alimento casi no cambia la supervivencia cuando hay depredadores; su efecto se ve más en el alimento y la energía.
- El fitness medio por generación no es monótono porque las semillas de entrenamiento cambian cada generación (es esperado).
- Cada modelo sale de UNA corrida de entrenamiento (semilla 42): no se mide la variabilidad entre corridas de entrenamiento. Limitación declarada en docs/hipotesis.md.
- Las hipótesis se redactaron después de ver el fitness de validación (semillas 1900 a 1909) y antes de tocar las semillas de evaluación final. Está declarado en docs/hipotesis.md.

## 10. Pendientes priorizados (hasta terminar)

P1. Verificar el estado actual (sección 11).

P2. Entrenar las arquitecturas de la comparación C2 (unos 14 minutos cada una en la máquina de Edison):

    python experiments/entrenar.py --especie presa --ocultas 6,4 --nombre presa_A_pequena
    python experiments/entrenar.py --especie presa --ocultas 24,16 --nombre presa_A_grande

P3. Congelar las hipótesis haciendo commit de docs/hipotesis.md ANTES de evaluar (la fecha del commit demuestra el pre-registro). Luego evaluar y analizar:

    python experiments/evaluar.py --presa-base models/presa_A_base --depre-etapa1 models/depre_A_etapa1 --depre-base models/depre_A_base --presa-pequena models/presa_A_pequena --presa-grande models/presa_A_grande
    python experiments/analizar.py

Después llenar las columnas Resultado y ¿Se cumplió? de docs/hipotesis.md con los valores de results/fase4/hipotesis_resultados.md, sin editar las hipótesis ni los criterios. Si un error obliga a repetir la evaluación, anotarlo en la bitácora como cambio posterior (post hoc).

P4. Completar la visualización (requisito obligatorio de la rúbrica; hoy es parcial). Mínimo a construir en src/neuroeco/viewer.py (sin romper la regla de que el visor no modifica la simulación, salvo en el modo defensa, que reinicia el mundo):

- Consulta de decisiones: al hacer clic en un agente, mostrar sus entradas, las activaciones de cada capa y las salidas (giro y velocidad) usando NeuralController.decide; indicar si el agente es red o referencia por reglas.
- Estadísticas en vivo: presas vivas, capturas, energía media y una gráfica corta en el tiempo.
- Modo defensa: teclas para cambiar semilla, densidad de comida, número de depredadores y modelo cargado en vivo, y para pausar y avanzar paso a paso. Es la modificación controlada de un parámetro que el profesor puede pedir.
- Poder cargar los modelos entrenados (ya existe --modelo-presa y --modelo-depredador) y elegir escenario.

P5. Análisis cualitativo y de errores: ver episodios con los modelos entrenados, describir las estrategias aprendidas (buscar plantas, huir, comportamiento ante paredes) y los trucos (reward hacking), cuantificar lo que se pueda con un script nuevo (por ejemplo velocidad media, tiempo cerca de paredes) y registrar hallazgos en la bitácora.

P6. Extras de rigor, en este orden de valor si hay tiempo: repetir el entrenamiento con 3 semillas del algoritmo (--semilla) para medir la variabilidad entre corridas; ablación de fitness con las variantes ya implementadas (variant_prey supervivencia, variant_predator capturas) como comparación adicional; ablación de entradas; entrenar en B y C; coevolución (etapa C); roles de depredador estilo Pac-Man con redes propias; visor 3D de repetición (solo al final y solo si todo lo demás está cerrado).

P7. Informe técnico de máximo 10 páginas (sin anexos), APA, Times New Roman 12, sin líneas decorativas, negrilla y cursiva solo en títulos, portada cuidada con el nombre de Edison. Secciones: problema, arquitectura, decisiones justificadas (puede resumir la bitácora), metodología, resultados (tablas y figuras de results/fase4), discusión (qué contradijo las expectativas), fallos y limitaciones, recomendaciones (qué decisión modificar primero y con qué evidencia) y la declaración de uso de IA. Mapear cada sección a la rúbrica. Anexos: bitácora completa, configuraciones, semillas, tablas completas.

P8. Declaración de uso de IA (docs/uso_ia.md y resumen en el informe). Debe ser honesta: el asistente Claude (Anthropic) generó la mayor parte del código y de los scripts bajo dirección de Edison, y Kiro generará lo que venga. Incluir qué recomendaciones se aceptaron, cuáles se rechazaron o modificaron (por ejemplo: se descartó el visor 3D del núcleo; se decidió entrenar al depredador por etapas; se corrigió el interceptor tras una prueba que falló) y las validaciones realizadas (44 pruebas automáticas, calibración con criterios y semillas separadas, validación del entrenamiento con semillas no usadas, evaluación final con semillas reservadas, hipótesis escritas antes).

P9. Reproducibilidad y repositorio: fijar versiones en requirements.txt (pip freeze del entorno de Edison: Python 3.12.0, NumPy 2.5.4); actualizar el README con los comandos exactos y las semillas; revisar .gitignore: hoy results/* está ignorado (salvo .gitkeep), pero la evidencia experimental debe poder revisarse, así que subir los CSV y figuras de results/fase4 y los modelos .npy y resumen.json de models/ (son pequeños); crear un commit o etiqueta de la entrega.

P10. Documento de defensa (pedido explícito de Edison; hacerlo cuando el programa esté terminado): explicar el código archivo por archivo, función por función y, donde importe, línea por línea, con el porqué de cada decisión; conceptos (red neuronal multicapa, tanh y sigmoide, neuroevolución, fitness, élite, torneo, mutación, semillas, datos pareados, Wilcoxon, Holm, intervalo de confianza, equivalencia, tamaño del efecto, reward hacking); mapa D1 a D14 con respuesta modelo para cada pregunta de la sección 5 de la propuesta; banco de unas 60 preguntas probables con respuesta (red, entrenamiento, resultados, decisiones, modificación de parámetros, interpretación de gráficas); guion de demostración en vivo de 5 a 7 minutos; ejercicios de modificación controlada de un parámetro con el resultado esperado; plan B si algo falla en vivo; glosario. Mismo estilo académico de Edison (sección 1).

P11. Ensayo de la sustentación: que Edison explique sin leer, cambie un parámetro en vivo y lea una gráfica.

## 11. Cómo verificar el estado (primer paso para Kiro)

    git status
    git log --oneline
    python -m pytest -q
    Get-ChildItem models
    Get-ChildItem results -Recurse

Esperado: 44 pruebas pasan. Debe haber en models/ al menos las carpetas de la presa base, depredador etapa 1 y depredador etapa 2. Si existen docs/hipotesis.md con "Estado: redactadas el 13 de noviembre de 2026" y las filas D13 y D14 en docs/bitacora.md, la Fase 4 se aplicó. Si faltan archivos de la Fase 4 (por ejemplo experiments/evaluar.py), reconstruirlos a partir de la sección 6 y de las descripciones de este documento. Si results/fase4/episodios.csv ya existe, la evaluación final ya se ejecutó: no repetirla sin registrar el motivo.

Instalación desde cero (PowerShell):

    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    pip install -r requirements.txt

Dependencias: numpy, pyyaml, pandas, matplotlib, scipy, pygame, pytest.

Comandos principales de reproducción: calibrar con python experiments/calibrar_mundo.py; entrenar la presa con python experiments/entrenar.py --especie presa --nombre presa_A_base; entrenar el depredador en dos etapas con python experiments/entrenar.py --especie depredador --oponente aleatorio --nombre depre_A_etapa1 y luego python experiments/entrenar.py --especie depredador --oponente reglas --desde models/depre_A_etapa1 --nombre depre_A_base; ver modelos con python experiments/ver_episodio.py --modelo-presa models/presa_A_base --modelo-depredador models/depre_A_base. Un entrenamiento completo son unos 9000 episodios: en la máquina de Edison tomó entre 806 y 917 segundos con varios procesos; en un solo núcleo serían unos 75 minutos.

## 12. Reglas que no se deben romper (invariantes)

- Las semillas de evaluación final 5000 a 5029 se usan solo en experiments/evaluar.py. Nunca para entrenar, validar, calibrar ni ajustar.
- No editar las hipótesis ni sus criterios después de la primera ejecución de evaluar.py. Todo cambio posterior se registra como post hoc.
- No cambiar parámetros calibrados (sección 7), el fitness (D4), las observaciones ni el protocolo de semillas sin registrar el cambio en la bitácora con la evidencia. Si se cambia algo del mundo, hay que reentrenar todos los modelos y repetir calibración y evaluación.
- Mantener la reproducibilidad: todo azar con semilla explícita; el resultado no debe depender del número de procesos.
- Mantener las interfaces de la sección 4 (observación, acción, controlador, genoma).
- Los resultados negativos se documentan, no se esconden.
- No presentar un número en el informe que no salga de results/ o models/.
- Aclaración técnica: en el proyecto de Edison, world.py es la versión original sin la optimización de distancias que se probó en el entorno de prueba (daba resultados idénticos bit a bit pero no se entregó). No mezclar versiones sin repetir las pruebas.

## 13. Problemas conocidos y trampas

- Windows y multiprocessing con spawn: todo script que use procesos necesita el bloque if __name__ == "__main__". Ya está en los scripts existentes.
- Los resultados numéricos varían en centésimas entre máquinas y versiones de NumPy; los criterios de calibración y las pruebas estadísticas deben leerse con ese margen (K1 está cerca de su umbral).
- La población "antes del entrenamiento" del depredador sale de models/depre_A_etapa1/population_gen0.npy (aleatoria), no de la etapa 2, porque la etapa 2 parte de la población ya entrenada de la etapa 1.
- La condición "red sin entrenar" usa las 5 primeras redes de la población inicial y promedia por semilla.
- Si no hay capturas, first_capture_step y mean_time_to_capture son NaN (se promedian ignorando NaN).
- Wilcoxon con muchas diferencias iguales a cero las descarta; con diferencias idénticas devuelve p = 1.
- En el visor, la fuente consolas es de Windows; en otros sistemas pygame usa una por defecto.
- La primera ejecución de las pruebas en paralelo puede tardar más en Windows por el arranque de procesos.

## 14. Qué tiene que poder defender Edison en la sustentación (guía para el documento de defensa)

Red y entrenamiento: por qué esos tamaños y activaciones; cómo se modifican los pesos (neuroevolución, no gradientes); qué se optimiza y qué trucos puede favorecer (quedarse quieto, paredes, orbitar); por qué un genoma compartido por especie y qué supuesto introduce; por qué entrenamiento por etapas del depredador. Experimentos: qué cambia y qué se mantiene en cada comparación; por qué semillas pareadas y distintas de las de entrenamiento; qué significan IC, Wilcoxon, Holm, tamaño del efecto y equivalencia; qué resultados contradijeron las expectativas. Mejora: qué modificaría primero y con qué evidencia. En vivo: ejecutar la simulación, cargar los modelos, consultar decisiones de un agente, cambiar un parámetro y leer una gráfica.