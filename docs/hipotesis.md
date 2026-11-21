# Hipótesis y protocolo de evaluación (Fase 4)

Estado: redactadas el 13 de noviembre de 2026, después de ver el fitness de validación de los entrenamientos (semillas 1900 a 1909) y antes de usar las semillas de evaluación final (5000 a 5029). Todo cambio posterior a la primera corrida de experiments/evaluar.py se registra en la bitácora como cambio posterior (post hoc) y se informa como tal.

## Protocolo

- Semillas: 30 semillas de evaluación final (5000 a 5029), nunca usadas para entrenar, validar ni calibrar. Son las mismas en todas las condiciones, de modo que las comparaciones son pareadas.
- Entrenamiento solo en el escenario A; evaluación en A, B y C (esto mide generalización).
- Presas: se evalúan contra el depredador perseguidor (el oponente de entrenamiento) y contra el interceptor (oponente no visto en el entrenamiento).
- Depredadores: se evalúan contra la presa por reglas (el oponente de entrenamiento).
- Red sin entrenar: las primeras 5 redes de la población inicial aleatoria; el resultado de cada semilla es el promedio de las 5.
- Métrica principal: el fitness de la especie (D4, valor entre 0 y 1). Secundarias: supervivencia de las presas, capturas, energía final.
- Estadística: diferencia pareada con IC del 95 % (distribución t), prueba de Wilcoxon pareada, tamaño del efecto (d de Cohen para pareados y correlación biserial por rangos) y corrección de Holm dentro de cada familia de hipótesis (H1 a H4). Las equivalencias se deciden por el IC dentro de un margen, no por un valor p.
- Cada modelo proviene de una sola corrida de entrenamiento (semilla del algoritmo evolutivo 42). La variabilidad entre corridas de entrenamiento no se mide; solo la variabilidad entre semillas de evaluación. Es una limitación y se declara en el informe.

## Hipótesis

| ID | Comparación | Hipótesis | Variable que cambia | Variables controladas | Criterio de éxito | Resultado | ¿Se cumplió? |
|----|-------------|-----------|---------------------|-----------------------|-------------------|-----------|--------------|
| H1a | C1: antes y después, presa | El entrenamiento mejora el fitness de la presa respecto a redes con pesos aleatorios. | Pesos (aleatorios o entrenados) | Arquitectura 6-12-8-2, escenario A, oponente perseguidor, semillas | Diferencia de fitness >= 0.20 y p ajustado < 0.01 | Diferencia +0,575 [IC 95 %: 0,550; 0,600]; p ajustado < ,001 | Sí |
| H1b | C1: antes y después, depredador | El entrenamiento mejora el fitness del depredador respecto a redes con pesos aleatorios. | Pesos (aleatorios o entrenados) | Arquitectura 5-10-8-2, escenario A, presa por reglas, semillas | Diferencia de fitness >= 0.20 y p ajustado < 0.01 | Diferencia +0,453 [IC 95 %: 0,395; 0,511]; p ajustado < ,001 | Sí |
| H2a | C2: arquitectura, red grande | Con el mismo presupuesto de entrenamiento, una red más grande (24 y 16 neuronas ocultas, 602 parámetros) no supera a la base (12 y 8, 206 parámetros), porque el espacio de búsqueda crece y el presupuesto no. | Tamaño de las capas ocultas | Entradas y salidas, algoritmo, presupuesto (100 generaciones, 30 genomas, 3 episodios), semilla del algoritmo, escenario A, oponente perseguidor | Diferencia <= 0 o p ajustado >= 0.05 | Diferencia +0,061 [IC 95 %: 0,030; 0,093]; p ajustado < ,001 | No |
| H2b | C2: arquitectura, red pequeña | Una red más pequeña (6 y 4 neuronas ocultas, 80 parámetros) rinde como la base, porque la tarea tiene solo 6 entradas. | Tamaño de las capas ocultas | Igual que H2a | IC 95 % de la diferencia dentro de +-0.05 | Diferencia +0,014 [IC 95 %: −0,015; 0,044]; p ajustado = ,543 | Sí |
| H3a1 | C3: presa contra referencias | La presa entrenada supera a la presa por reglas. | Tipo de controlador | Escenario A, oponente perseguidor, semillas | Diferencia >= 0.05 y p ajustado < 0.05 | Diferencia +0,077 [IC 95 %: 0,044; 0,109]; p ajustado < ,001 | Sí |
| H3a2 | C3: presa contra referencias | La presa entrenada supera claramente a la presa aleatoria. | Tipo de controlador | Escenario A, oponente perseguidor, semillas | Diferencia >= 0.30 y p ajustado < 0.01 | Diferencia +0,565 [IC 95 %: 0,535; 0,594]; p ajustado < ,001 | Sí |
| H3b1 | C3: depredador contra referencias | El depredador entrenado supera claramente al depredador aleatorio. | Tipo de controlador | Escenario A, presa por reglas, semillas | Diferencia >= 0.30 y p ajustado < 0.01 | Diferencia +0,449 [IC 95 %: 0,390; 0,507]; p ajustado < ,001 | Sí |
| H3b2 | C3: depredador contra referencias | El depredador entrenado es equivalente al perseguidor por reglas (ni lo supera ni queda muy por debajo). | Tipo de controlador | Escenario A, presa por reglas, semillas | IC 95 % de la diferencia dentro de +-0.08 | Diferencia −0,025 [IC 95 %: −0,099; 0,050]; p ajustado = ,730 | No |
| H3b3 | C3: depredador contra referencias | El depredador entrenado supera al interceptor por reglas. | Tipo de controlador | Escenario A, presa por reglas, semillas | Diferencia > 0 y p ajustado < 0.05 | Diferencia +0,068 [IC 95 %: −0,008; 0,143]; p ajustado = ,341 | No |
| H4 | Generalización | Los modelos entrenados solo en A conservan una ventaja positiva sobre el controlador aleatorio en los escenarios B y C, y la presa también la conserva contra el interceptor (oponente no visto). Son 7 pruebas: presa en B y C contra el perseguidor, presa en A, B y C contra el interceptor, depredador en B y C. | Escenario u oponente | Modelo entrenado, semillas | En cada una, diferencia > 0 y p ajustado < 0.05 | 7 pruebas; diferencias de 0,122 a 0,637; p ajustado máximo < ,001 | Sí (7 de 7) |

## Preguntas exploratorias (sin hipótesis previa)

- Cómo se comparan las redes entrenadas con las referencias por reglas en los escenarios B y C y contra el interceptor.
- Cómo se comporta la red de presa entrenada contra la red de depredador entrenada (ecosistema completo).
- Qué estrategias aprendieron las redes (se analizará viendo episodios y las salidas de la red).

Estas comparaciones se reportan como descriptivas, con su propia corrección de Holm, y no se usan para afirmar que una hipótesis se cumplió.

Resultados completados con experiments/completar_hipotesis.py a partir de results/fase4/comparaciones.csv. Las hipótesis y sus criterios no se modificaron. Fecha: 2026-11-21.
