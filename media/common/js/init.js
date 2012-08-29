// name space for app

app.properties = {
    viewModel: new propertiesViewModel()
};

app.onResize = function () {
    $("#map").height($(window).height() - 114);
    map.render('map');
};

$(document).ready(function () {

    app.properties.viewModel.init()
    .done(function () {
        // apply the viewmodel
        ko.applyBindings(app.properties.viewModel, document.getElementById('property-html'));
        app.onResize();
    })
    .fail(function () {
        map.zoomToExtent(OpenLayers.Bounds.fromArray([-13954802.50397, 5681411.4375898, -13527672.389972, 5939462.8450446]));
        ko.applyBindings(app.viewModel);
    });

    $(window).resize(app.onResize);

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
        };
        if (!file) {
            $("#upload-file-required").fadeIn();
            return false;
        };

        $("#uploadProgress").show();
    },
    uploadProgress: function(event, position, total, percentComplete) {
        var percentVal = percentComplete + '%';
        $("#uploadProgress .bar").css('width', percentVal);
        if (percentComplete > 99) {
            $("#uploadResponse").html('<p class="label label-info">Upload complete. Processing stand data...</p>');
        }
    },
    complete: function(xhr) {
        $("#uploadResponse").html(xhr.responseText);
        $("#uploadProgress").hide();
        $("#uploadProgress .bar").css('width', '0%');
        if (xhr.status == 201) {
            app.properties.viewModel.afterUploadSuccess();
        }
    }
    }; 
    $('#uploadForm').submit( function () {
        $(this).ajaxSubmit(options); 
        return false; 
    });

});


