//////////////////////////////////////////////////
//////////////////////////////////////////////////
////////// Datasets2Tools Website Scripts ////////
//////////////////////////////////////////////////
//////////////////////////////////////////////////

///////////////////////////////////
////////// 1. Main ////////////////
///////////////////////////////////

var entry_point = '/datasets2tools-dev';

function main() {

	homepage.main();
	keywordSearch.main();
	developmentSearch.main();
	advancedSearch.main();
	uploadForm.main();
	metadataExplorer.main();
	help.main();
	analyze.main();

};

///////////////////////////////////
////////// 2. Scripts /////////////
///////////////////////////////////

//////////////////////////////
///// 1. Homepage ////////////
//////////////////////////////

var homepage = {
	main: function() {

	}
};

//////////////////////////////
///// 2. Keyword Search //////
//////////////////////////////

var keywordSearch = {

	// navigates to search url when clicking on search button
	submitSearch: function() {
		// event listener
		$('#search-button').click(function(evt) {

			// get object type
			objectType = $('input[type="radio"][name="radio"]:checked').attr('id');

			// get keywords
			var keywords = [];
			$('.tags-input').find('span').each(function(i, elem) {
				keywords.push($(elem).text());
			});

			// navigate
			if (keywords.length > 0) {
				window.location = 'search?object_type=' + objectType + '&keywords=' + keywords.join(', ')
			}
		})
	},

	// sets example when clicking on objects
	setExample: function() {

		$('input[type="radio"]').click(function(evt) {

			// get object type
			objectType = $(evt.target).attr('id');

			// change example
			if (objectType === 'analysis') {
				$('#search-example').html('Examples: <a class="search-example-link" href="#">enrichment, prostate cancer, upregulated</a>; or <a class="search-example-link" href="#">small molecule, reverse, myocardial infarction</a>.')
			} else if (objectType === 'dataset') {
				$('#search-example').html('Examples: <a class="search-example-link" href="#">breast cancer, estrogen positive</a>; or <a class="search-example-link" href="#">GSE10325</a>.')
			} else if (objectType === 'tool') {
				$('#search-example').html('Examples: <a class="search-example-link" href="#">enrichment</a>; or <a class="search-example-link" href="#">L1000</a>; or <a class="search-example-link" href="#">image data</a>.')
			}
		})

	},

	// searches example
	searchExample: function() {

		$(document).on('click', '.search-example-link', function(evt) {
			// get tags input
			var $tagsInput = $('.tags-input');

			// remove existing tags
			$tagsInput.find('.tag').remove();

			// add tags
			$.each($(evt.target).text().split(', ').reverse(), function(index, value) {
				$tagsInput.prepend('<span class="tag" data-tag="'+value+'">'+value+'</span>')
			})

			// search
			$('#search-button').click()
		})

	},

	// go back
	goBack: function() {

		$('#back-button').click(function(evt) {
			// scroll to
			setTimeout(function() {
				$('html, body').animate({
				        scrollTop: $("html").offset().top
				    }, 750);	
			}, 100)

			// hide results
			setTimeout(function(){
				$('#search-results-wrapper').css('display', 'none');
			}, 950)
		})

	},

	// checks if page has query and fixes accordingly
	pageSetup: function() {

		if ((window.location.href.indexOf('object_type=') !== -1) && (window.location.href.indexOf('keywords=') !== -1)) {

			// get tags and object type
			var tags = decodeURIComponent(window.location.href.split('keywords=')[1]).split(', '),
				objectType = window.location.href.split('object_type=')[1].split('&')[0];

			// click button
			$('#'+objectType).click();

			// add tags
			$.each(tags.reverse(), function(index, value) {
				$('.tags-input').prepend('<span class="tag" data-tag="'+value+'">'+value+'</span>');
			})

			// scroll to
			setTimeout(function() {
				$('html, body').animate({
				        scrollTop: $("#search-results-wrapper").offset().top
				    }, 750);	
			}, 500)

		} else {

			// click analysis
			$('#analysis').click();
			$('#search-results-wrapper').css('display', 'none');
		}

	},

	// main 
	main: function() {
		if (window.location.pathname === entry_point+'/search') {
			var self = this;
			self.submitSearch();
			self.setExample();
			self.searchExample();
			self.goBack();
			self.pageSetup();
		}
	}
};

