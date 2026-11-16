# Especificación de diseño (versión 0.1, 12 de noviembre de 2026)

Todo valor numérico de este documento es inicial y se calibra con datos. Cada cambio relevante se registra en docs/bitacora.md.

## 1. Pregunta y alcance

Pregunta orientadora: en qué condiciones los agentes controlados por redes neuronales desarrollan comportamientos de búsqueda, persecución y evasión que mejoran su desempeño frente a estrategias sin aprendizaje.

Núcleo del proyecto: una especie de presas y una especie de depredadores, cada una con su propia red neuronal multicapa y su propio entrenamiento. Todo lo demás (obstáculos, rayos de visión, coevolución, roles de depredador, visor 3D) queda como extensión, y solo se aborda cuando el núcleo esté completo y documentado.

## 2. Entorno

- Mundo 2D rectangular con paredes (sin reaparición por el borde), tiempo discreto, máximo de pasos por episodio según configs/base.yaml.
- Elementos: plantas (alimento), presas y depredadores. Sin obstáculos en el núcleo.
- Plantas: aparecen en posiciones aleatorias; reaparecen con probabilidad respawn_rate por paso hasta un máximo.
- Presa: consume una planta si está a menos de eat_radius; gana energy_value de energía.
- Depredador: captura una presa si está a menos de capture_radius; la presa muere y el depredador gana energy_gain_capture.
- Energía: el costo por paso es energy_cost_base más energy_cost_move por la velocidad. Un agente con energía 0 muere.
- Fin de episodio: se alcanza max_steps o mueren todas las presas. Si mueren todos los depredadores el episodio continúa, para no sesgar las métricas de las presas.
- Las poblaciones son fijas dentro de un episodio (no hay reproducción en el simulador). La evolución ocurre entre episodios.

## 3. Percepción (entradas de las redes)

Todas las entradas son relativas al agente y están normalizadas. Si no hay objetivo dentro del rango de visión, la distancia vale 1 y el ángulo vale 0.

Presa (6 entradas):
1. Energía propia dividida por max_energy.
2. Ángulo relativo a la planta más cercana (dividido por pi).
3. Distancia a la planta más cercana (dividida por vision_range).
4. Ángulo relativo al depredador más cercano.
5. Distancia al depredador más cercano.
6. Distancia a la pared al frente (dividida por vision_range, máximo 1).

Depredador (5 entradas):
1. Energía propia dividida por max_energy.
2. Ángulo relativo a la presa más cercana.
3. Distancia a la presa más cercana.
4. Rumbo de la presa más cercana relativo a la línea de visión depredador-presa (permite anticipar hacia dónde se mueve).
5. Distancia a la pared al frente.

Variables excluidas y por qué: posición absoluta (x, y), información global del mapa, estado de otros agentes de su misma especie. Con posición absoluta la red podría memorizar el mapa en lugar de aprender a reaccionar; con sensores relativos lo aprendido generaliza a otras semillas y escenarios.

## 4. Redes neuronales

| Especie | Arquitectura | Parámetros | Activación oculta | Salidas |
|---------|--------------|------------|-------------------|---------|
| Presa | 6, 12, 8, 2 | 206 | tanh | giro (tanh) y velocidad (sigmoide) |
| Depredador | 5, 10, 8, 2 | 166 | tanh | giro (tanh) y velocidad (sigmoide) |

Dos capas ocultas por especie, como exige el enunciado. El giro de salida se multiplica por max_turn (radianes por paso) y la velocidad por max_speed. La red se implementa a mano con NumPy.

## 5. Entrenamiento: neuroevolución

- Genoma: vector con todos los pesos y sesgos de la red de una especie.
- Cada especie tiene su propia población de genomas (population_size).
- Evaluación de un genoma: en cada episodio, todos los individuos de esa especie usan el mismo genoma (supuesto que reduce el ruido y simplifica el análisis). El fitness es el promedio de la especie en el episodio, y luego el promedio de episodes_per_genome episodios con semillas de entrenamiento.
- Operadores: elitismo, selección por torneo, cruce uniforme opcional y mutación gaussiana (mutation_rate, mutation_sigma).
- Etapas: (A) la presa evoluciona contra un depredador de referencia fijo; (B) el depredador evoluciona contra una presa de referencia fija; (C, extensión) coevolución de ambas.
- Se registra por generación: fitness mejor, medio y desviación; y los pesos del mejor genoma, como evidencia de que los parámetros cambian.

