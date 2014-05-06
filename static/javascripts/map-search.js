(function() {
  window.LR = window.LR || {};

  var MapSearch = window.LR.MapSearch = function(options) {
    this.$el = $(options.el);
    this.$infoEl = $(options.infoEl);
    this.$startDrawingButton = $(options.startDrawingButton);
    this.$stopDrawingButton = $(options.stopDrawingButton);
    this.$drawingHelp = $(options.drawingHelp);
    this.geoUrl = options.geoUrl;
    this.postcodeCentre = options.postcodeCentre;
    this.init();
  };
  MapSearch.prototype = {
    init: function() {
      this.vectorLayer = null;
      this.currentHighlight = null;
      this.currentTitles = null;
      this.drawInteraction = null;

      // Init buttons
      this.$startDrawingButton.click(_.bind(this.startDrawing, this));
      this.$stopDrawingButton.click(_.bind(this.stopDrawing, this));

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
                    this.postcodeCentre['coordinates'][0],
                    this.postcodeCentre['coordinates'][1]
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
              color: '#blue',
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
    },
    onClick: function(event) {
      var pixel = this.map.getEventPixel(event.originalEvent);
      var feature = this.map.forEachFeatureAtPixel(pixel, function(feature, layer) {
        return feature;
      });

      if (feature) {
        // Hack - don't do interaction when clicking on polygon
        this.map.removeInteraction(this.drawInteraction);
        setTimeout(_.bind(function() {
          this.map.addInteraction(this.drawInteraction);
        }, this), 0);

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
      if (this.drawInteraction || !this.hasMapMoved()) {
        return;
      }
      this.fetchTitlesWithinViewExtent();
    },

    fetchTitlesWithinViewExtent: function() {
      this.fetchTitlesWithinPolygon(this.getViewExtentAsGeoJSON());
    },

    // Fetch the titles within a polygon and display them on the map
    fetchTitlesWithinPolygon: function(polygon) {
      console.log('Updating map', polygon);
      var url = this.geoUrl + '/titles?partially_contained_by=' + encodeURIComponent(JSON.stringify(polygon))
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

    startDrawing: function() {
      this.removeVectorLayer();
      this.drawInteraction = new ol.interaction.Draw({
        type: 'Polygon'
      });
      this.drawInteraction.on('drawend', _.bind(this.onDrawEnd, this));
      this.map.addInteraction(this.drawInteraction);
      this.$startDrawingButton.hide();
      this.$drawingHelp.show();
    },

    onDrawEnd: function(e) {
      var geojson = new ol.format.GeoJSON().writeFeature(e.feature);
      this.fetchTitlesWithinPolygon(geojson['geometry']);
    },

    stopDrawing: function() {
      this.map.removeInteraction(this.drawInteraction);
      this.drawInteraction = null;
      this.fetchTitlesWithinViewExtent();
      this.removeVectorLayer();
      this.$startDrawingButton.show();
      this.$drawingHelp.hide();
    }
  };
})();
