(function() {
  window.LR = window.LR || {};

  var MapSearch = window.LR.MapSearch = function(options) {
    this.$el = $(options.el);
    this.$infoEl = $(options.infoEl);
    this.geoUrl = options.geoUrl;
    this.init();
  };
  MapSearch.prototype = {
    init: function() {
      this.vectorLayer = null;
      this.currentHighlight = null;
      this.currentTitles = null;

      // Init map
      var layer = new ol.layer.Tile({
        name: 'TMS',
        source: new ol.source.XYZ({
          url: 'http://atlas1.viaeuropa.uk.com/viaeuropa/lreg140411/hybrid/{z}/{x}/{y}.png'
        })
      });
      this.map = new ol.Map({
        layers: [layer],
        target: this.$el[0],
        view: new ol.View2D({
          //center: [-500000, 7300000],
          //zoom: 5
          center: [
                    14708.755563011973,
                    6761018.225448865
          ],
          zoom: 16
        })
      });
      this.map.on('moveend', this.onMoveend, this);
      this.featureOverlay = new ol.FeatureOverlay({
        map: this.map,
        style: function(feature, resolution) {
          return [new ol.style.Style({
            stroke: new ol.style.Stroke({
              color: '#f00',
              width: 1
            }),
            fill: new ol.style.Fill({
              color: 'rgba(255,0,0,0.2)'
            }),
          })];
        }
      });

      // Init mouse events
      $(this.map.getViewport()).on('click', _.bind(this.onClick, this));
    },
    onClick: function(event) {
      var pixel = this.map.getEventPixel(event.originalEvent);
      var feature = this.map.forEachFeatureAtPixel(pixel, function(feature, layer) {
        return feature;
      });

      if (feature) {
        this.$infoEl.show();

        template = _.template('<h2><%= address %></h2><p><a href="/properties/<%= title_number %>">View full details</a>');
        this.$infoEl.html(template(this.currentTitles[feature.getId()]));
      }
      else {
        this.$infoEl.text('');
        this.$infoEl.hide();
      }

      if (feature !== this.currentHighlight) {
        if (this.currentHighlight) {
          this.featureOverlay.removeFeature(this.currentHighlight);
        }
        if (feature) {
          this.featureOverlay.addFeature(feature);
        }
        this.currentHighlight = feature;
      }
    },
    onMoveend: function() {
      if (!this.hasMapMoved()) {
        return;
      }
      console.log('Updating map')
      var url = this.geoUrl + '/titles?partially_contained_by=' + encodeURIComponent(JSON.stringify(this.getViewExtentAsGeoJSON()))
      $.ajax({
        url: url,
        dataType: 'jsonp',
        success: _.bind(this.onGeoSuccess, this),
      });
    },
    onGeoSuccess: function(results) {
      this.removeVectorLayer();

      var vectorLayer = new ol.layer.Vector({
        source: this.getSourceFromTitles(results['objects']),
        style: [new ol.style.Style({
          stroke: new ol.style.Stroke({
            color: 'red',
            width: 1
          }),
          fill: new ol.style.Fill({
            color: 'rgba(255, 0, 0, 0.1)'
          })
        })],
      });

      // hash indexed by title number
      this.currentTitles = _.object(_.map(results['objects'], function(title) {
        title['address'] = title['address'].replace(',', ',<br>').replace('(', '<br>').replace(')', '')
        return [title['title_number'], title];
      }));

      this.setVectorLayer(vectorLayer);
    },

    getSourceFromTitles: function(titles) {
      var features = _.map(titles, function(title) {
        return {
          "id": title['title_number'],
          "type":"Feature",
          "geometry": title['extent']['geometry'],
        };
      });
      return new ol.source.GeoJSON({
        projection: 'EPSG:3857',
        object: {
          'type': 'FeatureCollection',
          'crs': {
            'type': 'name',
            'properties': {
              'name': 'EPSG:3857'
            }
          },
          'features': features,
        },
      });
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
    getViewExtent: function() {
      return this.map.getView().calculateExtent(this.map.getSize());
    },
    getViewExtentPolygon: function() {
      e = this.getViewExtent();
      // min(x), min(y), max(x), max(y)
      return [
        [e[0], e[1]],
        [e[2], e[1]],
        [e[2], e[3]],
        [e[0], e[3]],
        [e[0], e[1]],
      ];
    },
    getViewExtentAsGeoJSON: function() {
      return {
        "type": "Polygon",
        "coordinates": [this.getViewExtentPolygon()],
        'crs': {
          'type': 'name',
          'properties': {
            'name': 'EPSG:3857'
          }
        },
      };
    },
    // Returns whether or not the map has moved since this function
    // was last called
    hasMapMoved: function() {
      var extent = this.getViewExtent();
      var result = false;
      if (!_.isEqual(extent, this._previousExtent)) {
        result = true;
      }
      this._previousExtent = this.getViewExtent()
      return result;
    },
  };
})();
