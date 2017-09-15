//////////////////////////////////////////////////////////////////////
///////// 1. Define Main Function ////////////////////////////////////
//////////////////////////////////////////////////////////////////////
////////// Author: Denis Torre
////////// Affiliation: Ma'ayan Laboratory, Icahn School of Medicine at Mount Sinai
////////// Based on Cite-D-Lite (https://github.com/MaayanLab/Cite-D-Lite).

function main() {

	// Locate parents on HTML page
	var parents = Page.locateParents();

	// Add Canned Analyses
	var cannedAnalysisInterfaces = Interfaces.add(parents);

	// Add event listeners for interactivity
	eventListener.main();

}

//////////////////////////////////////////////////////////////////////
///////// 2. Define Variables ////////////////////////////////////////
//////////////////////////////////////////////////////////////////////

//////////////////////////////////////////////////
////////// 1. Page ///////////////////////////////
//////////////////////////////////////////////////

///// Functions related to the webpage.

var Page = {

	//////////////////////////////
	///// 1. isDataMedSearchResults
	//////////////////////////////

	///// Returns true if the user is on a DataMed search results page, otherwise false

	isDataMedSearchResults: function() {
		return /.*search.php.*/.test(window.location.href);
	},

	//////////////////////////////
	///// 2. isDataMedLanding
	//////////////////////////////

	///// Returns true if the user is on a DataMed dataset landing page, otherwise false

	isDataMedLanding: function() {
		return /.*display-item.php.*/.test(window.location.href);
	},

	//////////////////////////////
	///// 3. isGeoSearchResults
	//////////////////////////////

	///// Returns true if the user is on a GEO search results page, otherwise false

	isGeoSearchResults: function() {
		return /.*gds\/\?term=.*/.test(window.location.href);
	},

	//////////////////////////////
	///// 4. isGeoDatasetLanding
	//////////////////////////////

	///// Returns true if the user is on a GEO dataset landing page, otherwise false

	isGeoDatasetLanding: function() {
		return /.*sites\/GDSbrowser\?acc=.*/.test(window.location.href);
	},

	//////////////////////////////
	///// 5. isGeoSeriesLanding
	//////////////////////////////

	///// Returns true if the user is on a GEO series landing page, otherwise false

	isGeoSeriesLanding: function() {
		return /.*geo\/query\/acc.cgi\?acc=.*/.test(window.location.href);
	},

	//////////////////////////////
	///// 6. locateParents
	//////////////////////////////

	///// Locates HTML elements which will be used to extract dataset accessions and append the interfaces

	locateParents: function() {
		var parents = {};
		if (Page.isDataMedSearchResults()) {
			$('.search-result li').each(function(i, elem){ parents[$(elem).find('span[data-original-title]').first().text().trim()] = $(elem) });
		} else if (Page.isDataMedLanding()) {
			$('#accordion-dataset').each(function(i, elem) { parents[$(elem).find('strong:contains(ID:)').parent().next().children(0).text().trim()] = $(elem) });
		} else if (Page.isGeoSearchResults()) {
			$('.rslt').each(function(i, elem) { parents[$(elem).find('.details').find('.lng_ln').last().find('a').text().trim()] = $(elem) });
		} else if (Page.isGeoDatasetLanding()) {
			$('#gds_details').each(function(i, elem) { parents[$(elem).find('th:contains(Reference Series:)').next().text().trim()] = $(elem) });
		} else if (Page.isGeoSeriesLanding()) {
			$('.acc').each(function(i, elem) { parents[$(elem).attr('id')] = $(elem).parents().eq(7) });
		}
		return parents;
	},

	//////////////////////////////
	///// 6. loadTooltips
	//////////////////////////////

	///// Loads tooltips

	loadTooltips: function() {

		$.widget("ui.tooltip", $.ui.tooltip, {
		    options: {
		        content: function () {
		            return $(this).prop('title');
		        }
		    }
		});

		$('.d2t-tooltip').each(function(i, elem) { $(elem).prev().attr('title', $(elem).remove().html());});

		$('.tool-icon').tooltip({
			classes:{'ui-tooltip':'tooltip-wrapper', 'ui-tooltip-content':'tooltip-black tooltip-bottom tool-icon-tooltip'},
			position:{my: 'center top', at: 'center bottom+5'},
			show:{duration: 0},
			hide:{duration: 0}
		});

		$('.canned-analysis-title').tooltip({
			classes:{'ui-tooltip':'tooltip-wrapper', 'ui-tooltip-content':'tooltip-black tooltip-bottom canned-analysis-title-tooltip'},
			position:{my: 'center top', at: 'center bottom+5'},
			show:{duration: 0},
			hide:{duration: 0}
		});

		$('.view-metadata').tooltip({
			classes:{'ui-tooltip':'tooltip-wrapper', 'ui-tooltip-content':'tooltip-black tooltip-right view-metadata-tooltip'},
			position:{my: 'left center', at: 'left+25 center'},
			show:{duration: 0},
			hide:{duration: 0}
		});

		$('.download-metadata').tooltip({
			classes:{'ui-tooltip':'tooltip-wrapper', 'ui-tooltip-content':'tooltip-white tooltip-right download-metadata-tooltip'},
			position:{my: 'left center', at: 'left+25 center'},
		    open:function(event, ui) { if (typeof(event.originalEvent) === 'undefined') { return false; }; var $id = $(ui.tooltip).attr('id'); $('div.ui-tooltip').not('#' + $id).remove(); },
		    close:function(event, ui) { ui.tooltip.hover(function() { $(this).stop(true).fadeTo(400, 1);; }, function() { $(this).remove(); }); },
			show:{duration: 0},
			hide:{duration: 500}
		});

		$('.share').tooltip({
			classes:{'ui-tooltip':'tooltip-wrapper', 'ui-tooltip-content':'tooltip-white tooltip-right share-tooltip'},
			position:{my: 'left center', at: 'left+25 center'},
		    open:function(event, ui) { if (typeof(event.originalEvent) === 'undefined') { return false; }; var $id = $(ui.tooltip).attr('id'); $('div.ui-tooltip').not('#' + $id).remove(); },
		    close:function(event, ui) { ui.tooltip.hover(function() { $(this).stop(true).fadeTo(400, 1); }, function() { $(this).fadeOut('400', function() { $(this).remove(); }); }); },
			show:{duration: 0},
			hide:{duration: 500}
		});

	},

	//////////////////////////////
	///// 8. addInterfaces
	//////////////////////////////

	///// Adds interfaces to parents

	addInterfaces: function(parents, cannedAnalysisInterfaces) {

		$.each(cannedAnalysisInterfaces, function(datasetAccession, datasetInterfaces) {
			if (Page.isDataMedSearchResults() || Page.isGeoSearchResults()) {
				parents[datasetAccession].append(datasetInterfaces['toolbar']);
			} else if (Page.isDataMedLanding()) {
				parents[datasetAccession].after('<div class="panel-group" id="accordion-cannedAnalyses" role="tablist" aria-multiselectable="true"><div class="panel panel-info"><div class="panel-heading" role="tab" id="heading-dataset-cannedAnalyses"><h4 class="panel-title"><a role="button" data-toggle="collapse" data-parent="#accordion-cannedAnalyses" data-target="#collapse-dataset-cannedAnalyses" href="#collapse-dataset-cannedAnalyses" aria-expanded="true" aria-controls="collapse-dataset-cannedAnalyses"><i class="fa fa-chevron-up"></i>&nbspCanned Analyses</a></h4></div><div id="collapse-dataset-cannedAnalyses" class="panel-collapse collapse in" role="tabpanel" aria-labelledby="heading-dataset-cannedAnalyses"><div class="panel-body">' + datasetInterfaces['tool_table'] + '</div></div></div></div>');
			} else if (Page.isGeoSeriesLanding()) {
				parents[datasetAccession].after('<div class="gse-landing-wrapper"><div class="gse-header">Canned Analyses</div>'+datasetInterfaces['tool_table']+'</div>');
			} else if (Page.isGeoDatasetLanding()) {
				// parents[datasetAccession].after('<div class="gds-header">Canned Analyses</div><div class="gds-landing-wrapper">'+datasetInterfaces['tool_table']+'</div>');
			}
		})

		this.loadTooltips();

	}
};

