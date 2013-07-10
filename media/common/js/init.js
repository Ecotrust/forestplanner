// name space for app

app.properties = {
    viewModel: new propertiesViewModel()
};
var authenticated = authenticated || false;


$(document).ready(function () {

    ko.applyBindings(app.properties.viewModel, document.getElementById('property-html'));
	// might be terribly inefficient to bind app to the tabs but we need many viewModels to update their state
	// beyond basic tabs (eg. when scenarios require xyz and we want to alert the user via the tabs...)
    ko.applyBindings(app, document.getElementById('global-tabs'));

    $(window).resize(app.onResize);
    app.onResize();

    map.zoomToExtent(OpenLayers.Bounds.fromArray([-13954802.50397, 5681411.4375898, -13527672.389972, 5939462.8450446]));
	app.globalErrorHandling();

	app.standUploadFormInit();

	app.chartInit();

	app.deferredClickHandler();

	app.router();

	app.moreHelp();

	window.onhashchange = app.hashChange;
	
	// temp hack. django switch in template is always adding this.
	//
	if (authenticated) {
		$('body').removeClass('no-auth');
	}

});

app.router = function () {
	var viewList = ['#properties', '#stands', '#scenarios'],
		loc = window.location.hash.split("/");

	//set in map_ext
	if (authenticated) {
		//TODO should probably account for about and help
		if ( $.inArray(loc[0], viewList) < 0) {
			window.location.hash = "#properties";
			//app.log('Rerouting to #properties');
		} else {
			app.hashChange();
		}

	}

};
app.deferredClickHandler = function () {
	//let's bubble.
	$('body').on('click', function (event, a) {
		var $t = $(event.target);

		if ($t.is('.more-toggle')) {
			$t.next('.more').toggle();
			event.preventDefault();
			return false; 
		}

	});
};

//needed by global tabs. Need to bind on page load but they don't exist yet. Cheap defer.
app.selectedPropertyName = ko.observable("");
app.selectedPropertyUID = ko.observable("");

app.moreHelp = function () {

	$('.info-help').find('strong')
		.next('span').hide()
		.after('<span class="read-more"> Read More...</span>');

	$('body').on('click', function (e) {
		var $target = $(e.target);
		if ($target.is('.read-more')) {
			$target.prev('span').toggle();
			$target.closest('.info-help').toggleClass('opened');
			if ($target.prev('span').is(':visible')) {
				$target.text(' Read Less');
			} else {
				$target.text(' Read More...');
			}
			e.stopImmediatePropagation();
		}
	});
};

app.onResize = function () {
    var height = $(window).height(),
		width = $(window).width(),
		divWidth;

    //$("#map").height(height - 137);
    $("#map").height(height - 163);
    map.render('map');

    divWidth = width * (7 / 12); // span7
    if (divWidth > height) {
        // "widescreen" so go side-by-side
        $(".timemap-container").width('48%');
        $(".timemap").height(height - 314);
    } else {
        // "narrow" so go top-to-bottom
        $(".timemap-container").width('99%');
        $(".timemap").height((height - 324) / 2.0);
    }
    if (scenarioPlot) {
        refreshCharts();
    }
};

app.chartInit = function () {
	// initialize chart and timemap metrics dropdowns
	// more in chart.js
    var chart_sel = $('#chart-metrics-select'),
		timemap_sel = $('#timemap-metrics-select'),
		metric;

    for (var prop in chartMetrics) {
        metric = chartMetrics[prop];
        chart_sel.append($('<option value="' + metric.variableName + '">' + metric.title + '</option>'));
        timemap_sel.append($('<option value="' + metric.variableName + '">' + metric.title + '</option>'));
    }
    chart_sel.change(refreshCharts);
    timemap_sel.change( function () { refreshTimeMap(true, true); });

    $('.selectpicker').selectpicker();

    $('#scenario-charts-tab').on('shown', refreshCharts); 
};

app.standUploadFormInit = function () {
	
	var options = {
		beforeSubmit: function (formData, jqForm, options) {
			var name, file;
			$(formData).each(function () {
				if (this.name === 'new_property_name') {
					name = this.value;
				} else if (this.name === 'ogrfile') {
					file = this.value;
				}
			});
			if (!name) {
				$("#upload-propertyname-required").fadeIn();
				return false;
			}
			if (!file) {
				$("#upload-file-required").fadeIn();
				return false;
			}

			$("#uploadProgress").show();
		},
		uploadProgress: function (event, position, total, percentComplete) {
			var percentVal = percentComplete + '%';
			$("#uploadProgress .bar").css('width', percentVal);
			if (percentComplete > 99) {
				$("#uploadProgress").hide();
				$("#uploadResponse").html('<p class="label label-info">Upload complete. Processing stand data...</p>');
			}
		},
		complete: function (xhr) {
			$("#uploadProgress").hide();
			$("#uploadProgress .bar").css('width', '0%');
		},
		error: function (data, status, xhr) {
			$("#uploadResponse").html(data.responseText);
		},
		success: function (data, status, xhr) {
			if (xhr.status === 201) {
				$("#uploadResponse").fadeOut();
				$("#uploadResponse").html('<p class="label label-success">Success</p>');
				$("#uploadResponse").fadeIn();
				$('#uploadForm').clearForm();
				var interval = setTimeout( function() {
					$("#uploadResponse").html('');
					app.properties.viewModel.afterUploadSuccess(data);
				}, 2000);
			}
		}

	}; 
    $('#uploadForm').submit(function () {
        $(this).ajaxSubmit(options); 
        return false; 
    });
};

app.globalErrorHandling = function () {
	$('body').prepend('<div id="flash" class="alert fade in" style="display: none"><h4></h4><div></div><a class="close" href="#">&times;</a>');
	app.$flash = $('#flash');

	$( document ).ajaxError(function (event, request, settings, exception) {
		app.flash(request.responseText);
        // TODO parse out human-readable text from html error responses?
	});

	app.$flash.find('.close').bind('click', app.flash.dismiss);
};

//@TODO should pass an object. it's 2013. -wm
app.flash = function (message, header, flashType) {
	// bs: alert-error, alert-warning, 
	var type = flashType || 'alert-error',
		hdr = header || 'Oops',
		msg = message || '';

	app.$flash.addClass( type ).slideDown(200)
		.find('div').text( msg ).end()
		.find('h4').text( hdr );

	// $(window).scrollTop(0);
	$("html, body").animate({ scrollTop: 0 }, 300);

};
app.flash.dismiss = function () {
	app.$flash.hide().removeClass('alert-error alert-warning alert-success');
	app.$flash.find('div, h4').text('');
};


// for when logging goes wild. pass a string and a hex or named css color
app.log = function (string, color) {
	var logged = string.toUpperCase();
	color = color || "#007";
	console.log("%c     " + logged + "     ",  "color:white; background-color:" + color + "");
};