var developmentSearch = {

	// navigates to search url when clicking on search button
	submitSearch: function() {
		// event listener
		$('#submit-search-button').click(function(evt) {

			// get object type
			objectType = 'analysis'

			// get keywords
			var keywords = [];
			$('.tags-input').find('span').each(function(i, elem) {
				keywords.push($(elem).text());
			});

			// navigate
			if (keywords.length > 0) {
				window.location = 'search_dev?object_type=' + objectType + '&keywords=' + keywords.join(', ')
			}
		})
	},

	// main 
	main: function() {
		if (window.location.pathname === entry_point+'/search_dev') {
			var self = this;
			self.submitSearch();
		}
	}
};

//////////////////////////////
///// 3. Advanced Search /////
//////////////////////////////

var advancedSearch = {

	// change selections
	changeSelections: function(object_type) {
		$('.selectpicker-term.selectpicker-'+object_type).removeClass('hidden');
		$('.selectpicker-term:not(.selectpicker-'+object_type+')').addClass('hidden');
	},

	// manage selections
	changeSelectionListener: function() {
		var self = this,
			$objectSelector = $('#objectType');

		$(document).on('change', '#objectType', function(evt) {
			self.changeSelections($objectSelector.val());
		})

		self.changeSelections($objectSelector.val());
	},

	// add row listener
	addRow: function() {
		$(document).on('click', '.add-search-term-button', function(evt) {

			var $evtTarget = $(evt.target), // get button
				$rowToAdd = $('.filter-row:not(.active)').first(); // get row to add

			// show following row
			$rowToAdd.addClass('active');
		})
	},

	// remove row listener
	removeRow: function() {
		$(document).on('click', '.remove-search-term-button', function(evt) {

			var $evtTarget = $(evt.target), // get button
				$currentRow = $evtTarget.parents('.row'); // get current row

			// hide current row
			$currentRow.removeClass('active');

			// reset selections
			$currentRow.find('.selectpicker-term select').val('').selectpicker('refresh');
			$currentRow.find('#value').val('');
			$currentRow.find('#comparisonType').val('CONTAINS');
			$currentRow.find('#operatorType').val('AND');
		})
	},

	// build query
	buildQuery: function() {
		$(document).on('change', '#advanced-search-form', function(evt) {

			// get active rows
			var $activeRows = $('.filter-row.active'),
				$queryBox = $('#advanced-search-query'),
				query = '',
				$activeRow, separatorType, termName, comparisonType, value;

			// build query
			$activeRows.each(function(i, elem) {
				$activeRow = $(elem);
				separatorType = $activeRow.find('#separatorType').length === 0 ? '' : $activeRow.find('#separatorType').val(); // get operator type, set '' if not specified
				termName = $activeRow.find('.selectpicker-term:not(.hidden) option:selected').attr('value'); // get term name
				comparisonType = $activeRow.find('#comparisonType').val(); // get comparison type
				value = '"'+$activeRow.find('#value').val()+'"'; // get value

				query = '(' + query + [separatorType, termName, comparisonType, value].join(' ') + ') ' // build query
			})

			// add
			$queryBox.html(query.replace('( ', '('));
		})
	},

	// submit search
	submitSearch: function() {
		$(document).on('click', '#advanced-search-submit-button', function(evt) {
			var objectType = $('#objectType').val(), // get object type
				query = $('#advanced-search-query').text().trim(); // get search query

			window.location = 'advanced_search?object_type=' + objectType + '&query=' + query // submit search
		})
	},

	// main
	main: function() {
		if (window.location.pathname === entry_point+'/advanced_search') {
			var self = this;
			self.changeSelectionListener();
			self.addRow();
			self.removeRow();
			self.buildQuery();
			self.submitSearch();
		}
	}
};

//////////////////////////////
///// 4. Upload //////////////
//////////////////////////////

