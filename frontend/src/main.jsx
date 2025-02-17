import './auth'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import { BrowserRouter, Routes, Route } from "react-router";

//import App from './Clustering.jsx'
//import App from './App.jsx'
import Feed from './Feed.jsx'
import Submission from './Submission.jsx'
import Review from './Review.jsx'
import Dashboard from './Dashboard.jsx'

createRoot(document.getElementById('root')).render(
  <BrowserRouter>
    <Routes>
      <Route path="/" element={<Feed />} />
      <Route path="/ops/submit" element={<Submission />} />
      <Route path="/ops/review" element={<Review />} />
      <Route path="/ops/dashboard" element={<Dashboard/>} />
    </Routes>
  </BrowserRouter>,
)
