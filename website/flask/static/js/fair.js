$('.fairness-insignia').each(function(i, elem) {
    $.ajax({
        url: "http://localhost:5000/datasets2tools/api/fairness_insignia",
        data: {
            object_type: $(elem).attr('data-object-type'),
            object_identifier: $(elem).attr('data-identifier')
        },
        success: function(data) {
            fairness_data = JSON.parse(data);
            if (fairness_data['fairness_score']) {
                // Get badge color
                badgeColor = d3.scaleLinear().domain([0, 9]).interpolate(d3.interpolateRgb).range([d3.rgb(255,0,0), d3.rgb(0,0,255)]);
                
                // Prepare badge
                $badge = $("<div>", {'class': 'fairness-insignia'})
                            .css('cursor', 'pointer')
                            .attr('data-toggle', 'popover')
                            .attr('data-placement', 'right')
                            .attr('data-animation', 'false')
                            .attr('data-html', 'true')
                            .attr('data-trigger', 'hover')
                            .attr('data-template', '<div class="popover" role="tooltip" style="max-width:1000px;"><div class="popover-arrow"></div><h3 class="popover-title" style="font-size: 9pt;"></h3><div class="popover-content"></div></div>')
                            .attr('data-title', 'FAIR Evaluation Summary<span style="font-size:8pt;color:#c2c2c2;padding-left:10px;font-weight:300;width:100%;">'+fairness_data['evaluations']+' evaluations</span>')
                            .append($("<i>", {class: 'fa fa-certificate'})
                                        .css('color', badgeColor(fairness_data['fairness_score']))
                                        .css('font-size', '20pt'))
                            .append($("<span>")
                                        .html(fairness_data['fairness_score'])
                                        .css('position', 'absolute')
                                        .css('font-size', '10pt')
                                        .css('font-weight', '300')
                                        .css('top', '4px')
                                        .css('left', '7px')
                                        .css('color', 'white'));

                // Add popover
                questionColor = d3.scaleLinear().domain([0, 1]).interpolate(d3.interpolateRgb).range([d3.rgb(255,0,0), d3.rgb(0,0,255)]);
                $popoverContent = $('<div>').append($('<div>').html(fairness_data['fairness_score']+' out of 9 questions were answered positively by the majority of evaluators.').css('font-size', '9pt').css('margin-bottom', '5px')).append($('<ol>').css('font-weight', '500').css('padding-left', '10px').css('margin-bottom', '0px').css('font-size', '9pt'));
                $.each(fairness_data['questions'], function(index, question){ $($popoverContent).find('ol').append($('<li>').append($('<span>').css('font-weight', '300').html(question['question'])).append($('<span>').css('padding-left', '5px').css('color', questionColor(question['average_score'])).html('('+Math.round(question['average_score']*100)+'% yes)'))) });
                $badge.attr('data-content', $popoverContent.html());

                // Replace
                $(elem).replaceWith($badge);

                // Popover animation
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

            } else {
            }
        }
    });
});