var uploadForm = {

	// change input method
	changeInputMethod: function() {

		$('.change-method label').click(function(evt) {
			var $evtTarget = $(evt.target), // get event target
				method = $evtTarget.hasClass('fa') ? $evtTarget.parent().attr('class').split(' ')[2] : $evtTarget.attr('class').split(' ')[2]; // get method

			$evtTarget.parents('.col-lg-4').find('.add-object-row.'+method).removeClass('hidden');
			$evtTarget.parents('.col-lg-4').find('.add-object-row:not(.'+method+')').addClass('hidden');
		})
	},

	// add object preview
	addObjectPreview: function(objectData, objectType) {
		var $addedObjectRow = $('#added-'+objectType+'-row'),
			$addedObjectCol = $('#added-'+objectType+'-col'),
			objectSummary, objectPreviewHtml;
		$addedObjectRow.removeClass('hidden');
		if (objectType === 'dataset') {
			var datasetIdentifier;

			if (typeof objectData === 'string') {
				datasetIdentifier = objectData;
				objectSummary = JSON.parse($.ajax({ // get annotation from id
					async: false,
					url: window.location.origin+entry_point+'/api/dataset',
					data: {
					  'dataset_accession':objectData,
					},
					success: function(data) {
						return data;
					}
				}).responseText)['results'][0];
			} else if (typeof objectData === 'object') {
				datasetIdentifier = objectData['dataset_accession'];
				objectSummary = objectData;
			}

			objectPreviewHtml =`
	 		<div class="row added-object added-dataset" id="`+datasetIdentifier+`">
				<div class="col col-10 text-left">
				 <div class="added-dataset-accession"><a href="`+objectSummary['dataset_landing_url']+`">`+objectSummary['dataset_accession']+`</a></div>
				 <div class="added-dataset-title">`+objectSummary['dataset_title']+`&nbsp<sup><i class="fa fa-info-circle fa-1x" aria-hidden="true" data-toggle="tooltip" data-placement="right" data-html="true" title="`+objectSummary['dataset_description']+`"></i></sup></div>
				</div>
				<div class="col col-2 text-right">
					<a class="remove-added-dataset" href="#">Remove</a>
				</div>
			</div>
			`.replace('\n', '');;

			$addedObjectCol.append(objectPreviewHtml);
			$('[data-toggle="tooltip"]').tooltip();

		} else if (objectType === 'tool') {

			if (typeof objectData === 'string') {
				objectSummary = JSON.parse($.ajax({ // get annotation from id
					async: false,
					url: window.location.origin+entry_point+'/api/tool',
					data: {
					  'tool_name':objectData,
					},
					success: function(data) {
						return data;
					}
				}).responseText)['results'][0];
			} else if (typeof objectData === 'object') {
				objectSummary = objectData;
			}

			objectPreviewHtml =`
	 		<div class="row added-object added-tool">
				<div class="col col-12 text-left">
				<div>
	 				<img class="added-tool-icon" src="`+objectSummary['tool_icon_url']+`">
					 <a class="added-tool-name" href="`+objectSummary['tool_homepage_url']+`">`+objectSummary['tool_name']+`</a>
				</div>
				<div class="added-tool-description">`+objectSummary['tool_description']+`</div>
				</div>
			</div>
			`.replace('\n', '');

			$addedObjectCol.html(objectPreviewHtml);
			$('[data-toggle="tooltip"]').tooltip()
		}
	},

	// add object
	addObject: function(analysisObject) {
		var self = this;
		$('.add-object-button-row button').click(function(evt) {
			var $activeAddRow = $(evt.target).parents('.add-object-button-row').parent().find('.add-object-row:not(.hidden)'), // get active row
				objectType = $activeAddRow.attr('id').split('-')[1], objectData;
			if (objectType === 'dataset') {

				if ($activeAddRow.hasClass('select-method')) {
					objectData = $activeAddRow.find('option:selected').attr('value');
				} else if ($activeAddRow.hasClass('insert-method')) {
					objectData = {};
					$activeAddRow.find('input:not([role="textbox"])').each(function(i, elem) {
						objectData[$(elem).attr('id')] = $(elem).val();
					})
					objectData['repository_fk'] = $activeAddRow.find('option:selected').attr('value');
				}

				if (analysisObject[objectType].indexOf(objectData) === -1 && objectData != "" && Object.values(objectData).indexOf('') === -1 && analysisObject['dataset'].map(function(x) {return x['dataset_accession']}).indexOf(objectData['dataset_accession']) < 1) {
					analysisObject[objectType].push(objectData);
					self.addObjectPreview(objectData, objectType);
				}

			} else if (objectType === 'tool') {

				if ($activeAddRow.hasClass('select-method')) {
					objectData = $activeAddRow.find('option:selected').attr('value');
				} else if ($activeAddRow.hasClass('insert-method')) {
					objectData = {};
					$activeAddRow.find('input:not([role="textbox"])').each(function(i, elem) {
						objectData[$(elem).attr('id')] = $(elem).val();
					})
				}

				if (objectData != "" && Object.values(objectData).indexOf('') === -1) {
					analysisObject[objectType] = objectData;
					self.addObjectPreview(objectData, objectType);
				}

			}
		})

		return analysisObject;
	},

	// remove dataset
	removeDataset: function(analysisObject) {
		$(document).on('click', '.remove-added-dataset', function(evt) {
			var $addedDatasetCol = $('#added-dataset-col'),
				removedDatasetIdentifier = $(evt.target).parent().parent().attr('id');
			analysisObject['dataset'] = analysisObject['dataset'].filter(function(x){ return(typeof x === 'object' ? x['dataset_accession'] != removedDatasetIdentifier : x != removedDatasetIdentifier) });
			if ($addedDatasetCol.find('.added-dataset').length === 1) {
				$addedDatasetCol.parent().addClass('hidden');
			}
			removedDatasetIdentifier = $(evt.target).parent().parent().remove();
		})

		return analysisObject;
	},

	// preview analysis
	previewAnalysis: function(analysisObject) {

		$('#preview-analysis-button-row button').click(function(evt) {
			analysisObject['analysis'] = {'metadata': {}};

			$('#input-analysis-row').find('input').each(function(i, elem) {
				analysisObject['analysis'][$(elem).attr('id')] = $(elem).val();
			})

			if ($('.tags-input').find('.tag').length > 0) {
				analysisObject['analysis']['metadata']['keywords'] = [];
				$('.tags-input').find('.tag').each(function(i, elem){ analysisObject['analysis']['metadata']['keywords'].push($(elem).attr('data-tag')); });
			}

			$('#metadata-row-wrapper').find('.row').each(function(i, elem){ analysisObject['analysis']['metadata'][$(elem).find('.metadata-term').val()] = $(elem).find('.metadata-value').val() });

			if (analysisObject['dataset'] != [] && analysisObject['tool'] != '' && Object.values(analysisObject['analysis']).indexOf('') === -1) {
				$.ajax({ // get preview html from api
					url: window.location.origin+entry_point+'/api/get_analysis_preview',
					data: {
					  'data': JSON.stringify(analysisObject),
					},
					success: function(data) {
						$('#preview-analysis-row').find('.col-12').html(data);
						$('#add-analysis-wrapper').addClass('hidden');
						$('#preview-analysis-wrapper').removeClass('hidden');
						$('#preview-analysis-row').removeClass('hidden');
						$('[data-toggle="tooltip"]').tooltip();
					}
				})
			}

		})

		return analysisObject;
	},

	// review analysis
	reviewAnalysis: function() {
		$('#review-analysis-button').click(function(evt) {
			$('#add-analysis-wrapper').removeClass('hidden');
			$('#preview-analysis-wrapper').addClass('hidden');
		})
		$('#review-error-analysis-button').click(function(evt) {
			$('#add-analysis-wrapper').removeClass('hidden');
			$('#preview-analysis-wrapper').addClass('hidden');
			$('#upload-error').addClass('hidden');
		})
	},

	// submit analysis
	submitAnalysis: function(analysisObject) {
		$('#submit-analysis-button').click(function(evt) {
			var $previewWrapper = $('#preview-analysis-wrapper'),
				$previewRow = $('#preview-analysis-row'),
				$success = $('#upload-success'),
				$error = $('#upload-error');
			$.ajax({
				url: window.location.origin+entry_point+'/api/manual_upload',
				data: {
				  'data': JSON.stringify(analysisObject),
				},
				success: function(data) {
					$previewWrapper.addClass('hidden');
					$previewRow.addClass('hidden');
					$success.removeClass('hidden');
					$error.addClass('hidden');
				},
				error: function(err) {
					$previewWrapper.addClass('hidden');
					$success.addClass('hidden');
					$error.removeClass('hidden');
				}
			})
		}) 
	},

	// submit analysis
	alterMetadata: function(analysisObject) {
		$(document).on('click', '#add-metadata-term', function(evt) {
			$('#metadata-row-wrapper').find('.row.hidden').first().removeClass('hidden');
		})
		$(document).on('click', '.remove-metadata-term', function(evt) {
			var $parentRow = $(evt.target).parents('.form-group.row');
			$parentRow.addClass('hidden');
			$parentRow.find('input').val('');
		}) 
	},

	// main
	main: function() {
		if (window.location.pathname === entry_point+'/upload') {
			var self = this,
				analysisObject = {'dataset': [], 'tool': '', 'analysis': {}};
			self.changeInputMethod();
			self.alterMetadata();
			analysisObject = self.addObject(analysisObject);
			analysisObject = self.removeDataset(analysisObject);
			analysisObject = self.previewAnalysis(analysisObject);
			self.reviewAnalysis();
			self.submitAnalysis(analysisObject);
		}
	}
};

