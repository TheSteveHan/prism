import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import { BrowserRouter, Routes, Route } from "react-router";

//import App from './Clustering.jsx'
//import App from './App.jsx'
import Feed from './Feed.jsx'
import Submission from './Submission.jsx'
import Review from './Review.jsx'

createRoot(document.getElementById('root')).render(
  <BrowserRouter>
    <Routes>
      <Route path="/" element={<Feed />} />
      <Route path="/submit" element={<Submission />} />
      <Route path="/review" element={<Review />} />
    </Routes>
  </BrowserRouter>,
)
