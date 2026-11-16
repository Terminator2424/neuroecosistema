# NeuroEcosistema: depredadores y presas

Proyecto final integrador. Electiva I de Profundización: Inteligencia Artificial.
Universidad Santo Tomás, Seccional Tunja.

## Instalación (Windows, PowerShell)

    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    pip install -r requirements.txt

## Uso (Fases 2 a 4: simulación, calibración, entrenamiento y experimentos)

Pruebas automáticas:

    python -m pytest -q

Ver un episodio en una ventana (agentes de referencia, sin aprendizaje):

    python experiments/ver_episodio.py
    python experiments/ver_episodio.py --escenario C --depredador interceptor --semilla 7

Revisión de los agentes de referencia (guarda results/fase2_referencias.csv):

    python experiments/revisar_referencias.py --n 10

Calibración del mundo (criterios K1 a K9, guarda results/fase2b_calibracion.csv):

    python experiments/calibrar_mundo.py

Entrenamiento por neuroevolución (guarda todo en models/<nombre>/):

    python experiments/entrenar.py --especie presa --rapido
    python experiments/entrenar.py --especie presa --nombre presa_A_base
    python experiments/entrenar.py --especie depredador --oponente aleatorio --nombre depre_A_etapa1
    python experiments/entrenar.py --especie depredador --oponente reglas --desde models/depre_A_etapa1 --nombre depre_A_base

Arquitecturas alternativas para la comparación C2:

    python experiments/entrenar.py --especie presa --ocultas 6,4 --nombre presa_A_pequena
    python experiments/entrenar.py --especie presa --ocultas 24,16 --nombre presa_A_grande

Evaluación final (usa las semillas 5000 a 5029; las hipótesis deben estar escritas antes) y análisis:

    python experiments/evaluar.py --presa-base models/presa_A_base --depre-etapa1 models/depre_A_etapa1 --depre-base models/depre_A_base --presa-pequena models/presa_A_pequena --presa-grande models/presa_A_grande
    python experiments/analizar.py

Ver modelos entrenados:

    python experiments/ver_episodio.py --modelo-presa models/presa_A_base --modelo-depredador models/depre_A_base

## Estructura

- src/neuroeco: código fuente (config, world, controllers, runner, viewer, network, fitness, evolution, training, evaluation, estadistica)
- configs: configuración base y escenarios A, B y C
- experiments: scripts de experimentos y visualización
- results: datos y gráficas (CSV, PNG)
- models: modelos entrenados
- docs: especificación de diseño, bitácora, hipótesis y declaración de uso de IA
- tests: pruebas

(Se completa conforme avance el proyecto.)