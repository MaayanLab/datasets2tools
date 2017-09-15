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
			$('.search-result li').each(function(i, elem){ parents[$(elem).find('em:contains(ID:) + span').text().trim()] = $(elem) });
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
	///// 8. addInterfaces
	//////////////////////////////

	///// Adds interfaces to parents

		addInterface: function(analysisInterface, parentDiv) {

			if (Page.isDataMedSearchResults() || Page.isGeoSearchResults()) {
				parentDiv.append(analysisInterface);
			} else if (Page.isDataMedLanding()) {

				parentDiv.after($('<div>', {'id':'accordion-d2t', 'class': 'panel-group', 'role': 'tablist', 'aria-multiselectable': 'true'})
									.html($('<div>', {'class': 'panel panel-info'})
										.append($('<div>', {'id': 'heading-dataset-d2t', 'class': 'panel-heading', 'role': 'tab'})
											.html($('<h4>', {'class': 'panel-title'})
												.html($('<a>', {'role': 'button', 'data-toggle': 'collapse', 'data-parent': '#accordion-d2t', 'data-target': 'collapse-dataset-d2t', 'aria-expanded': 'true', 'aria-controls': 'collapse-dataset-d2t'})
													.append($('<i>', {'class': 'fa fa-chevron-up'}))
													.append(' Canned Analyses'))))
										.append($('<div>', {'id': 'collapse-dataset-d2t', 'class': 'panel-collapse collapse in', 'role': 'tabpanel', 'aria-labelledby': 'heading-dataset-d2t'})
											.html($('<div>', {'class': 'panel-body'})
												.html(analysisInterface)))));

			} else if (Page.isGeoSeriesLanding()) {

				parentDiv.after($('<table>', {'id': 'd2t-landing-wrapper', 'class': 'd2t-geo d2t-gse'})
									.html($('<tbody>')
										.append($('<tr>')
											.html($('<th>')
												.html('Canned Analyses')))
										.append($('<tr>')
											.html($('<td>')
												.html(analysisInterface)))))

			} else if (Page.isGeoDatasetLanding()) {

				parentDiv.after($('<table>', {'id': 'd2t-landing-wrapper', 'class': 'd2t-geo d2t-gds gds_panel'})
									.html($('<tbody>')
										.append($('<tr>', {'class': 'caption'})
											.html($('<th>')
												.html('Canned Analyses')))
										.append($('<tr>')
											.html($('<td>')
												.html(analysisInterface)))));
			}
	}
};

//////////////////////////////////////////////////
////////// 2. Interfaces /////////////////////////
//////////////////////////////////////////////////

///// Functions related to the interface.

