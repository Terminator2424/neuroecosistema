# NeuroEcosistema: presas y depredadores con redes neuronales

Proyecto final integrador de la Electiva I de Profundización: Inteligencia Artificial.
Universidad Santo Tomás, Seccional Tunja. Autor: Edison Javier Gonzalez Velosa. Docente: Diego Alejandro Vela Beltrán.

### NeuroEcosistema
<img width="600" alt="NeuroEcosistema" src="https://github.com/user-attachments/assets/bbe5de5c-df49-4885-b1de-c21bd20ceb5b" />

### NeuroEcosistema - Individuos
<img width="600" alt="NeuroEcosistema - Individuos" src="https://github.com/user-attachments/assets/694b6ab4-0327-4b1c-b0c9-e5df4c8c80ad" />

## Qué es

Una simulación en 2D con plantas, presas y depredadores. Cada animal decide cómo moverse con una red neuronal (la presa percibe 6 cosas y el depredador 5; ambas devuelven un giro y una velocidad). Las redes no vienen programadas: se entrenan por neuroevolución (se prueban 30 redes, las mejores pasan y se mutan, durante 100 generaciones). Después se comparan contra agentes sin aprendizaje (aleatorio, por reglas, perseguidor e interceptor) en tres escenarios, con 30 semillas de evaluación y pruebas estadísticas pareadas.

Pregunta orientadora: en qué condiciones los agentes con redes neuronales mejoran su desempeño frente a estrategias sin aprendizaje.

## Resultados principales

| Comparación | Resultado |
|---|---|
| Presa entrenada frente a sin entrenar | +0,58 de fitness (p < ,001) |
| Depredador entrenado frente a sin entrenar | +0,45 de fitness (p < ,001) |
| Presa entrenada frente a presa por reglas (escenario A) | 0,79 frente a 0,72 |
| Red pequeña (80 parámetros) frente a base (206) | Equivalentes |
| Red grande (602 parámetros) frente a base | La grande supera a la base contra el perseguidor (contradijo lo esperado) |
| Depredador entrenado frente a perseguidor por reglas | Sin diferencia significativa; no se pudo demostrar equivalencia |

La presa entrenada se especializó en su oponente y su escenario: en el escenario de poca comida pierde contra reglas simples porque corre siempre a velocidad máxima y muere de hambre. Cada modelo proviene de una sola corrida de entrenamiento (limitación declarada). Los detalles, las 16 pruebas de hipótesis y su interpretación están en el informe y en docs/hipotesis.md; los datos, en results/fase4.

## Requisitos e instalación (Windows, PowerShell)

Probado con Python 3.12. Desde la carpeta del proyecto:

    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    pip install -r requirements.txt

## Cómo ejecutarlo

Pruebas automáticas:

    python -m pytest -q

Visor con las redes entrenadas (clic en un animal para ver qué percibe y qué decide su red):

    python experiments/ver_episodio.py

Teclas del visor: clic elegir animal, ESPACIO pausa, flecha derecha un paso, flechas arriba y abajo velocidad, N otra semilla, R reiniciar, 1 2 3 escenarios A B C, Z y X menos o más depredadores, V y B menos o más comida, P cambiar la presa, D cambiar el depredador, T estela, S guardar una captura en results/capturas, ESC salir.

Otros comandos:

    python experiments/revisar_referencias.py --n 10
    python experiments/calibrar_mundo.py
    python experiments/analizar_comportamiento.py --n 10

## Reproducir entrenamientos, evaluación y análisis

Un entrenamiento completo simula unos 9000 episodios (entre 13 y 15 minutos en un equipo con varios procesos).

    python experiments/entrenar.py --especie presa --nombre presa_A_base
    python experiments/entrenar.py --especie depredador --oponente aleatorio --nombre depre_A_etapa1
    python experiments/entrenar.py --especie depredador --oponente reglas --desde models/depre_A_etapa1 --nombre depre_A_base
    python experiments/entrenar.py --especie presa --ocultas "6,4" --nombre presa_A_pequena
    python experiments/entrenar.py --especie presa --ocultas "24,16" --nombre presa_A_grande
    python experiments/evaluar.py --presa-base models/presa_A_base --depre-etapa1 models/depre_A_etapa1 --depre-base models/depre_A_base --presa-pequena models/presa_A_pequena --presa-grande models/presa_A_grande
    python experiments/analizar.py
    python experiments/completar_hipotesis.py

La evaluación usa las semillas de evaluación final (5000 a 5029) y debe ejecutarse una sola vez; sus resultados ya están en results/fase4.

## Reproducibilidad

- Todo el azar usa semillas explícitas. Hay cuatro grupos separados: entrenamiento (desde 1000), validación (1900 a 1909), desarrollo y calibración (desde 2000) y evaluación final (5000 a 5029).
- El resultado de un entrenamiento no depende del número de procesos.
- Cada corrida guarda en models/<nombre> su configuración completa (config.yaml), el historial de fitness, la población y el resumen con las versiones de Python y NumPy.
- Los parámetros del mundo están en configs/base.yaml y en configs/escenarios (A, B y C). Los resultados numéricos pueden variar en centésimas entre equipos.

## Estructura del repositorio

- src/neuroeco: código fuente (config, world, controllers, runner, network, fitness, evolution, training, evaluation, estadistica, viewer)
- configs: configuración base y escenarios A, B y C
- experiments: comandos de entrenamiento, evaluación, análisis y visualización
- models: modelos entrenados (presa_A_base, presa_A_pequena, presa_A_grande, depre_A_etapa1, depre_A_base)
- results: datos y gráficas (referencias, calibración, evaluación final, comportamiento)
- docs: especificación de diseño, bitácora de decisiones (15), hipótesis y resultados, declaración de uso de IA
- tests: pruebas automáticas
- entrega: informe técnico (PDF y Word) y diapositivas de la exposición

## Uso de inteligencia artificial

El código fue generado con el asistente Claude (Anthropic) bajo la dirección del autor, quien ejecutó y supervisó la calibración, los entrenamientos, la evaluación y el análisis. La declaración completa, con lo aceptado, lo corregido y las validaciones, está en docs/uso_ia.md y en el informe.
