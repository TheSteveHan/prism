import {configureStore} from '@reduxjs/toolkit'
import {combineReducers} from 'redux'
import {persistStore, persistReducer} from 'redux-persist'
import storage from 'redux-persist/lib/storage' // defaults to localStorage for web
import thunk from 'redux-thunk'
import user from './slices/user'

const middlewares = [thunk]

// Middleware: Redux Persist Config
const userPersistConfig = {
  // Root
  key: 'user',
  // Storage Method (React Native)
  storage,
  whitelist: ['token', 'refreshToken', 'profile', 'loading', 'preferredTheme', 'superhostOpenUrls'],
}

const reducer = combineReducers({
  user: persistReducer(userPersistConfig, user),
})

const store = configureStore({
  reducer,
  middleware: middlewares,
})

const persistor = persistStore(store)

export {store, persistor}
