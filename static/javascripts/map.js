(function() {
  window.LR = window.LR || {};

  var Map = window.LR.Map = function(options) {
    this.$el = $(options.el);
    this.init();
  };
  Map.prototype = {
    init: function() {
      this.vectorLayer = null;
      this.currentHighlight = null;

      // Init map
      var raster = new ol.layer.Tile({
        source: new ol.source.OSM()
      });
      this.map = new ol.Map({
        layers: [raster],
        target: this.$el[0],
        view: new ol.View2D({
          //center: [-500000, 7300000],
          //zoom: 5
          center: [
                    14708.755563011973,
                    6761018.225448865
          ],
          zoom: 18
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
      $(this.map.getViewport()).on('mousemove', _.bind(this.onMousemove, this));
    },
    onMousemove: function(event) {
      var pixel = this.map.getEventPixel(event.originalEvent);
      var feature = this.map.forEachFeatureAtPixel(pixel, function(feature, layer) {
        return feature;
      });
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
      console.log('onMoveend')
      this.onGeoSuccess([{
        "address": "11 Fore Street, Harlow (CM17 0AA)",
        "extent": {
          "geometry": {
            "coordinates": [
              [
                [
                  [
                    14708.755563011973,
                    6761018.225448865
                  ],
                  [
                    14709.161068287178,
                    6761018.294465071
                  ],
                  [
                    14708.435732840697,
                    6761024.966253572
                  ],
                  [
                    14708.398674280676,
                    6761025.355691914
                  ],
                  [
                    14714.628369111884,
                    6761025.901180545
                  ],
                  [
                    14717.462192686182,
                    6761026.222616948
                  ],
                  [
                    14717.677197182695,
                    6761025.2939769225
                  ],
                  [
                    14725.204510948624,
                    6761026.060307912
                  ],
                  [
                    14736.21162987126,
                    6761027.161480935
                  ],
                  [
                    14746.571356929484,
                    6761028.200718575
                  ],
                  [
                    14747.634241033204,
                    6761019.269821937
                  ],
                  [
                    14747.80142376746,
                    6761017.808601182
                  ],
                  [
                    14747.361857752814,
                    6761008.274526637
                  ],
                  [
                    14747.14251453567,
                    6761000.756663681
                  ],
                  [
                    14745.669362713881,
                    6760988.98754546
                  ],
                  [
                    14737.630035003409,
                    6760990.032371336
                  ],
                  [
                    14732.52917425383,
                    6760989.45379999
                  ],
                  [
                    14732.80216481544,
                    6760987.746763348
                  ],
                  [
                    14730.376216412868,
                    6760987.575185578
                  ],
                  [
                    14728.694414239853,
                    6760987.462691532
                  ],
                  [
                    14728.6877217654,
                    6760987.786512725
                  ],
                  [
                    14719.15462008965,
                    6760987.418812016
                  ],
                  [
                    14717.909630210603,
                    6760987.342050606
                  ],
                  [
                    14710.83331394239,
                    6760987.096473619
                  ],
                  [
                    14710.360977361106,
                    6761004.100649248
                  ],
                  [
                    14709.200607157567,
                    6761008.584527049
                  ],
                  [
                    14708.77297452414,
                    6761013.28964111
                  ],
                  [
                    14709.420367678382,
                    6761013.351564559
                  ],
                  [
                    14708.755563011973,
                    6761018.225448865
                  ]
                ]
              ]
            ],
            "type": "MultiPolygon"
          }
        },
        "lenders": [
          {
            "name": "HSBC"
          }
        ],
        "registered_owners": [
          {
            "address": "123 Fake Street",
            "name": "Chris"
          }
        ],
        "title_number": "EX27651",
        "postcode" : "KT23 3AA"
      }]);
    },
    onGeoSuccess: function(results) {
      this.removeVectorLayer();

      var vectorLayer = new ol.layer.Vector({
        source: this.getSourceFromTitle(results[0]),
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

      this.setVectorLayer(vectorLayer);
    },
    getSourceFromTitle: function(title) {
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
          'features': [
            {
              "id": title['title_number'],
              "type":"Feature",
              "geometry": title['extent']['geometry'],
            }
          ]
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
    getViewExtentAsGeoJSON: function() {
      return {
        "type": "multi_polygon",
        "coordinates": [[this.getViewExtent()]]
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
