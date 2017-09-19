$('.fairness-insignia').each(function(i, elem) {
    $.ajax({
        url: "{{ url_for('fairness_insignia_api') }}",
        data: {
            object_type: $(elem).attr('data-object-type'),
            object_identifier: $(elem).attr('data-identifier')
        },
        success: function(data) {
            fairness_data = JSON.parse(data);
            if (fairness_data['fairness_score']) {
                color = d3.scaleLinear().domain([0, 9]).interpolate(d3.interpolateRgb).range([d3.rgb(255,0,0), d3.rgb(0,0,255)]);
                $(elem).html(
                    $("<div>").css('border-radius', '3px')
                        .css('font-size', '9pt')
                        .css('color', 'white')
                        .css('margin-top', 'auto')
                        .css('margin-bottom', 'auto')
                        .css('cursor', 'pointer')
                        .css('padding', '2px 5px')
                        .css('padding', '2px 5px')
                        .attr('data-toggle', 'tooltip')
                        .attr('data-placement', 'right')
                        .attr('data-animation', 'false')
                        .attr('data-html', 'true')
                        .attr('data-original-title', 'FAIRness')
                        .css('background-color', color(fairness_data['fairness_score']))
                        .html(fairness_data['fairness_score'])
                        .prepend($("<i>", {class: 'fa fa-certificate'}).css('margin-right', '5px'))
                    );
            } else {
            }
        }
    });
});