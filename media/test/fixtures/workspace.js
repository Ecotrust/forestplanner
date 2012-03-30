  fixtures.workspace = {
    "generic-links": [{
      "models": ["trees_stand", "trees_forestproperty"],
      "uri-template": "/features/generic-links/links/geojson/{uid+}/",
      "select": "multiple single",
      "rel": "alternate",
      "title": "GeoJSON"
    }, {
      "title": "Copy",
      "models": ["trees_stand", "trees_forestproperty"],
      "uri-template": "/features/generic-links/links/copy/{uid+}/",
      "rel": "edit",
      "method": "POST",
      "select": "multiple single"
    }, {
      "title": "Delete",
      "models": ["trees_stand", "trees_forestproperty"],
      "confirm": "Are you sure you want to delete this feature and it's contents?",
      "uri-template": "/features/generic-links/links/delete/{uid+}/",
      "rel": "edit",
      "method": "DELETE",
      "select": "multiple single"
    }, {
      "models": ["trees_stand", "trees_forestproperty"],
      "uri-template": "/features/generic-links/links/png-image/{uid+}/",
      "select": "multiple single",
      "rel": "alternate",
      "title": "PNG Image"
    }, {
      "models": ["trees_stand", "trees_forestproperty"],
      "uri-template": "/features/generic-links/links/kml/{uid+}/",
      "select": "multiple single",
      "rel": "alternate",
      "title": "KML"
    }, {
      "models": ["trees_stand", "trees_forestproperty"],
      "uri-template": "/features/generic-links/links/kmz/{uid+}/",
      "select": "multiple single",
      "rel": "alternate",
      "title": "KMZ"
    }],
    "feature-classes": [{
      "link-relations": {
        "edit": [{
          "uri-template": "/features/stand/{uid}/form/",
          "title": "Edit"
        }, {
          "uri-template": "/features/stand/{uid}/share/",
          "title": "Share"
        }],
        "self": {
          "uri-template": "/features/stand/{uid}/",
          "title": "View"
        },
        "create": {
          "uri-template": "/features/stand/form/"
        }
      },
      "id": "trees_stand",
      "title": "Stand"
    }, {
      "link-relations": {
        "edit": [{
          "uri-template": "/features/forestproperty/{uid}/form/",
          "title": "Edit"
        }, {
          "uri-template": "/features/forestproperty/{uid}/share/",
          "title": "Share"
        }],
        "self": {
          "uri-template": "/features/forestproperty/{uid}/",
          "title": "View"
        },
        "alternate": [{
          "uri-template": "/features/forestproperty/links/property-stands-geojson/{uid+}/",
          "select": "single",
          "rel": "alternate",
          "title": "Property Stands GeoJSON"
        }],
        "create": {
          "uri-template": "/features/forestproperty/form/"
        }
      },
      "id": "trees_forestproperty",
      "collection": {
        "add": {
          "uri-template": "/features/forestproperty/{collection_uid}/add/{uid+}"
        },
        "classes": ["trees_stand"],
        "remove": {
          "uri-template": "/features/forestproperty/{collection_uid}/remove/{uid+}"
        }
      },
      "title": "ForestProperty"
    }]
  }