//////////////////////////////////////////////////
////////// 2. Interfaces /////////////////////////
//////////////////////////////////////////////////

///// Functions related to the interface.

var Interfaces = {

	//////////////////////////////
	///// 1. Create Interfaces
	//////////////////////////////

	///// Gets interfaces relevant to identified datasets from the API

	createInterface: function(apiData, datasetAccession) {

		// Get toolbar
		$toolbar = $('<div>', {'class': 'd2t-toolbar'})
						.append($('<div>', {'class': 'd2t-logo-wrapper'})
							.html($('<a>', {'href': '#'})
								.html($('<img>', {'class': 'd2t-logo', 'src': 'https://pbs.twimg.com/profile_images/745655614081220610/GA9jRnsf.jpg'}))))
						.append($('<div>', {'class': 'd2t-tool-icon-outer-wrapper'})
							.html($('<div>', {'class': 'd2t-tool-icon-inner-wrapper'})));

		$.each(apiData, function(toolName, toolData) { $toolbar.find('.d2t-tool-icon-inner-wrapper')
														.append($('<img>', {'class': 'd2t-tool-icon', 'src': 'https://pbs.twimg.com/profile_images/745655614081220610/GA9jRnsf.jpg', 'data-tool-name': toolName}))
														.append($('<div>', {'class': 'd2t-tool-icon-tooltip'})
															.append($('<div>', {'class': 'd2t-tool-icon-tooltip-name'}).html(toolName))
															.append($('<div>', {'class': 'd2t-tool-icon-tooltip-count'}).html(toolData['canned_analyses'].length+' analyses'))
															.append($('<div>', {'class': 'd2t-tool-icon-tooltip-description'}).html(toolData['tool_description'])) )});
$('<div>', {'class': ''})
		// Get tool info
		$toolinfo = $('<div>', {'class': 'd2t-tool-info-wrapper'})
						.append($('<div>', {'class': 'd2t-logo-wrapper'})
							.append($('<a>', {'href': '#'})
								.append($('<img>', {'class': 'd2t-back-arrow', 'src': 'https://image.freepik.com/free-icon/left-arrow-inside-a-circle_318-42520.jpg'}))));

		$.each(apiData, function(toolName, toolData) { $toolinfo.append($('<div>', {'id': datasetAccession+'-'+toolName+'-info', 'class': 'd2t-tool-info'})
																			.append($('<div>', {'class': 'd2t-tool-icon-outer-wrapper'})
																				.html($('<div>', {'class': 'd2t-tool-icon-inner-wrapper'})
																					.html($('<img>', {'class': 'd2t-tool-icon', 'src': 'https://pbs.twimg.com/profile_images/745655614081220610/GA9jRnsf.jpg'}))))
																			.append($('<div>', {'class': 'd2t-tool-info-text-wrapper'})
																				.append($('<div>', {'class': 'd2t-tool-info-tool-name'})
																					.html(toolName))
																				.append($('<div>', {'class': 'd2t-tool-info-tool-description'})
																					.html(toolData['tool_description'])))
																			)});

		// Get tables
		$tables = $('<div>', {'class': 'd2t-table-wrapper'});

		$.each(apiData, function(toolName, toolData) {
			$tables.append($('<table>', {'id': datasetAccession+'-'+toolName+'-table', 'class': 'd2t-table'})
				.append($('<thead>')
					.html($('<tr>')
						.append($('<th>', {'class': 'd2t-link-header'}).html('Link'))
						.append($('<th>', {'class': 'd2t-description-header'}).html('Description'))
						.append($('<th>', {'class': 'd2t-metadata-header'}).html('Metadata')))));
		});

		$.each(apiData, function(toolName, toolData){
			$.each(toolData['canned_analyses'], function(index, analysisData) {
				$tables.find('#'+datasetAccession+'-'+toolName+'-table')
					.append($('<tbody>')
						.append($('<tr>')
							.append($('<td>', {'class': 'd2t-link-col'})
								.html($('<a>', {'href': analysisData['canned_analysis_url']})
									.html($('<img>', {'class': 'd2t-link-icon', 'src': 'https://pbs.twimg.com/profile_images/745655614081220610/GA9jRnsf.jpg'}))))
							.append($('<td>', {'class': 'd2t-description-col'})
								.html(analysisData['canned_analysis_title']))
							.append($('<td>', {'class': 'd2t-metadata-col'})
								.html($('<i>', {'class': 'fa fa-info-circle'})))));
			});
		});

		return $('<div>', {'data-dataset-accession': datasetAccession, 'class': 'd2t-wrapper'})
					.append($toolbar)
					.append($toolinfo)
					.append($tables);
	},

	//////////////////////////////
	///// 2. Add
	//////////////////////////////

	///// Gets interfaces relevant to identified datasets from the API

	add: function(parents) {

		// Define self
		var self = this;
		var apiData = {"l1000cds2": {"tool_description": "sdfsdfsf", "tool_homepage_url": "NULLdfgdfgdfg", "canned_analyses": [{"canned_analysis_title": "Small molecules which mimic acute myocardial infarction", "canned_analysis_description": "The L1000 database was queried in order to identify small molecule perturbations which mimic the acute myocardial infarction gene expression signature in the  Heart left ventricles above LAD artery (AMI -induced by left coronary artery ligation) - 1 Hour  cell type.", "canned_analysis_url": "http://amp.pharm.mssm.edu/L1000CDS2/#/result/58d1c047e467bea600fb84f2", "metadata": {"do_id": "DOID:9408", "cell_type": "Heart left ventricles above LAD artery (AMI -induced by left coronary artery ligation) - 1 Hour", "pert_ids": "GSM12363, GSM12364, GSM12365", "direction": "mimic", "umls_cui": "C0155626", "curator": "cadimo", "disease_name": "acute myocardial infarction", "ctrl_ids": "GSM12322, GSM12323, GSM12324", "organism": "mouse", "creeds_id": "dz:1000"}}, {"canned_analysis_title": "Small molecules which reverse acute myocardial infarction", "canned_analysis_description": "The L1000 database was queried in order to identify small molecule perturbations which reverse the acute myocardial infarction gene expression signature in the  Heart left ventricles above LAD artery (AMI -induced by left coronary artery ligation) - 1 Hour  cell type.", "canned_analysis_url": "http://amp.pharm.mssm.edu/L1000CDS2/#/result/58d1c04ae467bea600fb84f4", "metadata": {"do_id": "DOID:9408", "cell_type": "Heart left ventricles above LAD artery (AMI -induced by left coronary artery ligation) - 1 Hour", "pert_ids": "GSM12363, GSM12364, GSM12365", "direction": "reverse", "umls_cui": "C0155626", "curator": "cadimo", "disease_name": "acute myocardial infarction", "ctrl_ids": "GSM12322, GSM12323, GSM12324", "organism": "mouse", "creeds_id": "dz:1000"}}, {"canned_analysis_title": "Small molecules which mimic acute myocardial infarction", "canned_analysis_description": "The L1000 database was queried in order to identify small molecule perturbations which mimic the acute myocardial infarction gene expression signature in the  Heart left ventricles above LAD artery (AMI -induced by left coronary artery ligation) - 4 Hours  cell type.", "canned_analysis_url": "http://amp.pharm.mssm.edu/L1000CDS2/#/result/58d1c04fe467bea600fb84f6", "metadata": {"do_id": "DOID:9408", "cell_type": "Heart left ventricles above LAD artery (AMI -induced by left coronary artery ligation) - 4 Hours", "pert_ids": "GSM12375, GSM12376, GSM12377", "direction": "mimic", "umls_cui": "C0155626", "curator": "cadimo", "disease_name": "acute myocardial infarction", "ctrl_ids": "GSM12334, GSM12335, GSM12336", "organism": "mouse", "creeds_id": "dz:1001"}}, {"canned_analysis_title": "Small molecules which reverse acute myocardial infarction", "canned_analysis_description": "The L1000 database was queried in order to identify small molecule perturbations which reverse the acute myocardial infarction gene expression signature in the  Heart left ventricles above LAD artery (AMI -induced by left coronary artery ligation) - 4 Hours  cell type.", "canned_analysis_url": "http://amp.pharm.mssm.edu/L1000CDS2/#/result/58d1c052e467bea600fb84f8", "metadata": {"do_id": "DOID:9408", "cell_type": "Heart left ventricles above LAD artery (AMI -induced by left coronary artery ligation) - 4 Hours", "pert_ids": "GSM12375, GSM12376, GSM12377", "direction": "reverse", "umls_cui": "C0155626", "curator": "cadimo", "disease_name": "acute myocardial infarction", "ctrl_ids": "GSM12334, GSM12335, GSM12336", "organism": "mouse", "creeds_id": "dz:1001"}}], "tool_icon_url": null}, "PAEA": {"tool_description": "EGGCELLENT\n", "tool_homepage_url": "NULLdfsgdsfgdfsg", "canned_analyses": [{"canned_analysis_title": "Enrichment analysis of genes dysregulated  in acute myocardial infarction", "canned_analysis_description": "An enrichment analysis was performed on the top most dyresgulated genes determined by applying the principal angle method to compare gene expression between cells affected by acute myocardial infarction and healthy control cells in the  Heart left ventricles above LAD artery (AMI -induced by left coronary artery ligation) - 1 Hour  cell type.", "canned_analysis_url": "http://amp.pharm.mssm.edu/PAEA?id=3085542", "metadata": {"do_id": "DOID:9408", "cell_type": "Heart left ventricles above LAD artery (AMI -induced by left coronary artery ligation) - 1 Hour", "pert_ids": "GSM12363, GSM12364, GSM12365", "curator": "cadimo", "umls_cui": "C0155626", "disease_name": "acute myocardial infarction", "ctrl_ids": "GSM12322, GSM12323, GSM12324", "organism": "mouse", "creeds_id": "dz:1000"}}], "tool_icon_url": null}};
		
		// Loop through parents
		$.each(parents, function(datasetAccession, resultDiv) {
			$(resultDiv).append(self.createInterface(apiData, datasetAccession));
			// $('.d2t-table').DataTable();
			// console.log(key);
			// $.ajax({
			// 	url: 'localhost:5000/datasets2tools/api/search',
			// 	data: {
			// 		'object_type': 'canned_analysis',
			// 		'dataset_accession': key
			// 	},
			// 	success: function(data) {
			// 		console.log(data);
			// 	}
			// });
		});

	}

};

