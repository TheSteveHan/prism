import { StrictMode, useEffect } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import { BrowserRouter, Routes, Route } from "react-router";
import { connect, Provider } from 'react-redux'
import { PersistGate } from 'redux-persist/integration/react'
import { store, persistor } from './redux/store'
import {
  getUserProfile,
  getTokens,
  setTokens,
  configureTokenRefresh,
  logout,
} from './redux/slices/user'

//import App from './Clustering.jsx'
//import App from './App.jsx'
import Feed from './Feed.jsx'
import Submission from './Submission.jsx'
import Review from './Review.jsx'
import Dashboard from './Dashboard.jsx'
import Nav from 'components/Nav'

const mapDispatch = { getTokens, getUserProfile, setTokens, logout }

const AppContent = connect(
  state => ({ preferredTheme: state.user?.profile?.theme }),
  mapDispatch,
)(({
    getTokens,
    getUserProfile,
    setTokens,
    logout,
    preferredTheme,
    extraAppRoutes,
}) => {
  useEffect(() => {
    // get a new set of tokens and set up auto refresh
    // fetch usr profile
    getUserProfile()
    getTokens().finally(() => {
      configureTokenRefresh(setTokens, logout)
    })
  }, [getTokens, setTokens, logout, getUserProfile])

  return <>
  <BrowserRouter>
    <Nav/>
    <Routes>
      <Route path="/" element={<Feed />} />
      <Route path="/ops/submit" element={<Submission />} />
      <Route path="/ops/review" element={<Review />} />
      <Route path="/ops/dashboard" element={<Dashboard/>} />
    </Routes>
  </BrowserRouter> 
</>
})
createRoot(document.getElementById('root')).render(
  <Provider store={store}>
    <PersistGate loading={null} persistor={persistor}>
      <AppContent/>
    </PersistGate>
  </Provider>
  ,
)
