import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export const injectAttack       = (device_id, attack_type) => api.post('/demo/inject-attack', { device_id, attack_type })
export const getDevices     = ()     => api.get('/devices/')
export const getIncidents   = (p={}) => api.get('/incidents/', { params: p })
export const getIncidentSummary = () => api.get('/incidents/summary')
export const getTelemetryStats  = () => api.get('/telemetry/stats')
export const getLatestTelemetry = () => api.get('/telemetry/latest')
export const resolveIncident    = (id) => api.patch(`/incidents/${id}/resolve`)
export const isolateDevice      = (id) => api.post(`/devices/${id}/isolate`)
export const restoreDevice      = (id) => api.post(`/devices/${id}/restore`)
export const getNistReport      = (id) => api.get(`/reports/${id}/nist`)
export const getCreditBrief     = (id) => api.get(`/reports/${id}/credit-brief`)

export default api
