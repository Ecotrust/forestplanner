DEFAULT_STAND_SPLASH = "/static/discovery/img/Evergreen_(PSF).png"
DEFAULT_STAND_IMAGE = "/static/discovery/img/Trees_icon_wide.png"

CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'Custom',
        'toolbar_Custom': [
            ['Format'],
            ['Bold', 'Italic', 'Underline','Strike','Subscript','Superscript'],
            ['NumberedList', 'BulletedList', '-', 'Outdent', 'Indent', '-', 'JustifyLeft', 'JustifyCenter', 'JustifyRight', 'JustifyBlock'],
            ['Link', 'Unlink'],
            ['Image','Table','HorizontalRule','SpecialChar'],
            [ 'TextColor','BGColor' ],
            ['Undo','Redo'],
            ['RemoveFormat', 'Source']
        ],
    }
}

IMPORT_TREELIST = False

HARD_SOFTWOOD_LOOKUP = {
    'Douglas-fir': 'softwood',
    'Nonstocked': 'unknown',
    'Bigleaf maple': 'hardwood',
    'Red alder': 'hardwood',
    'Lodgepole pine': 'softwood',
    'Tanoak': 'hardwood',
    'Western larch': 'softwood',
    'Oregon white oak': 'hardwood',
    'Western juniper': 'softwood',
    'Pacific madrone': 'hardwood',
    'Grand fir': 'softwood',
    'Western hemlock': 'softwood',
    'Unknown; access denied': 'unknown',
    'Western white pine': 'softwood',
    'Ponderosa pine': 'softwood',
    'Oregon ash': 'hardwood',
    'Western redcedar': 'softwood',
    'Sitka spruce': 'softwood',
    'Black cottonwood': 'hardwood',
    'Engelmann spruce': 'softwood',
    'White fir': 'softwood',
    'Incense cedar': 'softwood',
    'Quaking aspen': 'hardwood',
    'Curlleaf mountain-mahogany': 'hardwood',
    'Mountain hemlock': 'softwood',
    'Shasta red fir': 'softwood',
    'Subalpine fir': 'softwood',
    'Whitebark pine': 'softwood',
    'Pacific silver fir': 'softwood',
    'Noble fir': 'softwood',
    'Port-Orford-cedar': 'softwood',
    'California-laurel': 'hardwood',
    'Canyon live oak': 'hardwood',
    'Jeffrey pine': 'softwood',
    'Golden chinkapin': 'hardwood',
    'Sugar pine': 'softwood',
    'Cherry': 'hardwood',
    'Unknown type': 'unknown',
    'Alaska cedar': 'softwood',
    'Subablpine larch': 'softwood',
    'Western paper birch': 'hardwood',
    'Willow': 'hardwood',
    'California black oak': 'hardwood',
    'Pacific yew': 'softwood',
    'White alder': 'hardwood',
    'Scotch pine': 'softwood',
    'Redwood': 'softwood',
    'Apple': 'hardwood',
    'Knobcone pine': 'softwood',
}
