(function() {
  window.LR = window.LR || {};

  var styles = {
    'MultiPolygon': [new ol.style.Style({
      stroke: new ol.style.Stroke({
        color: 'red',
        width: 1
      }),
      fill: new ol.style.Fill({
        color: 'rgba(255,0,0,0.2)'
      })
    })],
    'Polygon': [new ol.style.Style({
      stroke: new ol.style.Stroke({
        color: 'red',
        lineDash: [4],
        width: 3
      }),
      fill: new ol.style.Fill({
        color: 'rgba(255,0,0,0.2)'
      })
    })],
  };

  var styleFunction = function(feature, resolution) {
    return styles[feature.getGeometry().getType()];
  };

  var SingleExtentMap = window.LR.SingleExtentMap = function(options) {
    this.$el = $(options.el);
    this.extent = options.extent;

    this.vectorLayer = null;

    var layer = new ol.layer.Tile({
      name: 'TMS',
      source: new ol.source.XYZ({
        url: 'http://atlas1.viaeuropa.uk.com/viaeuropa/lreg140411/hybrid/{z}/{x}/{y}.png'
      })
    });
    this.map = new ol.Map({
      controls:[],
      layers: [layer],
      renderer: 'canvas',
      target: this.$el[0],
      view: new ol.View2D({
        center: [0, 0],
        zoom: options.zoom || 18
      })
    });

    if (this.extent) {
      this.setExtent(this.extent);
      this.setCenter(this.extent);
    }
  };
  SingleExtentMap.prototype = {
    setExtent: function(extent) {
      this.removeVectorLayer();
      var vectorSource = new ol.source.GeoJSON(
        /** @type {olx.source.GeoJSONOptions} */ ({
        object: {
          'type': 'FeatureCollection',
          'crs': {
            'type': 'name',
            'properties': {
              'name': 'EPSG:3857'
            }
          },
          'features': [
            {
              "type":"Feature",
              "geometry": extent['geometry']
            }
          ]
        }
      }));
      this.setVectorLayer(new ol.layer.Vector({
        source: vectorSource,
        style: styleFunction
      }));
    },
    setCenter: function(extent) {
      this.map.getView().setCenter(extent['geometry']['coordinates'][0][0][0]);
    },
    removeVectorLayer: function() {
      if (this.vectorLayer) {
        this.map.removeLayer(this.vectorLayer);
      }
    },
    setVectorLayer: function(layer) {
      this.map.addLayer(layer);
      this.vectorLayer = layer;
    },
  };
})();