//////////////////////////////////////////////////
////////// 3. eventListener //////////////////////
//////////////////////////////////////////////////

///// Event listeners.

var eventListener = {

	clickToolIcon: function() {
		$('.d2t-tool-icon').click(function(evt) {
			// Get click info
			datasetAccession = $(evt.target).parents('.d2t-wrapper').attr('data-dataset-accession');
			toolName = $(evt.target).attr('data-tool-name');

			// Hide and show
			$(evt.target).parents('.d2t-toolbar').css('display', 'none');

			$(evt.target).parents('.d2t-wrapper').find('.d2t-tool-info-wrapper').css('display', 'table');
			$(evt.target).parents('.d2t-wrapper').find('#'+datasetAccession+'-'+toolName+'-info').css('display', 'table');

			$(evt.target).parents('.d2t-wrapper').find('.d2t-table-wrapper').show();
			$(evt.target).parents('.d2t-wrapper').find('#'+datasetAccession+'-'+toolName+'-table').show();
		})
	},

	clickBackArrow: function() {
		$('.d2t-back-arrow').click(function(evt) {
			// Get click info
			datasetAccession = $(evt.target).parents('.d2t-wrapper').attr('data-dataset-accession');
			toolName = $(evt.target).attr('data-tool-name');

			// Hide and show
			$(evt.target).parents('.d2t-wrapper').find('.d2t-toolbar').css('display', 'table');
			$(evt.target).parents('.d2t-wrapper').find('.d2t-tool-info-wrapper').css('display', 'none');
			$(evt.target).parents('.d2t-wrapper').find('.d2t-tool-info').css('display', 'none');

			$(evt.target).parents('.d2t-wrapper').find('.d2t-table-wrapper').css('display', 'none');
			$(evt.target).parents('.d2t-wrapper').find('.d2t-table').css('display', 'none');
		})
	},

	//////////////////////////////
	///// . main
	//////////////////////////////

	///// Main wrapper.

	main: function() {
		this.clickToolIcon();
		this.clickBackArrow();
	}

};

//////////////////////////////////////////////////////////////////////
///////// 3. Run Main Function ///////////////////////////////////////
//////////////////////////////////////////////////////////////////////
main();