//////////////////////////////
///// 5. Explorer ////////////
//////////////////////////////

var metadataExplorer = {

	// d3 circle packing
	circlePacking: function(root) {

		var self = this;

			if (root['children'].length > 0) {

				$('.metadata-explorer-results').hide();
				$('.metadata-explorer-visualize').show();

				$('svg').html('');

				var svg = d3.select("svg"),
				    margin = 20,
				    diameter = +svg.attr("width"),
				    g = svg.append("g").attr("transform", "translate(" + diameter / 2 + "," + diameter / 2 + ")");

				var color = d3.scaleLinear()
				    .domain([-1, 5])
				    .range(["#eceeef", "#3366cc"])
				    .interpolate(d3.interpolateHcl);

				var pack = d3.pack()
				    .size([diameter - margin, diameter - margin])
				    .padding(2);

				  root = d3.hierarchy(root)
				      .sum(function(d) { return d.size; })
				      .sort(function(a, b) { return b.value - a.value; });

				  var focus = root,
				      nodes = pack(root).descendants(),
				      view;

				  var circle = g.selectAll("circle")
				    .data(nodes)
				    .enter().append("circle")
				      .attr("class", function(d) { return d.parent ? d.children ? "node" : "node node--leaf" : "node node--root"; })
				      .style("fill", function(d) { return d.children ? color(d.depth) : null; })
				      .on("click", function(d) { if (focus !== d) zoom(d), d3.event.stopPropagation(); });

				  var text = g.selectAll("text")
				    .data(nodes)
				    .enter().append("text")
				      .attr("class", "label")
				      .style("fill-opacity", function(d) { return d.parent === root ? 1 : 0; })
				      .style("display", function(d) { return d.parent === root ? "inline" : "none"; })
				      .style("font-size", function(d) {return d.data.relsize > 0 ? 9+5*d.data.relsize : "13pt"; })
				      // .style("font-size", function(d) {return d.data.size > 0 ? Math.min(Math.sqrt(d.data.size)+3, 25) : "13pt"; })
				      .text(function(d) { return d.data.name; });

				  var node = g.selectAll("circle,text");

				  svg
				      .style("background", color(-1))
				      .on("click", function() { zoom(root); });

				  zoomTo([root.x, root.y, root.r * 2 + margin]);

				  function zoom(d) {
				    var focus0 = focus; focus = d;

				    var transition = d3.transition()
				        .duration(d3.event.altKey ? 7500 : 750)
				        .tween("zoom", function(d) {
				          var i = d3.interpolateZoom(view, [focus.x, focus.y, focus.r * 2 + margin]);
				          return function(t) { zoomTo(i(t)); };
				        });

				    transition.selectAll("text")
				      .filter(function(d) { return d.parent === focus || this.style.display === "inline"; })
				        .style("fill-opacity", function(d) { return d.parent === focus ? 1 : 0; })
				        .on("start", function(d) { if (d.parent === focus) this.style.display = "inline"; })
				        .on("end", function(d) { if (d.parent !== focus) this.style.display = "none"; });
				  }

				  function zoomTo(v) {
				    var k = diameter / v[2]; view = v;
				    node.attr("transform", function(d) { return "translate(" + (d.x - v[0]) * k + "," + (d.y - v[1]) * k + ")"; });
				    circle.attr("r", function(d) { return d.r * k; });
				  }

			} else {
				$('.metadata-explorer-results').show();
				$('.metadata-explorer-visualize').hide();
				self.addResults();
			}
	},

	// add select
	selectOptions: function(selectOptionsObj, queryObj={}) {
		var self = this;
		$('#term-row-wrapper').html('');
		$.each(selectOptionsObj, function(termName, termValueObj) {
			$('#term-row-wrapper').append('<div class="row term-row" data-term-name="'+termName.replace(' ', '_').replace(' ', '_').replace(' ', '_').toLowerCase()+'"><div class="col-4 term-name-col">'+termName+'</div><div class="col-8 text-left"><input type="text" placeholder="Select..."></div></div>');
			var options = [];
			$.each(termValueObj, function(termValue, count) { options.push({'id': termValue, 'title': termValue+' ('+count+')'}) });
			var $select = $('#term-row-wrapper input').last().selectize({
			    maxItems: null,
			    valueField: 'id',
			    labelField: 'title',
			    searchField: 'title',
			    options: options,
			    create: false
			});
			var control = $select[0].selectize;
			$(document).off('change', '#explorer-selection-col');
			control.setValue(queryObj[termName.replace(' ', '_').replace(' ', '_').replace(' ', '_').toLowerCase()]);
			self.selectListener();
		})
	},

	// refresh interface
	refreshInterface: function(queryObj={}) {
		var isVisualizeMode = $('.metadata-explorer-visualize').first().is(':visible'),
			self = this;
		if (isVisualizeMode) {
			self.newVisualization(queryObj, true);
		} else {
			self.newVisualization(queryObj);
			self.addResults();
		}
	},

	// get query obj
	getQueryObj: function() {
		var queryObj = {};
		$('#explorer-selection-col .term-row').each(function(i, elem){
			var termName = $(elem).attr('data-term-name'),
				values = [];
			$(elem).find('.item').each(function(i, e){values.push($(e).attr('data-value'))});
			if (values != '') {
				queryObj[termName] = values;
			}
		});
		return queryObj;
	},

	// get new visualization
	newVisualization: function(queryObj, updateD3=false) {
		var self = this;
			$.ajax({
				async: true,
				url: window.location.origin+entry_point+'/api/metadata_explorer',
				data: {
				  'query': JSON.stringify(queryObj)
				},
				success: function(data) {
					metadataExplorerObj = JSON.parse(data);
					if (updateD3){
						self.circlePacking(metadataExplorerObj['d3']);
					}
					self.selectOptions(metadataExplorerObj['select'], queryObj);
				}
			});
	},

	// get results
	addResults: function() {
		var self = this,
			$explorerResults = $('#explorer-results'),
			queryObj = self.getQueryObj();
		$explorerResults.html('');
		$('.metadata-explorer-results').show();
		$('.metadata-explorer-visualize').hide();
		$.ajax({
			async: true,
			url: window.location.origin+entry_point+'/api/metadata_explorer',
			data: {
			  'query': JSON.stringify(queryObj),
			  'query_type': 'results'
			},
			success: function(data) {
				// metadataExplorerObj = JSON.parse(data);
				$explorerResults.html(data);
				$(function() {$('[data-toggle="tooltip"]').tooltip()}) 
			}
		});
	},

	// select listener
	selectListener: function() {
		var self = this;
		$(document).on('change', '#explorer-selection-col', function(evt) {
			var queryObj = self.getQueryObj();
			self.refreshInterface(queryObj);
		})
	},

	// get results
	resultsListener: function() {
		var self = this;
		$(document).on('click', '#change-explorer-view .metadata-explorer-visualize', function(evt) {
			self.addResults();
		})
		$(document).on('click', '#change-explorer-view .metadata-explorer-results', function(evt) {
			self.addResults();
			$('.metadata-explorer-results').hide();
			$('.metadata-explorer-visualize').show();
						var queryObj = self.getQueryObj();
			self.refreshInterface(queryObj);
		})
	},

	// main
	main: function() {
		if (window.location.pathname === entry_point+'/metadata') {
			var self = this;
			self.refreshInterface();
			self.selectListener();
			self.resultsListener();
		}
	}
};