var Interfaces = {

	//////////////////////////////
	///// 1. Create Search Interface
	//////////////////////////////

	///// Gets interfaces relevant to identified datasets from the API on search pages

	createSearchInterface: function(apiData, datasetAccession) {

		// Get page class
		if (Page.isDataMedSearchResults() || Page.isDataMedLanding()) {
			pageClass = 'datamed'
		} else if (Page.isGeoSearchResults() || Page.isGeoSeriesLanding() || Page.isGeoDatasetLanding()) {
			pageClass = 'geo'
		}

		// Get toolbar
		$toolbar = $('<div>', {'class': 'd2t-toolbar'})
						.append($('<div>', {'class': 'd2t-logo-wrapper'})
							.html($('<a>', {'href': '#'})
								.html($('<img>', {'class': 'd2t-logo', 'src': 'https://pbs.twimg.com/profile_images/745655614081220610/GA9jRnsf.jpg'}))))
						.append($('<div>', {'class': 'd2t-tool-icon-outer-wrapper'})
							.html($('<div>', {'class': 'd2t-tool-icon-inner-wrapper'})));

		$.each(apiData, function(toolName, toolData) { $toolbar.find('.d2t-tool-icon-inner-wrapper')
														.append($('<img>', {'class': 'd2t-tool-icon', 'src': 'https://pbs.twimg.com/profile_images/745655614081220610/GA9jRnsf.jpg', 'data-tool-name': toolName, 'data-toggle': "d2t-tooltip", 'data-placement': "top", 'data-html': "true", 'data-original-title': "<div class='d2t-tool-icon-tooltip'><div class='d2t-tool-icon-tooltip-name'>"+toolName+"</div><div class='d2t-tool-icon-tooltip-count'>"+toolData['canned_analyses'].length+" analyses</div><div class='d2t-tool-icon-tooltip-description'>"+toolData['tool_description']+"</div></div>"}))});

		// Get tool info
		$toolinfo = $('<div>', {'class': 'd2t-tool-info-wrapper'})
						.append($('<div>', {'class': 'd2t-logo-wrapper'})
								.append($('<img>', {'class': 'd2t-back-arrow', 'src': 'https://image.freepik.com/free-icon/left-arrow-inside-a-circle_318-42520.jpg'})));

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

			// Table header
			$tables.append($('<table>', {'id': datasetAccession+'-'+toolName+'-table', 'class': 'd2t-table'})
				.append($('<thead>')
					.html($('<tr>')
						.append($('<th>', {'class': 'd2t-link-header'}).html('Link'))
						.append($('<th>', {'class': 'd2t-description-header'}).html('Description'))
						.append($('<th>', {'class': 'd2t-metadata-header'}).html('Metadata')))));

			// Table rows
			$.each(toolData['canned_analyses'], function(index, analysisData) {
				$tables.find('#'+datasetAccession+'-'+toolName+'-table')
					.append($('<tbody>')
						.append($('<tr>')
							.append($('<td>', {'class': 'd2t-link-col'})
								.html($('<a>', {'href': analysisData['canned_analysis_url']})
									.html($('<img>', {'class': 'd2t-link-icon', 'src': 'https://pbs.twimg.com/profile_images/745655614081220610/GA9jRnsf.jpg'}))))
							.append($('<td>', {'class': 'd2t-description-col'})
								.html($('<span>', {'data-toggle': "d2t-tooltip", 'data-placement': "top", 'data-html': "true", 'data-original-title': "<div class='d2t-canned-analysis-description-tooltip'>"+analysisData['canned_analysis_description']+""})
									.html(analysisData['canned_analysis_title'])))
							.append($('<td>', {'class': 'd2t-metadata-col'})
								.html($('<i>', {'class': 'fa fa-info-circle', 'data-toggle': "d2t-tooltip", 'data-placement': "top", 'data-html': "true"})))));

				// Row metadata tooltips
				metadataTooltip = $('<div>', {'class': 'd2t-metadata-tooltip'}).html($('<ul>', {'class': 'd2t-metadata-list'}));
				$.each(analysisData['metadata'], function(termName, termValue) {
					metadataTooltip.find('ul').append($('<li>')
						.append($('<span>', {'class': 'd2t-metadata-term'})
							.html(termName+':'))
						.append($('<span>', {'class': 'd2t-metadata-value'})
							.html(termValue)))
				});
				$tables.find('#'+datasetAccession+'-'+toolName+'-table i').last().attr('data-original-title', metadataTooltip.html())

			});

		});

		// Return
		return $('<div>', {'data-dataset-accession': datasetAccession, 'class': 'd2t-wrapper d2t-' + pageClass})
					.append($toolbar)
					.append($toolinfo)
					.append($tables);
	},

	//////////////////////////////
	///// 2. Create Landing Interface
	//////////////////////////////

	///// Gets interfaces relevant to identified datasets from the API on landing pages

	createLandingInterface: function(apiData, datasetAccession) {
		
		// Get tool table
		$toolTable = $('<table>', {'class': 'd2t-tool-table'})
						.append($('<thead>')
							.html($('<tr>')
								.append($('<th>', {'class': 'd2t-tool-name-header'}).html('Tool'))
								.append($('<th>', {'class': 'd2t-tool-description-header'}).html('Description'))
								.append($('<th>', {'class': 'd2t-canned-analyses-header'}).html('Analyses'))))
						.append($('<tbody>'));
		$.each(apiData, function(toolName, toolData) {
			$toolTable.find('tbody')
				.append($('<tr>')
					.append($('<td>')
						.html(toolName))
					.append($('<td>')
						.html(toolData['tool_description']))
					.append($('<td>')
						.html(toolData['canned_analyses'].length)))
		});

		// Get analysis tables
		$analysisTables = $('<div>')

		// Return
		return $('<div>')
					.append($toolTable)
					.append($analysisTables);
	},

	//////////////////////////////
	///// 3. Add
	//////////////////////////////

	///// Creates and add interfaces

	add: function(parents) {

		// Define self
		var self = this;
		var apiData = {"l1000cds2": {"tool_description": "sdfsdfsf", "tool_homepage_url": "NULLdfgdfgdfg", "canned_analyses": [{"canned_analysis_title": "Small molecules which mimic acute myocardial infarction", "canned_analysis_description": "The L1000 database was queried in order to identify small molecule perturbations which mimic the acute myocardial infarction gene expression signature in the  Heart left ventricles above LAD artery (AMI -induced by left coronary artery ligation) - 1 Hour  cell type.", "canned_analysis_url": "http://amp.pharm.mssm.edu/L1000CDS2/#/result/58d1c047e467bea600fb84f2", "metadata": {"do_id": "DOID:9408", "cell_type": "Heart left ventricles above LAD artery (AMI -induced by left coronary artery ligation) - 1 Hour", "pert_ids": "GSM12363, GSM12364, GSM12365", "direction": "mimic", "umls_cui": "C0155626", "curator": "cadimo", "disease_name": "acute myocardial infarction", "ctrl_ids": "GSM12322, GSM12323, GSM12324", "organism": "mouse", "creeds_id": "dz:1000"}}, {"canned_analysis_title": "Small molecules which reverse acute myocardial infarction", "canned_analysis_description": "The L1000 database was queried in order to identify small molecule perturbations which reverse the acute myocardial infarction gene expression signature in the  Heart left ventricles above LAD artery (AMI -induced by left coronary artery ligation) - 1 Hour  cell type.", "canned_analysis_url": "http://amp.pharm.mssm.edu/L1000CDS2/#/result/58d1c04ae467bea600fb84f4", "metadata": {"do_id": "DOID:9408", "cell_type": "Heart left ventricles above LAD artery (AMI -induced by left coronary artery ligation) - 1 Hour", "pert_ids": "GSM12363, GSM12364, GSM12365", "direction": "reverse", "umls_cui": "C0155626", "curator": "cadimo", "disease_name": "acute myocardial infarction", "ctrl_ids": "GSM12322, GSM12323, GSM12324", "organism": "mouse", "creeds_id": "dz:1000"}}, {"canned_analysis_title": "Small molecules which mimic acute myocardial infarction", "canned_analysis_description": "The L1000 database was queried in order to identify small molecule perturbations which mimic the acute myocardial infarction gene expression signature in the  Heart left ventricles above LAD artery (AMI -induced by left coronary artery ligation) - 4 Hours  cell type.", "canned_analysis_url": "http://amp.pharm.mssm.edu/L1000CDS2/#/result/58d1c04fe467bea600fb84f6", "metadata": {"do_id": "DOID:9408", "cell_type": "Heart left ventricles above LAD artery (AMI -induced by left coronary artery ligation) - 4 Hours", "pert_ids": "GSM12375, GSM12376, GSM12377", "direction": "mimic", "umls_cui": "C0155626", "curator": "cadimo", "disease_name": "acute myocardial infarction", "ctrl_ids": "GSM12334, GSM12335, GSM12336", "organism": "mouse", "creeds_id": "dz:1001"}}, {"canned_analysis_title": "Small molecules which reverse acute myocardial infarction", "canned_analysis_description": "The L1000 database was queried in order to identify small molecule perturbations which reverse the acute myocardial infarction gene expression signature in the  Heart left ventricles above LAD artery (AMI -induced by left coronary artery ligation) - 4 Hours  cell type.", "canned_analysis_url": "http://amp.pharm.mssm.edu/L1000CDS2/#/result/58d1c052e467bea600fb84f8", "metadata": {"do_id": "DOID:9408", "cell_type": "Heart left ventricles above LAD artery (AMI -induced by left coronary artery ligation) - 4 Hours", "pert_ids": "GSM12375, GSM12376, GSM12377", "direction": "reverse", "umls_cui": "C0155626", "curator": "cadimo", "disease_name": "acute myocardial infarction", "ctrl_ids": "GSM12334, GSM12335, GSM12336", "organism": "mouse", "creeds_id": "dz:1001"}}], "tool_icon_url": null}, "PAEA": {"tool_description": "EGGCELLENT\n", "tool_homepage_url": "NULLdfsgdsfgdfsg", "canned_analyses": [{"canned_analysis_title": "Enrichment analysis of genes dysregulated  in acute myocardial infarction", "canned_analysis_description": "An enrichment analysis was performed on the top most dyresgulated genes determined by applying the principal angle method to compare gene expression between cells affected by acute myocardial infarction and healthy control cells in the  Heart left ventricles above LAD artery (AMI -induced by left coronary artery ligation) - 1 Hour  cell type.", "canned_analysis_url": "http://amp.pharm.mssm.edu/PAEA?id=3085542", "metadata": {"do_id": "DOID:9408", "cell_type": "Heart left ventricles above LAD artery (AMI -induced by left coronary artery ligation) - 1 Hour", "pert_ids": "GSM12363, GSM12364, GSM12365", "curator": "cadimo", "umls_cui": "C0155626", "disease_name": "acute myocardial infarction", "ctrl_ids": "GSM12322, GSM12323, GSM12324", "organism": "mouse", "creeds_id": "dz:1000"}}], "tool_icon_url": null}};
		
		// Loop through parents
		$.each(parents, function(datasetAccession, parentDiv) {

			// Create interfaces
			if (Page.isDataMedSearchResults() || Page.isGeoSearchResults()) {
				analysisInterface = self.createSearchInterface(apiData, datasetAccession);
			} else if (Page.isDataMedLanding() || Page.isGeoSeriesLanding() || Page.isGeoDatasetLanding()) {
				analysisInterface = self.createLandingInterface(apiData, datasetAccession);
			}

			// Add
			Page.addInterface(analysisInterface, parentDiv);

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

		// Tables and tooltips
		$('.d2t-table').DataTable({});
		$("[data-toggle='d2t-tooltip']").tooltip();

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
			$(evt.target).parents('.d2t-wrapper').find('#'+datasetAccession+'-'+toolName+'-table_wrapper').show();
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
			$(evt.target).parents('.d2t-wrapper').find('.dataTables_wrapper').css('display', 'none');
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