## 6. Funciones de fitness (versión inicial)

- Presa: 0.7 por supervivencia normalizada (pasos vivos entre max_steps) más 0.3 por comida consumida normalizada.
- Depredador: 0.7 por capturas normalizadas (capturas entre número de presas) más 0.3 por energía final normalizada.

Comportamientos que podrían favorecerse indebidamente (a vigilar y documentar): presas que se pegan a las paredes o a las esquinas, presas que no se mueven para ahorrar energía, depredadores que orbitan sin capturar, depredadores que capturan rápido pero se quedan sin energía.

## 7. Agentes de referencia (líneas base)

- Aleatorio (ambas especies): giro y velocidad al azar.
- Presa por reglas, forrajeador-huidizo: huye del depredador si está dentro de un radio de alarma; si no, va hacia la planta más cercana.
- Depredador por reglas, perseguidor directo: va hacia la presa más cercana (estilo Blinky de Pac-Man).
- Depredador por reglas, interceptor: apunta a la posición futura estimada de la presa más cercana (estilo Pinky de Pac-Man).

## 8. Diseño experimental

Entrenamiento en el escenario base A; evaluación en los tres escenarios (A, B, C), lo que además mide generalización. Cada escenario se define para que difiera del A en una sola variable:

| Escenario | Plantas iniciales | Reaparición | Depredadores |
|-----------|-------------------|-------------|--------------|
| A: recursos suficientes, pocos depredadores | 80 | 0.04 | 3 |
| B: escasez de alimento | 20 | 0.005 | 3 |
| C: mayor presión de depredación | 80 | 0.04 | 10 |

Valores provisionales; se calibran antes de correr los experimentos finales.

Comparaciones mínimas (cada una con hipótesis escrita antes de ejecutarla, variables controladas, resultados, análisis y conclusión):
- C1: antes y después del entrenamiento (misma arquitectura, pesos aleatorios contra pesos entrenados).
- C2: dos arquitecturas o configuraciones (la base contra una de mayor o menor capacidad).
- C3: red entrenada contra agentes de referencia (aleatorio, reglas, interceptor).

Reglas generales: semillas de entrenamiento y de evaluación en rangos distintos y registrados; 30 semillas de evaluación por condición; las mismas semillas en todas las condiciones, de modo que las comparaciones sean pareadas; media, desviación y intervalo de confianza del 95 %; prueba de Wilcoxon pareada (o Welch si no hay pareo) y tamaño del efecto.

## 9. Métricas

Supervivencia media de las presas, alimento consumido, capturas de los depredadores, energía final, tiempo hasta la captura y variabilidad entre repeticiones.

## 10. Reproducibilidad

- Generadores de azar con semilla explícita (numpy.random.default_rng).
- Cada corrida guarda su configuración completa, las semillas y el hash del commit en results/.
- Instalación y ejecución descritas en el README.

## 11. Fuera del núcleo (extensiones)

Obstáculos, visión por rayos, coevolución (etapa C), roles de depredador con redes propias, visor 3D de repetición.

## 12. Detalles fijados en la Fase 3

- Genoma: vector con W1, b1, W2, b2, W3, b3 (presa 206 parámetros, depredador 166). Pesos iniciales Normal(0, 1/entradas) y sesgos en cero.
- Fitness (configs/base.yaml, sección fitness): presa 0.7 por supervivencia más 0.3 por comida consumida, con 8 plantas por presa como 100 % del componente de comida; depredador 0.7 por capturas sobre el total de presas más 0.3 por energía final. Variantes disponibles para comparar: solo supervivencia y solo capturas.
- Semillas: en cada generación todos los genomas se evalúan con las mismas semillas, y las semillas cambian de una generación a otra. Al final, los mejores genomas de la última generación se re-evalúan con semillas de validación (seeds.train_start más 900 en adelante) que nunca se usaron para entrenar, y el modelo final es el mejor en esa validación. Las semillas de evaluación final no se tocan.
- Operadores: elitismo, torneo, mutación gaussiana por gen. El cruce está disponible pero desactivado (crossover_rate 0).
- Entrenamiento por etapas del depredador: primero contra presa aleatoria y luego contra la presa por reglas, partiendo de la población final de la etapa anterior (D12).
- Cada corrida guarda en models/<nombre>/: mejor genoma, población inicial y final, historial por generación, configuración completa y resumen (incluye la versión de Python y NumPy y el commit).