//////////////////////////////
///// 6. Help ////////////////
//////////////////////////////

var help = {

	// open accordion
	openAccordion: function() {
		try {
			var openLink = window.location.hash,
				openSection = String(openLink.match(/[a-zA-Z]+/g));
			if (['', 'general'].indexOf(openSection) == -1) {
				$("a[href='#help-"+openSection+"']").click();
				$(openLink).get(0).scrollIntoView();
			}	
		} catch(err) {
		}
	},

	// main
	main: function() {
		if (window.location.pathname === entry_point+'/help') {
			var self = this;
			self.openAccordion();
		}
	}
};

//////////////////////////////
///// 7. Help ////////////////
//////////////////////////////

var analyze = {

	// add tool
	addTool: function() {
		$('#add-tool-icon').on('click', function(evt) {
			// Show tool row
			$('.added-tool-row.hidden').first().removeClass('hidden');
		})

	},

	// remove tool
	removeTool: function() {
		$('.remove-tool').on('click', function(evt) {
			// Get parent row
			$parentRow = $(evt.target).parents('.added-tool-row');

			// Hide row
			$parentRow.addClass('hidden');

			// Hide text
			$parentRow.find('.selected-tool-description').addClass('hidden');
			$parentRow.find('.tool-details').addClass('hidden');
			$parentRow.find('.tool-options').addClass('hidden');

			// Reset selection
			$parentRow.find('select').prop('selectedIndex', 0);

			// Remove data
			$selectedToolIcon = $parentRow.find('.selected-tool-icon');
			$selectedToolIcon.css('background-image', 'url("")');
			$selectedToolIcon.find('.fa').css('visibility', 'visible');
		})

	},

	// select dataset
	selectDataset: function() {
		$('#select-dataset-to-analyze').on('change', function(evt) {
			// Get selected dataset ID
			var datasetId = $(evt.target).val();

			// AJAX request
			$.ajax({
				async: true,
				url: window.location.origin+entry_point+'/api/dataset',
				data: {
					'd.id': datasetId
				},
				success: function(data) {
					
					// Get dataset data
					datasetObj = JSON.parse(data)['results'][0];

					// Add text
					$('#selected-dataset-title').html(datasetObj['dataset_title']);

					// Show text
					$('#selected-dataset-text').css('visibility', 'visible');

					// Show tools
					$('#first-tool-row').css('visibility', 'visible');
				}
			})
		})
	},

	// select tool
	selectTool: function() {
		$('.select-tool').on('change', function(evt) {

			// Get selected tool ID
			var toolId = $(evt.target).val(),
				$parentRow = $(evt.target).parents('.added-tool-row');

			// AJAX request
			$.ajax({
				async: true,
				url: window.location.origin+entry_point+'/api/script',
				data: {
					'id': toolId
				},
				success: function(data) {
					
					// Get tool data
					toolObj = JSON.parse(data)['results'][0];

					// Add data
					$parentRow.find('.selected-tool-description').html(toolObj['script_description']);

					// Show
					// $parentRow.find('.selected-tool-title').html(toolObj['tool_name']);
					$parentRow.find('.selected-tool-description').removeClass('hidden');
					$parentRow.find('.tool-details').removeClass('hidden');
					$parentRow.find('.tool-options').removeClass('hidden');

					// Add icon
					$selectedToolIcon = $parentRow.find('.selected-tool-icon');
					$selectedToolIcon.css('background-image', 'url("'+toolObj['script_icon_url']+'")');
					$selectedToolIcon.find('.fa').css('visibility', 'hidden');

				}
			})
		})
	},

	// generate json
	generateAnalysisJson: function() {

	},

	// analyze
	submitAnalysis: function() {
		$('#submit-analysis-icon').on('click', function(evt) {
			
			// Define object
			var analysisObject = {
				'dataset': {},
				'tools': []
			};

			// Add dataset
			analysisObject['dataset'] = {
				'dataset_accession': $('#select-dataset-to-analyze').val(),
				'options': {},
				'signatures': {}
			}

			// Add tools
			$('.added-tool-row:not(.hidden)').each(function(i, elem) {

				// Add script info
				analysisObject['tools'].push({
					'script_name': $(elem).find('option:selected').text().trim().toLowerCase(),
					'parameters': {},
					'plots': {}
				});

			// Print
			console.log(JSON.stringify(analysisObject));

			})

		})
	},

	// generate notebook
	generateNotebook: function() {
		// Check if query
		if (window.location.href.indexOf('?q=') > -1) {

			// Perform ajax call
			$.ajax({
				async: true,
				url: window.location.href.replace('/analyze', '/api/analyze'),
				success: function(data) {
					$('body').html(data);
				}
			})
		}
	},

	// main
	main: function() {
		if (window.location.pathname === entry_point+'/analyze') {
			var self = this;
			self.selectDataset();
			self.submitAnalysis();
			self.generateNotebook();
			self.addTool();
			self.removeTool();
			self.selectTool();
		}
	}
};



///////////////////////////////////
////////// 3. Call ////////////////
///////////////////////////////////

main();