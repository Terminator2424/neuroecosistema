# Resultados de las hipótesis (generado por experiments/analizar.py)

| ID | Comparación | Criterio | Diferencia [IC 95 %] | p de Wilcoxon (ajustado) | Veredicto |
|----|-------------|----------|----------------------|--------------------------|-----------|
| H1a | red_entrenada frente a red_sin_entrenar (escenario A, oponente perseguidor, fitness_presa) | diferencia de fitness >= 0.20 y p ajustado < 0.01 | 0.575 [0.550; 0.600] | 1.9e-09 (3.7e-09) | CUMPLE |
| H1b | red_entrenada frente a red_sin_entrenar (escenario A, oponente reglas, fitness_depredador) | diferencia de fitness >= 0.20 y p ajustado < 0.01 | 0.453 [0.395; 0.511] | 1.9e-09 (3.7e-09) | CUMPLE |
| H2a | red_grande frente a red_entrenada (escenario A, oponente perseguidor, fitness_presa) | la red grande no supera a la base (diferencia <= 0 o p ajustado >= 0.05) | 0.061 [0.030; 0.093] | 0.00015 (0.00031) | NO CUMPLE |
| H2b | red_pequena frente a red_entrenada (escenario A, oponente perseguidor, fitness_presa) | IC 95 % de la diferencia dentro de +-0.05 | 0.014 [-0.015; 0.044] | 0.54 (0.54) | CUMPLE |
| H3a1 | red_entrenada frente a reglas (escenario A, oponente perseguidor, fitness_presa) | diferencia >= 0.05 y p ajustado < 0.05 | 0.077 [0.044; 0.109] | 4.4e-05 (0.00013) | CUMPLE |
| H3a2 | red_entrenada frente a aleatoria (escenario A, oponente perseguidor, fitness_presa) | diferencia >= 0.30 y p ajustado < 0.01 | 0.565 [0.535; 0.594] | 1.9e-09 (9.3e-09) | CUMPLE |
| H3b1 | red_entrenada frente a aleatorio (escenario A, oponente reglas, fitness_depredador) | diferencia >= 0.30 y p ajustado < 0.01 | 0.449 [0.390; 0.507] | 1.9e-09 (9.3e-09) | CUMPLE |
| H3b2 | red_entrenada frente a perseguidor (escenario A, oponente reglas, fitness_depredador) | equivalencia: IC 95 % de la diferencia dentro de +-0.08 | -0.025 [-0.099; 0.050] | 0.73 (0.73) | NO CUMPLE |
| H3b3 | red_entrenada frente a interceptor (escenario A, oponente reglas, fitness_depredador) | diferencia > 0 y p ajustado < 0.05 | 0.068 [-0.008; 0.143] | 0.17 (0.34) | NO CUMPLE |
| H4-presa-B | red_entrenada frente a aleatoria (escenario B, oponente perseguidor, fitness_presa) | diferencia > 0 y p ajustado < 0.05 | 0.213 [0.197; 0.230] | 1.9e-09 (1.3e-08) | CUMPLE |
| H4-presa-C | red_entrenada frente a aleatoria (escenario C, oponente perseguidor, fitness_presa) | diferencia > 0 y p ajustado < 0.05 | 0.556 [0.522; 0.590] | 1.9e-09 (1.3e-08) | CUMPLE |
| H4-presa-A-int | red_entrenada frente a aleatoria (escenario A, oponente interceptor, fitness_presa) | diferencia > 0 y p ajustado < 0.05 (oponente no visto en el entrenamiento) | 0.353 [0.326; 0.380] | 1.9e-09 (1.3e-08) | CUMPLE |
| H4-presa-B-int | red_entrenada frente a aleatoria (escenario B, oponente interceptor, fitness_presa) | diferencia > 0 y p ajustado < 0.05 (oponente no visto en el entrenamiento) | 0.122 [0.105; 0.139] | 1.9e-09 (1.3e-08) | CUMPLE |
| H4-presa-C-int | red_entrenada frente a aleatoria (escenario C, oponente interceptor, fitness_presa) | diferencia > 0 y p ajustado < 0.05 (oponente no visto en el entrenamiento) | 0.184 [0.160; 0.209] | 1.9e-09 (1.3e-08) | CUMPLE |
| H4-depre-B | red_entrenada frente a aleatorio (escenario B, oponente reglas, fitness_depredador) | diferencia > 0 y p ajustado < 0.05 | 0.432 [0.396; 0.468] | 1.9e-09 (1.3e-08) | CUMPLE |
| H4-depre-C | red_entrenada frente a aleatorio (escenario C, oponente reglas, fitness_depredador) | diferencia > 0 y p ajustado < 0.05 | 0.637 [0.601; 0.673] | 1.9e-09 (1.3e-08) | CUMPLE |
