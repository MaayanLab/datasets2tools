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

}

main();