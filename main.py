import os
#import magic
import urllib.request
from app import app
from flask import Flask, flash, request, redirect, render_template, jsonify, send_file
from werkzeug.utils import secure_filename
import requests, xmljson, pickle, re
from xml.dom import minidom
from bs4 import BeautifulSoup
import numpy as np, math
from sklearn.svm import SVR
import pickle


ALLOWED_EXTENSIONS = set(['owl', "rdf", "sav"])
ontologies = []
training_dataset = []
clf = None
allAttribs = []
evaluatedPitfalls = []


def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_model(filename):	
	return '.' in filename and filename.rsplit('.', 1)[1].lower() == "sav"

@app.route('/')
def upload_form():
	return render_template('upload.html')

@app.route('/scrapePitfalls')
def scrapePitfalls():
	catalogue = requests.get("http://oops.linkeddata.es/catalogue.jsp").content
	soup = BeautifulSoup(catalogue, "lxml")
	pitfalls = soup.find("ul").findAll("li")
	parsedPitfalls = [el.text.strip()[:3] if el.text.strip()[0]!="(" else re.search("\).+", el.text.strip()).group()[1:].strip()[:3] for el in pitfalls]
	return jsonify({"pitfalls": parsedPitfalls})

@app.route('/oopsScan', methods=['POST'])
def oops_request():
	if request.method == 'POST':
		
		req = request.get_json()
		pitfalls = [el.split("=")[1] for el in req['pitfalls'].split("&")]
		ontologies = req['ontologies']

		allResults = []

		difficultyDict = {"Minor": 1, "Important": 2, "Critical": 3}
		importanceDict = {}
		ontoNames = []
		for ontology in ontologies:
			ontoText = ontology["content"]
			ontoName = ontology["name"]
			attribs, results = OOPSparser(ontoText, pitfalls)
			for pitfall in attribs:
				importanceDict[pitfall[0]] = difficultyDict[pitfall[-2]]
			ontoNames.append(ontoName)
			allResults.append(np.array(results))
		allResults = np.array(allResults)
		global training_dataset
		training_dataset = np.array([allResults[:,i] for i in range(allResults.shape[1]) if any(allResults[:,i])]).T
		files = [pitfalls[i] for i in range(allResults.shape[1]) if any(allResults[:,i])]
		difficulties = [importanceDict[file] for file in files]
		if not files:
			return jsonify({"results": [], "message": "No pitfalls detected. Please choose more pitfalls"})
		weightMatrix = [difficulties + elem for elem in np.array([training_dataset[:,i]/(math.ceil(max(training_dataset[:,i])/5) * 5) for i in range(training_dataset.shape[1])]).T]
		weightMatrix = np.array([row ** difficulties for row in weightMatrix])
		Y_train = np.sum(weightMatrix, axis=1)
		global evaluatedPitfalls
		evaluatedPitfalls = files
		print ("Training:", training_dataset)
		return jsonify({"ontologies": ontoNames, "featurevecs": [[str(s) for s in result] for result in training_dataset.tolist()], "labels": [str(y) for y in Y_train.tolist()], "pitfalls": files, "message": "Success!"})

@app.route("/train", methods=['POST'])
def train():
	if request.method == 'POST':
		req = request.get_json()

		global training_dataset
		print ("2. Training:", training_dataset)
		X_train = training_dataset
		Y_train = np.array([float(x) for x in req['Y']])
		epsilon, C, gamma = float(req['epsilon']), float(req['C']), float(req['gamma'])
		global clf
		clf = SVR(gamma=gamma, C=C, epsilon=epsilon)
		print (X_train, Y_train, type(X_train[0]), type(X_train[0][0]))
		clf.fit(X_train, Y_train) 
		return jsonify({"message": "Success!"})

@app.route("/save", methods=['GET'])
def save():
	filename = 'static/ontoranker.sav'
	saveList = [evaluatedPitfalls, clf]
	pickle.dump(saveList, open(filename, 'wb'))
	response = send_file('static/ontoranker.sav', attachment_filename='model.sav', as_attachment=True)
	response.headers["x-filename"] = "model.sav"
	response.headers["Access-Control-Expose-Headers"] = 'x-filename'
	return response

