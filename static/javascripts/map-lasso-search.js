(function() {
  window.LR = window.LR || {};

  var MapLassoSearch = window.LR.MapLassoSearch = function(options) {
    this.$el = $(options.el);
    this.$infoEl = $(options.infoEl);
    this.geoUrl = options.geoUrl;
    this.postcodeCentre = options.postcodeCentre;
    this.init();
  };
  MapLassoSearch.prototype = {
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
        layers: [layer,vector],
        target: this.$el[0],
        view: new ol.View2D({
          //center: [-500000, 7300000],
          //zoom: 5
          center: [
            14708.755563011973,
            6761018.225448865   
          ],
          zoom: 13
        }),
        interactions: [new ol.interaction.DoubleClickZoom({delta: 0}), 
                     new ol.interaction.DragPan({}),
                     new ol.interaction.MouseWheelZoom({}),
                     new ol.interaction.PinchRotate({}),
                     new ol.interaction.PinchZoom({})]
      });
      this.map.on('moveend', this.onMoveend, this);
      this.featureOverlay = new ol.FeatureOverlay({
        map: this.map,
        style: function(feature, resolution) {
          return [new ol.style.Style({
            stroke: new ol.style.Stroke({
              color: 'blue',
              width: 1
            }),
            fill: new ol.style.Fill({
              color: 'rgba(0,0,255,0.2)'
            }),
          })];
        }
      });

      // Init mouse events
      $(this.map.getViewport()).on('click', _.bind(this.onClick, this));
      var el = document.getElementById("search-button");
      el.addEventListener("click", this.search.bind(this), false);
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
      var url = this.geoUrl + '/titles?partially_contained_by=' + lasso
      $.ajax({
        url: url,
        dataType: 'jsonp',
        success: _.bind(this.onGeoSuccess, this),
      });
    },
    search: function() {
      var layers = this.map.getLayers();
      var polyLayer = null;
      layers.forEach(function(layer) {
        if (layer.get('name') == 'Polygon Layer') {
           polyLayer = layer;
        }
      });
      source = polyLayer.getSource();
      features = source.getFeatures();
      var format = new ol.format.GeoJSON();
      featureGeoJSON = format.writeFeature(features[0]); 
      geometryGeoJSON = featureGeoJSON['geometry'];
      lasso = JSON.stringify( geometryGeoJSON);               
      
      this.map.removeInteraction(draw);

      console.log('Updating map for search')
      var url = this.geoUrl + '/titles?partially_contained_by=' + lasso
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
            color: 'blue',
            width: 1
          }),
          fill: new ol.style.Fill({
            color: 'rgba(0, 0, 255, 0.1)'
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