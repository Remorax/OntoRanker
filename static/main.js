
'use strict';

;( function ( document, window, index )
{
	var inputs = document.querySelectorAll( '.inputfile' );
	Array.prototype.forEach.call( inputs, function( input )
	{
		var label	 = input.nextElementSibling,
			labelVal = label.innerHTML;

		input.addEventListener( 'change', function( e )
		{
			var fileName = '';
			if( this.files && this.files.length > 1 )
				fileName = ( this.getAttribute( 'data-multiple-caption' ) || '' ).replace( '{count}', this.files.length );
			else
				fileName = e.target.value.split( '\\' ).pop();

			if( fileName )
				label.querySelector( 'span' ).innerHTML = fileName;
			else
				label.innerHTML = labelVal;
		});

		// Firefox bug fix
		input.addEventListener( 'focus', function(){ input.classList.add( 'has-focus' ); });
		input.addEventListener( 'blur', function(){ input.classList.remove( 'has-focus' ); });
	});
}( document, window, 0 ));

function lock() {
	$(".ontolabels").prop("disabled", true);
	$(".params").prop("disabled", true);
	$(".params").removeAttr("required");
	$(".ontolabels").removeAttr("required");
}

function unlock() {
	$(".ontolabels").removeAttr("disabled");
	$(".params").removeAttr("disabled");
	$(".params").prop("required", true);
	$(".ontolabels").prop("required", true);
}
$("input[name='label-mode']").click(function () {
	$(".ontolabels").prop("disabled", ($(this).val() === 'auto') ? true:false);
	console.log($(this));
});

$("input[name='mode']").click(function () {
	$('#upload_buttons').css('display', ($(this).val() === 'upload') ? 'table':'none');
	$('#submit_para').css('display', ($(this).val() === 'upload') ? '':'none');
	$('#create_buttons').css('display', ($(this).val() === 'train') ? 'table':'none');
});
var allOntologies = [];
$('#file-3').on('change', function(e){

	$('#pitfall-row').css('display', 'none');
	$('#evaluate_oops').css('display', 'none');
	$("#error-scan").css('display', 'none');
	$("#final_create_buttons").css('display', 'none');
	$("#pitfall-table").css('display', 'none');

	var files = $('#file-3').prop("files");
	readOntologies(files);
	var names = $.map(files, function(val) { return val.name; });
	$.getJSON('/scrapePitfalls',
		function(data) {
			console.log(data.pitfalls);
			var pitfalls = "";
			for (var i in data.pitfalls)
			{
				var string = "<input id='" + data.pitfalls[i] + "' class='pitfall-cb' name='pitfall' type='checkbox'\
								value='" + data.pitfalls[i] + "'/>\
								<span class='pitfall-label'>" + data.pitfalls[i] + "</span>";
				pitfalls += string
			}
			$('#pitfall-row').css('display', '');
			$('#evaluate_oops').css("display", '');
			$("#pitfall-table").css('display', '');
			$("#pitfall-checkbox").html(pitfalls);
	 });
})

function readOntologies(ontologies) {
  var reader = new FileReader();  
  function readOntology(index) {
	if( index >= ontologies.length )
		return;
	var ontology = ontologies[index];
	reader.onload = function(e) {  
	  // get file content  
	  var ontology_text = e.target.result;
	  var ontology_name = ontology.name;
	  allOntologies.push({"name": ontology_name, "content": ontology_text});
	  readOntology(index+1)
	}
	reader.readAsBinaryString(ontology);
  }
  readOntology(0);
}

function trainModel()
{
	var Y_train = [];
	$('.ontolabels').each(function(){
		Y_train.push($(this).val());
	});
	console.log(Y_train);
	var data = {"Y": Y_train, "epsilon": $("#epsilon").val(), "C": $("#C").val(), "gamma": $("#gamma").val()};
	$("#train").prop("value","Training...");
	fetch("/train", {
		method: "POST",
		headers: {
			"Content-Type": "application/json"
		},
		body: JSON.stringify(data)
		}).then(function(response) {
			return response.json();
		}).then(function(data) {
			$("#final_create_buttons").css('display', '');
			$("#train").prop("value","Train model");
		});

}

$("#scan").on('click', function(e)
{
	var pitfalls = $('.pitfall-cb:checked').serialize();
	var requestData = {"pitfalls": pitfalls, "ontologies": allOntologies};
	$("#scan").prop("value","Scanning...");
	fetch("/oopsScan", {
		method: "POST",
		headers: {
			"Content-Type": "application/json"
		},
		body: JSON.stringify(requestData)
		}).then(function(response) {
			return response.json();
		}).then(function(data) {
			if (data["message"]!="Success!"){
				$("#error-scan").css('display', '');
				$("#scan").prop("value","Pitfall Scan");
			} else {
				var header = "<h3 id='pitfalls-title'>SCANNED PITFALLS </h3><br/>";

				var table = "<table id='train-table'>";
				table += "<tr class='th-row'><td>Ontology</td>";
				for (var i in data["pitfalls"]){
					table += "<td>" + data["pitfalls"][i] + "</td>";
				}
				table += "<td>Score</td></tr>";

				for (var i in data["featurevecs"]){
					var ontology = "<td>" + data["featurevecs"][i].join("</td><td>") + "</td>";
					var row = "<tr><td>" + data["ontologies"][i] + "</td>" + ontology + 
									"<td><input class='ontolabels' id='ontolabel" + i + "' value='" + parseFloat(data["labels"][i]).toFixed(2) + "' size=5px disabled/></td></tr>";
					table += row;
				}
				
				table += "</table>";
				var mode = "<table id='modes_table'><tr><td class='mode-radio'>\
					<input id='auto' name='label-mode' type='radio' value='auto' onclick='lock()' checked />\
					<span class='mode-label'>Auto</span></td>\
					<td class='mode-radio'>\
	    			<input id='manual' name='label-mode' type='radio' onclick='unlock()' value='manual'/>\
	    			<span class='mode-label'>Manual</span></td></tr></table>"
	    		var params = "<table id='params_table'><tr>\
								<td><label for='epsilon'>Epsilon</label><input class='params' id='epsilon' value='1' size=5px disabled/></td>\
								<td><label for='C'>C</label><input class='params' id='C' value='100' size=5px disabled/></td>\
								<td><label for='gamma'>Gamma</label><input class='params' id='gamma' value='0.01' size=5px disabled/></td>\
								</tr></table>"
				var train = "<p style='text-align: center; padding-top: 20px;'>\
								<input type='button' id='train' value='Train SVR model' onclick='trainModel()'></p>"
				var html = header+table+params+mode+train;
				$("#pitfall-table").html(html);
				$("#pitfall-table").css('display', '');
				$("#scan").prop("value","Pitfall Scan");
				console.log($(".ontolabels").val(), $("#epsilon").val(), $("#C").val(), $("#gamma").val());
			}
			
	});

})


// $("#download").on('click', function(e)
// {
// 	$.getJSON('/save',
// 		function(data) {
// 			console.log(data.message);
// 	 });
// })