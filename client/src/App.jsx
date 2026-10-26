import React, { useEffect, useRef, useState } from 'react';
import * as maplibregl from 'maplibre-gl';
import { setWorkerUrl } from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url';

setWorkerUrl(workerUrl);

export default function App() {
  const mapContainer = useRef(null);
  const map = useRef(null);
  
  const [nodes, setNodes] = useState([]);
  const [profiles, setProfiles] = useState([]);
  const [roads, setRoads] = useState([]);
  const [overrides, setOverrides] = useState({});
  const [selectedOrigin, setSelectedOrigin] = useState('oakhaven');
  const [selectedStops, setSelectedStops] = useState(['riverbend', 'northgate']);
  const [selectedProfile, setSelectedProfile] = useState('dcc_death_sport');
  const [routeData, setRouteData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [copyStatus, setCopyStatus] = useState(false);

  const popupRef = useRef(new maplibregl.Popup({ closeButton: false, closeOnClick: false, offset: 12 }));

  const pixelToIdentity = (x, y) => {
    const lng = (x / 1168) * 120 - 60;
    const lat = 40 - (y / 784) * 80;
    return [lng, lat];
  };

  useEffect(() => {
    if (map.current) return;

    map.current = new maplibregl.Map({
      container: mapContainer.current,
      style: {
        version: 8,
        projection: { type: 'identity' },
        sources: {},
        layers: [{ id: 'background', type: 'background', paint: { 'background-color': '#0f172a' } }]
      },
      center: [0, 0],
      zoom: 1.5
    });

    const initMap = async () => {
      try {
        map.current.addSource('eldmere-map', {
          type: 'image',
          url: '/eldmere.jpg',
          coordinates: [
            [-60, 40],
            [60, 40],
            [60, -40],
            [-60, -40]
          ]
        });
      
        map.current.addLayer({
          id: 'eldmere-layer',
          type: 'raster',
          source: 'eldmere-map',
          paint: { 'raster-fade-duration': 0 }
        });
      
        const [roadsRes, overridesRes, nodesRes, profilesRes] = await Promise.all([
          fetch('http://localhost:8000/api/roads'),
          fetch('http://localhost:8000/api/overrides'),
          fetch('http://localhost:8000/api/nodes'),
          fetch('http://localhost:8000/api/profiles')
        ]);

        const roadsGeoJson = await roadsRes.json();
        const overridesData = await overridesRes.json();
        const nodesData = await nodesRes.json();
        const profilesData = await profilesRes.json();

        setRoads(roadsGeoJson.features);
        setOverrides(overridesData);
        setNodes(nodesData);
        setProfiles(profilesData);

        const transformedRoadsGeoJson = {
          ...roadsGeoJson,
          features: roadsGeoJson.features.map(feature => ({
            ...feature,
            geometry: {
              ...feature.geometry,
              coordinates: feature.geometry.coordinates.map(coord => pixelToIdentity(coord[0], coord[1]))
            }
          }))
        };

        map.current.addSource('roads-source', {
          type: 'geojson',
          data: transformedRoadsGeoJson
        });
        
        map.current.addLayer({
          id: 'roads-layer',
          type: 'line',
          source: 'roads-source',
          layout: { 'line-join': 'round', 'line-cap': 'round' },
          paint: {
            'line-color': ['match', ['get', 'status'], 'closed', '#ef4444', '#94a3b8'],
            'line-width': ['match', ['get', 'status'], 'closed', 4, 2],
            'line-dasharray': [2, 2]
          }
        });

        const nodesGeoJson = {
          type: 'FeatureCollection',
          features: nodesData.map(n => {
            const [lng, lat] = pixelToIdentity(n.coordinates[0], n.coordinates[1]);
            return {
              type: 'Feature',
              geometry: { type: 'Point', coordinates: [lng, lat] },
              properties: { name: n.name, id: n.id, type: n.type }
            };
          })
        };

        map.current.addSource('nodes-source', {
          type: 'geojson',
          data: nodesGeoJson
        });

        map.current.addLayer({
          id: 'nodes-layer',
          type: 'circle',
          source: 'nodes-source',
          paint: {
            'circle-radius': 7,
            'circle-color': '#e11d48',
            'circle-stroke-width': 2,
            'circle-stroke-color': '#ffffff'
          }
        });

        map.current.on('mouseenter', 'nodes-layer', (e) => {
          map.current.getCanvas().style.cursor = 'pointer';
          const coordinates = e.features[0].geometry.coordinates.slice();
          const { name, id, type } = e.features[0].properties;
          popupRef.current.setLngLat(coordinates).setHTML(`
            <div style="color: #0f172a; font-family: sans-serif; padding: 2px;">
              <strong style="font-size: 13px;">${name}</strong><br/>
              <span style="font-size: 11px; color: #475569;">Type: ${type} (${id})</span>
            </div>
          `).addTo(map.current);
        });

        map.current.on('mouseleave', 'nodes-layer', () => {
          map.current.getCanvas().style.cursor = '';
          popupRef.current.remove();
        });

        map.current.on('mouseenter', 'roads-layer', (e) => {
          map.current.getCanvas().style.cursor = 'pointer';
          const coordinates = e.lngLat;
          const { road_id, type, status, reason } = e.features[0].properties;
          popupRef.current.setLngLat(coordinates).setHTML(`
            <div style="color: #0f172a; font-family: sans-serif; padding: 2px;">
              <strong style="font-size: 12px;">Road: ${road_id} (${type})</strong><br/>
              <span style="font-size: 11px; color: ${status === 'closed' ? '#ef4444' : '#16a34a'}; font-weight: bold;">Status: ${status.toUpperCase()}</span>
              ${reason ? `<br/><span style="font-size: 10px; color: #475569;">Note: ${reason}</span>` : ''}
            </div>
          `).addTo(map.current);
        });

        map.current.on('mouseleave', 'roads-layer', () => {
          map.current.getCanvas().style.cursor = '';
          popupRef.current.remove();
        });

      } catch (err) {
        console.error('Initialization error:', err);
      }
    };

    if (map.current.loaded()) {
      initMap();
    } else {
      map.current.on('load', initMap);
    }
  }, []);

  useEffect(() => {
    if (routeData) {
      calculateRoute();
    }
  }, [selectedProfile]);

  const toggleRoadOverride = async (roadId, currentStatus) => {
    const newStatus = currentStatus === 'closed' ? 'open' : 'closed';
    try {
      const res = await fetch('http://localhost:8000/api/overrides/toggle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ road_id: roadId, status: newStatus, reason: 'Campaign World-State Toggle' })
      });
      const data = await res.json();
      setOverrides(data.active_overrides);

      const roadsRes = await fetch('http://localhost:8000/api/roads');
      const roadsGeoJson = await roadsRes.json();
      
      setRoads(roadsGeoJson.features);
      if (map.current.getSource('roads-source')) {
        const transformedRoadsGeoJson = {
          ...roadsGeoJson,
          features: roadsGeoJson.features.map(feature => ({
            ...feature,
            geometry: {
              ...feature.geometry,
              coordinates: feature.geometry.coordinates.map(coord => pixelToIdentity(coord[0], coord[1]))
            }
          }))
        };
        map.current.getSource('roads-source').setData(transformedRoadsGeoJson);
      }

      if (routeData) {
        calculateRoute();
      }
    } catch (err) {
      console.error('Failed to toggle override:', err);
    }
  };

  const toggleStop = (nodeId) => {
    if (selectedStops.includes(nodeId)) {
      setSelectedStops(selectedStops.filter(id => id !== nodeId));
    } else {
      setSelectedStops([...selectedStops, nodeId]);
    }
  };

  const calculateRoute = async () => {
    setLoading(true);
    setErrorMessage('');
    try {
      const response = await fetch('http://localhost:8000/api/optimize-route', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          origin: selectedOrigin,
          stops: selectedStops,
          profile: selectedProfile
        })
      });
      
      const result = await response.json();
      if (!response.ok) {
        throw new Error(result.detail || 'Route calculation failed');
      }

      setRouteData(result);

      const transformedRouteGeoJson = {
        ...result.geojson,
        geometry: {
          ...result.geojson.geometry,
          coordinates: result.geojson.geometry.coordinates.map(coord => pixelToIdentity(coord[0], coord[1]))
        }
      };

      if (map.current.getSource('route-source')) {
        map.current.getSource('route-source').setData(transformedRouteGeoJson);
        map.current.setPaintProperty('route-layer', 'line-color', result.color);
        map.current.setPaintProperty('route-layer', 'line-dasharray', result.dasharray);
      } else {
        map.current.addSource('route-source', {
          type: 'geojson',
          data: transformedRouteGeoJson
        });

        map.current.addLayer({
          id: 'route-layer',
          type: 'line',
          source: 'route-source',
          layout: { 'line-join': 'round', 'line-cap': 'round' },
          paint: {
            'line-color': result.color,
            'line-width': 5,
            'line-dasharray': result.dasharray
          }
        });
      }
    } catch (err) {
      setErrorMessage(err.message);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const exportHandout = async (actionType) => {
    if (!routeData) return;
    try {
      const res = await fetch('http://localhost:8000/api/export-handout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          origin: selectedOrigin,
          stops: selectedStops,
          profile: selectedProfile,
          route_result: routeData
        })
      });
      const data = await res.json();
      
      if (actionType === 'copy') {
        await navigator.clipboard.writeText(data.markdown);
        setCopyStatus(true);
        setTimeout(() => setCopyStatus(false), 2500);
      } else if (actionType === 'download') {
        const blob = new Blob([data.markdown], { type: 'text/markdown' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `t4-campaign-handout-${selectedProfile}.md`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      }
    } catch (err) {
      console.error('Failed to export handout:', err);
    }
  };

  return (
    <div style={{ display: 'flex', height: '100vh', width: '100vw', margin: 0, padding: 0, overflow: 'hidden' }}>
      <div style={{ width: '400px', padding: '20px', background: '#1e293b', color: '#f8fafc', overflowY: 'auto', boxSizing: 'border-box' }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 'bold', marginBottom: '1rem', marginTop: 0 }}>T⁴ Spatial Logistics</h2>
        
        <div style={{ marginBottom: '1rem' }}>
          <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.5rem' }}>Origin Settlement</label>
          <select 
            value={selectedOrigin} 
            onChange={(e) => setSelectedOrigin(e.target.value)}
            style={{ width: '100%', padding: '8px', borderRadius: '4px', background: '#334155', color: '#fff', border: '1px solid #475569', boxSizing: 'border-box' }}
          >
            {nodes.map(n => (
              <option key={n.id} value={n.id}>{n.name}</option>
            ))}
          </select>
        </div>

        <div style={{ marginBottom: '1rem' }}>
          <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.5rem' }}>Travel Profile (Rules & Verbiage)</label>
          <select 
            value={selectedProfile} 
            onChange={(e) => setSelectedProfile(e.target.value)}
            style={{ width: '100%', padding: '8px', borderRadius: '4px', background: '#334155', color: '#fff', border: '1px solid #475569', boxSizing: 'border-box' }}
          >
            {profiles.map(p => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </select>
        </div>

        <div style={{ marginBottom: '1.2rem' }}>
          <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.5rem' }}>Trade Loop Stops</label>
          <div style={{ background: '#334155', padding: '10px', borderRadius: '4px', border: '1px solid #475569' }}>
            {nodes.map(n => (
              <div key={n.id} style={{ display: 'flex', alignItems: 'center', marginBottom: '6px' }}>
                <input 
                  type="checkbox" 
                  id={`stop-${n.id}`}
                  checked={selectedStops.includes(n.id)}
                  onChange={() => toggleStop(n.id)}
                  style={{ marginRight: '8px', cursor: 'pointer' }}
                />
                <label htmlFor={`stop-${n.id}`} style={{ fontSize: '0.875rem', cursor: 'pointer' }}>{n.name}</label>
              </div>
            ))}
          </div>
        </div>

        <div style={{ marginBottom: '1.5rem' }}>
          <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.5rem', fontWeight: 'bold', color: '#fca5a5' }}>Campaign World-State Overrides</label>
          <div style={{ background: '#334155', padding: '10px', borderRadius: '4px', border: '1px solid #475569' }}>
            <p style={{ fontSize: '0.75rem', color: '#94a3b8', margin: '0 0 8px 0' }}>Toggle road conditions & simulated hazards:</p>
            {roads.map(r => {
              const roadId = r.properties.road_id;
              const status = r.properties.status;
              const isClosed = status === 'closed';
              return (
                <div key={roadId} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px', fontSize: '0.85rem' }}>
                  <span>Road <strong>{roadId}</strong> ({r.properties.type})</span>
                  <button 
                    onClick={() => toggleRoadOverride(roadId, status)}
                    style={{
                      background: isClosed ? '#ef4444' : '#10b981',
                      color: '#fff',
                      border: 'none',
                      borderRadius: '4px',
                      padding: '3px 8px',
                      fontSize: '0.75rem',
                      fontWeight: 'bold',
                      cursor: 'pointer'
                    }}
                  >
                    {isClosed ? 'CLOSED' : 'OPEN'}
                  </button>
                </div>
              );
            })}
          </div>
        </div>

        <button 
          onClick={calculateRoute}
          disabled={loading || selectedStops.length === 0}
          style={{ width: '100%', padding: '10px', background: '#e11d48', color: '#fff', border: 'none', borderRadius: '4px', fontWeight: 'bold', cursor: 'pointer', opacity: selectedStops.length === 0 ? 0.6 : 1 }}
        >
          {loading ? 'Computing Route...' : 'Calculate Trade Loop'}
        </button>

        {errorMessage && (
          <div style={{ marginTop: '1.0rem', background: '#7f1d1d', color: '#fca5a5', padding: '10px', borderRadius: '6px', fontSize: '0.85rem' }}>
            <strong>Error:</strong> {errorMessage}
          </div>
        )}

        {routeData && (
          <div style={{ marginTop: '1.5rem', background: '#334155', padding: '12px', borderRadius: '6px' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: '600', marginBottom: '0.5rem', marginTop: 0 }}>Itinerary Summary</h3>
            {routeData.notice && (
              <div style={{ background: '#78350f', color: '#fde68a', padding: '8px', borderRadius: '4px', fontSize: '0.75rem', marginBottom: '8px' }}>
                <strong>🔄 Re-routed:</strong> {routeData.notice}
              </div>
            )}
            <p style={{ fontSize: '0.875rem', margin: '4px 0' }}><strong>Path:</strong> {routeData.itinerary.join(' ➔ ')}</p>
            <p style={{ fontSize: '0.875rem', margin: '4px 0' }}><strong>Distance:</strong> {routeData.total_distance} {routeData.dist_unit}</p>
            <p style={{ fontSize: '0.875rem', margin: '4px 0' }}><strong>Est. Travel:</strong> {routeData.estimated_travel_time} {routeData.time_unit}</p>

            <div style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
              <button 
                onClick={() => exportHandout('copy')}
                style={{ flex: 1, padding: '6px', background: '#475569', color: '#fff', border: 'none', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 'bold', cursor: 'pointer' }}
              >
                {copyStatus ? 'Copied Handout!' : '📋 Copy Handout'}
              </button>
              <button 
                onClick={() => exportHandout('download')}
                style={{ flex: 1, padding: '6px', background: '#0284c7', color: '#fff', border: 'none', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 'bold', cursor: 'pointer' }}
              >
                📥 Download .md
              </button>
            </div>
          </div>
        )}
      </div>
      
      <div ref={mapContainer} style={{ flex: 1, height: '100%', position: 'relative' }} />
    </div>
  );
}