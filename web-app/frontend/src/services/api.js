import axios from 'axios';

// When running with CRA proxy (package.json → "proxy"), relative paths work.
// In production you can set REACT_APP_API_BASE.
const BASE = process.env.REACT_APP_API_BASE || '/api';

const http = axios.create({
  baseURL: BASE,
  withCredentials: true,          // send session cookie
  headers: { 'Content-Type': 'application/json' },
});

// ---- Documents ----

export const getDocuments = () => http.get('/documents');

export const uploadDocuments = (documents) =>
  http.post('/upload', { documents });

export const loadSampleDocuments = () => http.post('/upload/samples');

export const resetSession = () => http.post('/reset');

// ---- Search ----

export const searchKeyword = (keyword, mode) =>
  http.post('/search', { keyword, mode });

export const compareKeyword = (keyword) =>
  http.post('/compare', { keyword });

// ---- Analysis / History ----

export const getAnalysis = () => http.get('/analysis');

export const getHistory = () => http.get('/history');
