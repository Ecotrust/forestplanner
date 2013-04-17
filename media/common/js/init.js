// name space for app

app.properties = {
    viewModel: new propertiesViewModel()
};

app.onResize = function () {
    var height = $(window).height();
    var width = $(window).width();

    $("#map").height(height - 114);
    map.render('map');

    divWidth = width * (7/12); // span7
    if (divWidth > height) {
        // "widescreen" so go side-by-side
        $(".timemap-container").width('48%');
        $(".timemap").height(height - 264);
    } else {
        // "narrow" so go top-to-bottom
        $(".timemap-container").width('99%');
        $(".timemap").height((height - 284)/2.0);
    }
};

$(document).ready(function () {

    ko.applyBindings(app.properties.viewModel, document.getElementById('property-html'));
    $(window).resize(app.onResize);
    app.onResize();
    map.zoomToExtent(OpenLayers.Bounds.fromArray([-13954802.50397, 5681411.4375898, -13527672.389972, 5939462.8450446]));

    var options = {
    beforeSubmit: function(formData, jqForm, options) {
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
    uploadProgress: function(event, position, total, percentComplete) {
        var percentVal = percentComplete + '%';
        $("#uploadProgress .bar").css('width', percentVal);
        if (percentComplete > 99) {
            $("#uploadProgress").hide();
            $("#uploadResponse").html('<p class="label label-info">Upload complete. Processing stand data...</p>');
        }
    },
    complete: function(xhr) {
        $("#uploadProgress").hide();
        $("#uploadProgress .bar").css('width', '0%');
    },
    error: function(data, status, xhr) {
        $("#uploadResponse").html(data.responseText);
    },
    success: function(data, status, xhr) {
        if (xhr.status == 201) {
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
    $('#uploadForm').submit( function () {
        $(this).ajaxSubmit(options); 
        return false; 
    });
    $('.manage-your-properties').click( function(e) {
        e.preventDefault();
        $('div#home-html').hide();
        app.properties.viewModel.init();
    });

});
