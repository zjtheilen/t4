import React, { useEffect, useState, useRef } from 'react'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'

const PROFILE_STYLES = {
  dcc: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
  backrooms: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
  fantasy_overland: 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',
  default: 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json'
}

export default function App() {
  const mapContainer = useRef(null)
  const map = useRef(null)
  const [isMounted, setIsMounted] = useState(false)
  const [profiles, setProfiles] = useState(['fantasy_overland', 'dcc', 'backrooms'])
  const [selectedProfile, setSelectedProfile] = useState('fantasy_overland')
  const [routeResult, setRouteResult] = useState(null)
  const [stops, setStops] = useState([])
  const worldDataRef = useRef(null)

  // Helper to draw or update the calculated route polyline on the map
  const updateRouteLayer = (mapInstance, geometry) => {
    if (!mapInstance) return

    const sourceId = 'active-route'
    const layerId = 'active-route-line'

    const geojson = {
      type: 'Feature',
      properties: {},
      geometry: geometry || { type: 'LineString', coordinates: [] }
    }

    if (mapInstance.getSource(sourceId)) {
      mapInstance.getSource(sourceId).setData(geojson)
    } else {
      mapInstance.addSource(sourceId, { type: 'geojson', data: geojson })
      mapInstance.addLayer({
        id: layerId,
        type: 'line',
        source: sourceId,
        layout: {
          'line-join': 'round',
          'line-cap': 'round'
        },
        paint: {
          'line-color': '#3b82f6', // Tactical blue route highlight
          'line-width': 5,
          'line-opacity': 0.85
        }
      })
    }

    // Automatically fit bounds to the calculated route
    if (geometry && geometry.coordinates && geometry.coordinates.length > 0) {
      const coords = geometry.coordinates
      const bounds = coords.reduce(
        (b, coord) => b.extend(coord),
        new maplibregl.LngLatBounds(coords[0], coords[0])
      )
      mapInstance.fitBounds(bounds, { padding: 100, maxZoom: 11, duration: 1000 })
    }
  }

  // Trigger route rendering whenever routeResult updates
  useEffect(() => {
    if (!map.current) return
    if (routeResult && routeResult.geometry) {
      updateRouteLayer(map.current, routeResult.geometry)
    }
  }, [routeResult])

  // Trigger mount flag on initial render to ensure DOM node is painted
  useEffect(() => {
    setIsMounted(true)
  }, [])

  // Fetch profiles on mount
  useEffect(() => {
    fetch('/api/v1/profiles')
      .then(res => res.json())
      .then(data => {
        if (Array.isArray(data)) setProfiles(data)
        else if (data.profiles && Array.isArray(data.profiles)) setProfiles(data.profiles)
      })
      .catch(err => console.warn("Using default profiles:", err))
  }, [])

  // Helper to add/update world layers on map
  const addWorldLayers = (mapInstance, data) => {
    if (!mapInstance || !data) return

    if (data.roads && data.roads.features) {
      if (mapInstance.getSource('roads')) {
        mapInstance.getSource('roads').setData(data.roads)
      } else {
        mapInstance.addSource('roads', { type: 'geojson', data: data.roads })
        mapInstance.addLayer({
          id: 'road-layer',
          type: 'line',
          source: 'roads',
          paint: {
            'line-color': '#2563eb',
            'line-width': 3,
            'line-dasharray': [2, 2]
          }
        })
      }
    }

    if (data.settlements && data.settlements.features) {
      if (mapInstance.getSource('settlements')) {
        mapInstance.getSource('settlements').setData(data.settlements)
      } else {
        mapInstance.addSource('settlements', { type: 'geojson', data: data.settlements })
        mapInstance.addLayer({
          id: 'settlement-layer',
          type: 'circle',
          source: 'settlements',
          paint: {
            'circle-radius': 9,
            'circle-color': '#ef4444',
            'circle-stroke-width': 2,
            'circle-stroke-color': '#ffffff'
          }
        })

        mapInstance.on('click', 'settlement-layer', (e) => {
          if (e.features && e.features.length > 0) {
            const settlementName = e.features[0].properties.name || e.features[0].properties.id
            setStops(prevStops => {
              if (prevStops[prevStops.length - 1] === settlementName) return prevStops
              return [...prevStops, settlementName]
            })
          }
        })

        mapInstance.on('mouseenter', 'settlement-layer', () => {
          mapInstance.getCanvas().style.cursor = 'pointer'
        })
        mapInstance.on('mouseleave', 'settlement-layer', () => {
          mapInstance.getCanvas().style.cursor = ''
        })
      }
    }
  }

  // Initialize Map instance once the DOM container is guaranteed to be mounted
  useEffect(() => {
    if (!isMounted) return
    if (map.current) return
    if (!mapContainer.current) return

    const mapInstance = new maplibregl.Map({
      container: mapContainer.current,
      style: PROFILE_STYLES['fantasy_overland'],
      center: [-117.15, 33.5],
      zoom: 8
    })
    map.current = mapInstance

    const initMap = async () => {
      try {
        const res = await fetch('/api/v1/geojson/world')
        const data = await res.json()
        worldDataRef.current = data

        if (mapInstance.isStyleLoaded()) {
          addWorldLayers(mapInstance, data)
        } else {
          mapInstance.once('load', () => addWorldLayers(mapInstance, data))
        }

        if (data.settlements && data.settlements.features && data.settlements.features.length > 0) {
          const coords = data.settlements.features.map(f => f.geometry.coordinates)
          const bounds = coords.reduce((b, coord) => b.extend(coord), new maplibregl.LngLatBounds(coords[0], coords[0]))
          mapInstance.fitBounds(bounds, { padding: 80, maxZoom: 10, duration: 1000 })
        }
      } catch (err) {
        console.error("Failed to load world GeoJSON:", err)
      }
    }

    mapInstance.once('load', initMap)

    return () => {
      mapInstance.remove()
      map.current = null
    }
  }, [isMounted])

  // Style switching with robust layer re-application
  useEffect(() => {
    if (!map.current) return
    const newStyle = PROFILE_STYLES[selectedProfile] || PROFILE_STYLES.default
    
    map.current.setStyle(newStyle)
    map.current.once('style.load', () => {
      if (worldDataRef.current) {
        addWorldLayers(map.current, worldDataRef.current)
      }
    })
  }, [selectedProfile])

  // Itinerary calculation
  const handleTestRoute = async () => {
    if (stops.length < 2) {
      alert("Please select at least 2 stops on the map.")
      return
    }

    try {
      const res = await fetch('/api/v1/itinerary', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ stops, profile: selectedProfile })
      })
      const json = await res.json()
      if (json.status === 'success') {
        setRouteResult(json.data)
      } else {
        alert(`Routing error: ${json.detail || 'Unknown error'}`)
      }
    } catch (err) {
      console.error("Routing request failed:", err)
    }
  }

  return (
    <div style={{ display: 'flex', height: '100vh', width: '100vw', overflow: 'hidden', margin: 0, padding: 0 }}>
      {/* Sidebar Control Panel */}
      <div style={{ width: '380px', background: '#1a1a1a', padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem', borderRight: '1px solid #333', zIndex: 10, overflowY: 'auto', color: '#fff', boxSizing: 'border-box' }}>
        <h2>T4 Visualizer</h2>
        <p style={{ fontSize: '0.85rem', color: '#aaa' }}>Topographic Terrain Traversal Tool</p>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <label style={{ fontSize: '0.9rem', fontWeight: 'bold' }}>Traversal Profile:</label>
          <select 
            value={selectedProfile} 
            onChange={e => setSelectedProfile(e.target.value)}
            style={{ padding: '0.5rem', background: '#2a2a2a', color: '#fff', border: '1px solid #444', borderRadius: '4px' }}
          >
            {profiles.map(p => <option key={p} value={p}>{p}</option>)}
          </select>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', background: '#222', padding: '0.75rem', borderRadius: '4px', border: '1px solid #333' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <label style={{ fontSize: '0.9rem', fontWeight: 'bold', color: '#60a5fa' }}>Itinerary Stops (Click Map):</label>
            <button onClick={() => setStops([])} style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer', fontSize: '0.75rem' }}>Clear</button>
          </div>
          <div style={{ fontSize: '0.85rem', color: '#ddd', minHeight: '30px', display: 'flex', flexWrap: 'wrap', gap: '4px', alignItems: 'center' }}>
            {stops.length === 0 ? (
              <span style={{ color: '#777', fontStyle: 'italic' }}>Click settlement nodes on the map...</span>
            ) : (
              stops.map((stop, idx) => (
                <span key={idx} style={{ background: '#333', padding: '2px 6px', borderRadius: '3px', border: '1px solid #444' }}>
                  {idx + 1}. {stop}
                </span>
              ))
            )}
          </div>
        </div>

        <button onClick={handleTestRoute} style={{ padding: '0.75rem', background: '#2563eb', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}>
          Calculate Itinerary ({stops.length} Stops)
        </button>

        {routeResult && (
          <div style={{ background: '#222', padding: '1rem', borderRadius: '4px', fontSize: '0.85rem', border: '1px solid #444', display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
            <h4 style={{ margin: '0 0 0.5rem 0', color: '#60a5fa' }}>Route Ledger</h4>
            <p><strong>Path:</strong> {routeResult.path_names?.join(' ➔ ')}</p>
            <p><strong>Distance:</strong> {routeResult.total_physical_km?.toFixed(1)} km</p>
            <p><strong>Hexes Crossed:</strong> {routeResult.hexes_crossed}</p>
            <p><strong>{routeResult.time_unit_name || 'Time'}:</strong> {routeResult.time_units_traveled}</p>
            <p><strong>{routeResult.resource_name || 'Resource'}:</strong> {routeResult.resources_consumed}</p>
          </div>
        )}
      </div>

      {/* Map Canvas Container */}
      <div style={{ flex: 1, height: '100%', position: 'relative' }}>
        <div ref={mapContainer} style={{ position: 'absolute', top: 0, bottom: 0, left: 0, right: 0 }} />
      </div>
    </div>
  )
}