@app.route('/', methods=['POST'])
def upload_file():
	if request.method == 'POST':
		# check if the post request has the files part
		valid_test, valid_model = False, False
		print ("going here")
		if 'files[]' not in request.files or "model" not in request.files:
			flash('No file part')
			return redirect(request.url)
		files = request.files.getlist('files[]')

		for file in files:
			print (file)
			if file and allowed_file(file.filename):
				filename = secure_filename(file.filename)
				valid_test = True
				file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

		model = request.files["model"]
		if model and allowed_model(model.filename):
			valid_model = True
			modelname = secure_filename(model.filename)
			model.save(os.path.join(app.config['UPLOAD_FOLDER'], modelname))

		if not valid_model or not valid_test:
			return redirect(request.url)
		flash('File(s) successfully uploaded')
		global ontologies
		ontologies = [f for f in os.listdir('./uploads') if f.endswith('.owl')]
		print (ontologies)
		return redirect('/analysis')

@app.route('/detailed/<ontoID>')
def show_pitfalls(ontoID):
	ontoID = int(ontoID) - 1
	if not allAttribs or not ontologies:
		return redirect("/")
	return render_template("detailed.html", attribs=allAttribs[ontoID], name=ontologies[ontoID])

def OOPSparser(text, pitfalls):
	xml = """<?xml version="1.0" encoding="UTF-8"?>
		<OOPSRequest>
			<OntologyURI></OntologyURI>
			<OntologyContent>""" + text + """</OntologyContent>
			<Pitfalls>""" + ",".join(pitfalls) + """</Pitfalls>
			<OutputFormat>XML</OutputFormat>
		</OOPSRequest>"""
	headers = {'Content-Type': 'application/xml'} # set what your server accepts
	response = requests.post('http://oops-ws.oeg-upm.net/rest', data=xml.encode("utf-8"), headers=headers).text
	parsedResponse = minidom.parseString(response)
	allPitfalls = parsedResponse.getElementsByTagName("oops:Pitfall")
	results = [0 for i in range(len(pitfalls))]
	attribs = []
	for pitfall in allPitfalls:
		codename = pitfall.getElementsByTagName("oops:Code")[0].childNodes[0].nodeValue
		description = pitfall.getElementsByTagName("oops:Description")[0].childNodes[0].nodeValue
		importance = pitfall.getElementsByTagName("oops:Importance")[0].childNodes[0].nodeValue
		name = pitfall.getElementsByTagName("oops:Name")[0].childNodes[0].nodeValue
		number = pitfall.getElementsByTagName("oops:NumberAffectedElements")[0].childNodes[0].nodeValue
		idx = pitfalls.index(codename)
		results[idx] += int(number)
		attribs.append((codename, name, description, importance, number))
	
	return (attribs, results)

@app.route('/analysis')
def show_analysis():
	clf_name = [f for f in os.listdir('./uploads') if f.endswith('.sav')][0]
	pitfalls, clf = pickle.load(open("uploads/" + clf_name, 'rb'))
	allResults = []
	global allAttribs, ontologies	
	for testontology in ontologies:
		f = open("uploads/" + testontology,"r").read()
		attribs, results = OOPSparser(f, pitfalls)
		allAttribs.append(attribs)
		allResults.append(results)
	X_test = np.array([np.array(response) for response in allResults])
	
	predictions = [round(pred, 2) for pred in clf.predict(X_test)]
	rankList = sorted(list(zip(ontologies, predictions)), key=lambda l: l[1])
	output = zip(list(range(1,len(ontologies)+1)), rankList)

	# output = [
	# 	("1", ("test_minor.owl", "104.57662846187996")),
	# 	("2", ("test_important.owl",	"109.47008328520329")),
	# 	("3", ("test_critical.owl",	"120.61679591478796"))
	# ]
	

	return render_template("analysis.html", ranks=output, attribs=allAttribs)		

if __name__ == "__main__":
	app.run()