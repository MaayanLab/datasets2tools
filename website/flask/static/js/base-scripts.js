function main() {
	$('#signup-question a').click(function(evt) {
		$('#login-modal').modal('hide');
	});

	if (window.location.href.indexOf('?login=true') > -1) {
		$('#login-modal').modal('show');
	}

	if (window.location.href.indexOf('?signup=true') > -1) {
		$('#signup-modal').modal('show');
	}

	$(document).ready(function(){
		$('[data-toggle="tooltip"]').tooltip(); 
	});

	$(function () {
		  $('[data-toggle="popover"]').popover({
			html : true,
			trigger : 'hover'
		}).on('hide.bs.popover', function () {
			if ($(".popover:hover").length) {
			  return false;
			}
		}); 

		$('body').on('mouseleave', '.popover', function(){
			$('.popover').popover('hide');
		});
	});
}

main();