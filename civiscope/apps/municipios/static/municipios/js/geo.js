/**
 * GeoJSON utility for Colatina neighborhoods.
 * Uses Turf.js to calculate centroids of neighborhood polygons.
 */

const GeoUtils = (function() {
    let neighborhoodData = null;
    const centroidCache = new Map();

    /**
     * Loads the GeoJSON data.
     * @param {string} url - URL to the GeoJSON file.
     */
    async function loadGeoJSON(url) {
        try {
            const response = await fetch(url);
            neighborhoodData = await response.json();
            console.log("GeoJSON loaded successfully");
            return neighborhoodData;
        } catch (error) {
            console.error("Error loading GeoJSON:", error);
            return null;
        }
    }

    /**
     * Finds the centroid of a neighborhood by name.
     * @param {string} nomeBairro - Name of the neighborhood.
     * @returns {Array|null} - [lat, lng] or null if not found.
     */
    function getBairroCentroide(nomeBairro) {
        if (!neighborhoodData) {
            console.warn("GeoJSON data not loaded yet.");
            return null;
        }

        // Check cache first
        if (centroidCache.has(nomeBairro)) {
            return centroidCache.get(nomeBairro);
        }

        // Search in GeoJSON
        const feature = neighborhoodData.features.find(f => 
            f.properties && f.properties.name.toLowerCase() === nomeBairro.toLowerCase()
        );

        if (feature) {
            try {
                // Calculate centroid using Turf.js
                // Note: Turf expects [lng, lat]
                const centroid = turf.centroid(feature);
                const coords = [centroid.geometry.coordinates[1], centroid.geometry.coordinates[0]];
                
                // Cache it
                centroidCache.set(nomeBairro, coords);
                return coords;
            } catch (error) {
                console.error(`Error calculating centroid for ${nomeBairro}:`, error);
                return null;
            }
        }

        console.warn(`Neighborhood not found in GeoJSON: ${nomeBairro}`);
        return null;
    }

    return {
        loadGeoJSON,
        getBairroCentroide
    };
})();

// Export for global use as requested
window.getBairroCentroide = GeoUtils.getBairroCentroide;
window.GeoUtils = GeoUtils;
