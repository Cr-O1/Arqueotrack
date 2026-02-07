// Sistema de dibujo de polÃ­gonos para yacimientos y sectores
function initPolygonDrawMap(options = {}) {
    const mapElement = document.getElementById(options.mapId || 'polygon-map');
    if (!mapElement) return null;

    const defaultLat = options.lat || 40.4168;
    const defaultLng = options.lng || -3.7038;
    const existingPolygon = options.existingPolygon || null;

    const map = L.map(options.mapId || 'polygon-map').setView([defaultLat, defaultLng], options.zoom || 10);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19
    }).addTo(map);

    const drawnItems = new L.FeatureGroup();
    map.addLayer(drawnItems);

    const drawControl = new L.Control.Draw({
        draw: {
            polygon: {
                allowIntersection: false,
                showArea: true,
                shapeOptions: {
                    color: options.polygonColor || '#6366F1',
                    fillColor: options.polygonColor || '#6366F1',
                    fillOpacity: 0.3,
                    weight: 3
                }
            },
            polyline: false,
            rectangle: {
                shapeOptions: {
                    color: options.polygonColor || '#6366F1',
                    fillColor: options.polygonColor || '#6366F1',
                    fillOpacity: 0.3,
                    weight: 3
                }
            },
            circle: false,
            circlemarker: false,
            marker: false
        },
        edit: {
            featureGroup: drawnItems,
            remove: true
        }
    });

    map.addControl(drawControl);

    const polygonInput = document.getElementById(options.polygonInputId || 'polygon_geojson');
    const areaInput = document.getElementById(options.areaInputId || 'area_m2');
    const areaDisplay = document.getElementById(options.areaDisplayId || 'area-display');
    const latInput = document.getElementById('lat');
    const lngInput = document.getElementById('lng');

    // Calcular Ã¡rea usando Turf.js si estÃ¡ disponible
    function calculateArea(layer) {
        if (typeof turf !== 'undefined') {
            const geojson = layer.toGeoJSON();
            const areaM2 = turf.area(geojson);
            return Math.round(areaM2 * 100) / 100;
        }
        return null;
    }

    // Obtener centroide del polÃ­gono
    function getCentroid(layer) {
        if (typeof turf !== 'undefined') {
            const geojson = layer.toGeoJSON();
            const centroid = turf.centroid(geojson);
            return {
                lat: centroid.geometry.coordinates[1],
                lng: centroid.geometry.coordinates[0]
            };
        }

        // Fallback: usar centro de bounds
        const bounds = layer.getBounds();
        const center = bounds.getCenter();
        return { lat: center.lat, lng: center.lng };
    }

    // CORREGIDO: Actualizar datos del polÃ­gono
    function updatePolygonData(layer) {
        const geojson = layer.toGeoJSON().geometry;

        // Guardar GeoJSON
        if (polygonInput) {
            polygonInput.value = JSON.stringify(geojson);
            console.log('PolÃ­gono guardado:', geojson);
        }

        // Calcular y guardar Ã¡rea
        const area = calculateArea(layer);
        if (area !== null) {
            if (areaInput) {
                areaInput.value = area.toFixed(2);
                console.log('Ãrea calculada:', area, 'mÂ²');
            }
            if (areaDisplay) {
                areaDisplay.textContent = `Ãrea calculada: ${formatArea(area)}`;
                areaDisplay.style.display = 'block';
            }
        }

        // Guardar centroide como coordenadas principales
        const centroid = getCentroid(layer);
        if (latInput) latInput.value = centroid.lat.toFixed(6);
        if (lngInput) lngInput.value = centroid.lng.toFixed(6);

        const coordsDisplay = document.getElementById('coords-display');
        if (coordsDisplay) {
            coordsDisplay.textContent = `Centro: ${centroid.lat.toFixed(6)}, ${centroid.lng.toFixed(6)}`;
        }
    }

    // Formatear Ã¡rea para mostrar
    function formatArea(areaM2) {
        if (areaM2 >= 10000) {
            return `${(areaM2 / 10000).toFixed(2)} ha (${areaM2.toLocaleString()} mÂ²)`;
        }
        return `${areaM2.toLocaleString()} mÂ²`;
    }

    // Limpiar datos del polÃ­gono
    function clearPolygonData() {
        if (polygonInput) polygonInput.value = '';
        if (areaInput) areaInput.value = '';
        if (areaDisplay) {
            areaDisplay.textContent = '';
            areaDisplay.style.display = 'none';
        }
        const coordsDisplay = document.getElementById('coords-display');
        if (coordsDisplay) coordsDisplay.textContent = '';
    }

    // Evento: PolÃ­gono creado
    map.on(L.Draw.Event.CREATED, function(e) {
        drawnItems.clearLayers(); // Solo un polÃ­gono a la vez
        drawnItems.addLayer(e.layer);
        updatePolygonData(e.layer);

        // Centrar mapa en el polÃ­gono
        map.fitBounds(e.layer.getBounds().pad(0.1));
    });

    // Evento: PolÃ­gono editado
    map.on(L.Draw.Event.EDITED, function(e) {
        e.layers.eachLayer(function(layer) {
            updatePolygonData(layer);
        });
    });

    // Evento: PolÃ­gono eliminado
    map.on(L.Draw.Event.DELETED, function(e) {
        if (drawnItems.getLayers().length === 0) {
            clearPolygonData();
        }
    });

    // Cargar polÃ­gono existente si se proporciona
    if (existingPolygon) {
        try {
            let geojsonData = existingPolygon;
            if (typeof existingPolygon === 'string') {
                geojsonData = JSON.parse(existingPolygon);
            }

            const layer = L.geoJSON(geojsonData, {
                style: {
                    color: options.polygonColor || '#6366F1',
                    fillColor: options.polygonColor || '#6366F1',
                    fillOpacity: 0.3,
                    weight: 3
                }
            });

            layer.eachLayer(function(l) {
                drawnItems.addLayer(l);
            });

            map.fitBounds(drawnItems.getBounds().pad(0.1));

            // Actualizar datos
            drawnItems.eachLayer(function(l) {
                updatePolygonData(l);
            });
        } catch (e) {
            console.error('Error loading existing polygon:', e);
        }
    }

    return {
        map: map,
        drawnItems: drawnItems,
        clearPolygon: function() {
            drawnItems.clearLayers();
            clearPolygonData();
        },
        updateData: function(layer) {
            updatePolygonData(layer);
        }
    };
}

// FunciÃ³n especÃ­fica para sectores
function initSectorPolygonMap(options = {}) {
    return initPolygonDrawMap({
        ...options,
        mapId: options.mapId || 'sector-polygon-map',
        polygonInputId: options.polygonInputId || 'polygon_geojson',
        areaInputId: options.areaInputId || 'area',
        areaDisplayId: options.areaDisplayId || 'sector-area-display'
    });
}

// Exportar funciones
window.initPolygonDrawMap = initPolygonDrawMap;
window.initSectorPolygonMap = initSectorPolygonMap;