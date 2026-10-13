Final project for Declarative Programming.
-------------------------------------------
📚Objective: Create a system that suggests books or movies to the user based on their previous preferences.

Tools:

Pandas to manage user and rating datasets.

NumPy to create similarity matrices.

Matplotlib to display recommendations and popularity analysis. 

AI Algorithm: Collaborative filtering or content-based models.(INFO: https://www.ibm.com/es-es/think/topics/collaborative-filtering & https://es.wikipedia.org/wiki/Filtrado_colaborativo)

INCLUDE GRAPHICAL INTERFACE

Requirements in are in their corresponding file (must use venv)

> python -m venv .venv

>  . .venv\Scripts\Activate.ps1

> pip install -r requirements.txt

For this academic version, the data is loaded into memory to facilitate evaluation without external dependencies. However, the engine (recommender_core.py) is designed in a modular way to scale and consume massive datasets from CSV files (e.g., MovieLens Dataset) or SQL databases

---

uvicorn main:app --reload

scalene benchmark.py

scalene --html --outfile reporte_scalene.html benchmark.py