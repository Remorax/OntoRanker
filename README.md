# OntoEvaluator User Application

An application to score and rank ontologies based on syntactic and semantic quality

## Setup

- Run `export FLASK_APP=main.py` from the `OntoEvaluatorApp` directory
- Next, run `flask run`
- Navigate to http://localhost:5000/

## How to Use 

1. First, you need a trained SVM model to score these ontologies. 
	- A sample trained model is available over [here](https://github.com/Remorax/OntoEvaluator/blob/master/OntoEvaluatorApp/ontoranker.sav). 
	- The code to retrain the model according to your own requirements is available [here](https://github.com/Remorax/OntoEvaluator/blob/master/OntoEvaluator.ipynb)

2. Next, you need a set of ontologies to be ranked. A sample set of ontologies is available over [here](https://github.com/Remorax/OntoEvaluator/tree/master/ontologies/test).

3. Finally, upload the trained SVM model and the ontologies to be ranked in the OntoEvaluator Application by navigating to http://localhost:5000/

4. You get a list of scored and ranked ontologies. Click on each ontology to get a detailed analysis of its quality in terms of the pitfalls present.