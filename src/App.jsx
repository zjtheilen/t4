import React, { useEffect, useState, useRef } from 'react'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'

export default function App() {
  const mapContainer = useRef(null)
  const map = useRef(null)
  const [profiles, setProfiles] = useState([])
  const [selectedProfile, setSelectedProfile] = useState('fantasy_overland')
  const [routeResult, setRouteResult] = useState(null)
  const [stops, setStops] = useState(["Oakhaven", "Riverbend", "Northgate"])

  // Fetch profiles on mount
  useEffect(() => {
    fetch('/api/v1/profiles')
      .then(res => res.json())
      .then(data => setProfiles(data.profiles || []))
      .catch(err => console.error("Error fetching profiles:", err))
  }, [])

  // Initialize MapLibre map and load world layers
  useEffect(() => {
    if (map.current) return
    console.log("Initializing MapLibre instance...")

    map.current = new maplibregl.Map({
      container: mapContainer.current,
      style: {
        version: 8,
        sources: {
          'raster-tiles': {
            type: 'raster',
            tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
            tileSize: 256,
            attribution: '&copy; OpenStreetMap Contributors'
          }
        },
        layers: [
          {
            id: 'simple-tile-layer',
            type: 'raster',
            source: 'raster-tiles',
            minzoom: 0,
            maxzoom: 19
          }
        ]
      },
      center: [-117.15, 33.5],
      zoom: 6
    })

    map.current.on('load', async () => {
      console.log("Map 'load' event fired! Fetching world GeoJSON...")
      try {
        const res = await fetch('/api/v1/geojson/world')
        const data = await res.json()
        console.log("GeoJSON data received:", data)

        // Add Roads Source & Layer
        if (data.roads && data.roads.features) {
          map.current.addSource('roads', { type: 'geojson', data: data.roads })
          map.current.addLayer({
            id: 'road-layer',
            type: 'line',
            source: 'roads',
            paint: {
              'line-color': '#eab308',
              'line-width': 2,
              'line-dasharray': [2, 2]
            }
          })
        }

        // Add Settlements Source & Layer
        if (data.settlements && data.settlements.features) {
          map.current.addSource('settlements', { type: 'geojson', data: data.settlements })
          map.current.addLayer({
            id: 'settlement-layer',
            type: 'circle',
            source: 'settlements',
            paint: {
              'circle-radius': 8,
              'circle-color': '#ef4444',
              'circle-stroke-width': 2,
              'circle-stroke-color': '#ffffff'
            }
          })

          // Fit bounds to settlements
          // Fit bounds to settlements
          const coords = data.settlements.features.map(f => f.geometry.coordinates)
          if (coords.length > 0) {
            const bounds = coords.reduce((b, coord) => b.extend(coord), new maplibregl.LngLatBounds(coords[0], coords[0]))
            map.current.fitBounds(bounds, { padding: 80, maxZoom: 8, duration: 1000 })
          }
        }
      } catch (err) {
        console.error("Failed to load world GeoJSON onto map:", err)
      }
    })

    return () => map.current?.remove()
  }, [])

  // Run Itinerary & render path on map
  const handleTestRoute = async () => {
    try {
      const res = await fetch('/api/v1/itinerary', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          stops: stops,
          profile: selectedProfile
        })
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
    <div style={{ display: 'flex', height: '100vh', width: '100vw', overflow: 'hidden' }}>
      {/* Sidebar Control Panel */}
      <div style={{ width: '380px', background: '#1a1a1a', padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem', borderRight: '1px solid #333', zIndex: 10, overflowY: 'auto' }}>
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

        <button 
          onClick={handleTestRoute}
        style={{ padding: '0.75rem', background: '#2563eb', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}
        >
          Calculate Itinerary ({stops.join(' ➔ ')})
        </button>

        {routeResult && (
          <div style={{ background: '#222', padding: '1rem', borderRadius: '4px', fontSize: '0.85rem', border: '1px solid #444', display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
            <h4 style={{ margin: '0 0 0.5rem 0', color: '#60a5fa' }}>Route Ledger</h4>
            <p><strong>Path:</strong> {routeResult.path_names.join(' ➔ ')}</p>
            <p><strong>Distance:</strong> {routeResult.total_physical_km.toFixed(1)} km</p>
            <p><strong>Hexes Crossed:</strong> {routeResult.hexes_crossed}</p>
            <p><strong>{routeResult.time_unit_name}:</strong> {routeResult.time_units_traveled}</p>
            <p><strong>{routeResult.resource_name}:</strong> {routeResult.resources_consumed}</p>
          </div>
        )}
      </div>

      {/* Map Canvas */}
      <div ref={mapContainer} style={{ flex: 1, height: '100%' }} />
    </div>
  )
}
