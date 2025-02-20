import axios from 'axios';
import SecureLS from 'secure-ls'
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';

const tokens = {
  refreshToken: null,
};
const USER_PROFILE_KEY = 'userProfile';
const LOCAL_ADMIN_DATA_KEY = 'localAdminData';

export const getUserProfile = createAsyncThunk(
  'user/getUserProfile',
  (thunkAPI) => {
    return axios.get(`/api/user/profile/`).then((resp) => {
      localStorage.setItem(USER_PROFILE_KEY, JSON.stringify(resp.data));
      return {
        profile: resp.data,
      };
    });
  },
);

export const getTokens = createAsyncThunk('user/getTokens', (thunkAPI) => {
  return axios.get(`/api/user/jwt-token/`).then((resp) => {
    // keep a copy for axios to use
    tokens.refreshToken = resp.data.refresh;
    tokens.token = resp.data.access;
    // update axios config
    const authHeader = tokens.token ? `JWT ${tokens.token}` : '';
    axios.defaults.headers.common.Authorization = authHeader;
    return {
      token: resp.data.access,
      refreshToken: resp.data.refresh,
    };
  });
});

export const configureTokenRefresh = (setTokens, logout) => {
  axios.interceptors.response.use(
    (r) => r,
    (error) => {
      const originalRequest = error.config;
      if (error.response && error.response.status === 401) {
        if (
          error.response.data &&
          error.response.data.code === 'token_not_valid' &&
          originalRequest.url !== '/api/user/token/refresh/' &&
          originalRequest.url !== '/api/user/web-logout/' &&
          !originalRequest.headers.Retry &&
          tokens.refreshToken != null
        ) {
          originalRequest.Retry = true
          return axios
            .post('/api/user/token/refresh/', {
              refresh: tokens.refreshToken,
            })
            .then((resp) => {
              const newTokens = {
                token: resp.data.access,
                refreshToken: resp.data.refresh,
              }
              setTokens(newTokens)
              return newTokens
            })
            .then((newTokens) => {
              originalRequest.headers.Authorization = `JWT ${newTokens.token}`
              originalRequest.headers.Retry = 'true'
              return axios(originalRequest)
            })
        } 
          // if refresh failed then logout
          if(originalRequest.url !== '/api/user/web-logout/'){
            logout && logout()
          }
          return Promise.reject(error)
        
      }
      return Promise.reject(error)
    },
  );
};

export const getAchievements = createAsyncThunk(
  'user/getAchievements',
  (thunkAPI) => {
    return axios.get(`/api/achievements/`).then((resp) => {
      return {
        achievements:resp.data
      }
    }).catch((e) => {
      console.log(e)
    })
  },
)

const slice = createSlice({
  name: 'user',
  initialState: {
    token: null,
    refreshToken: null,
    authenticating: true,
    loading: true,
    profile: JSON.parse(localStorage.getItem(USER_PROFILE_KEY)),
    achievements: null,
    superhostOpenUrls: [],
  },
  reducers: {
    setSuperhostOpenUrls(state, action){
       
      state.superhostOpenUrls = action.payload
    },
    setAchievements(state, action){
       
      state.achievements = state.achievements?{
        ...state.achievements,
        ...action.payload
      } :{
        ...action.payload
      }
    },
    setTokens(state, action) {
       
      state.token = action.payload.token;
       
      state.refreshToken = action.payload.refreshToken;
      // update local copy
      tokens.token = state.token;
      tokens.refreshToken = state.refreshToken;
      // update axios config
      const authHeader = state.token ? `Bearer ${state.token}` : '';
      axios.defaults.headers.common.Authorization = authHeader;
    },
    logout(state) {
      axios.post('/api/user/web-logout/').then(() => {
        // ignore
         
        location.href="/accounts/login/"
      })
       
      state.token = null;
       
      state.refreshToken = null;
       
      state.profile = null;
      tokens.token = null;
      tokens.refreshToken = null;
       
      state.achievements = null
      axios.defaults.headers.common.Authorization = '';
      localStorage.removeItem(USER_PROFILE_KEY);
      // clear all blueprint caches
      const ls = new SecureLS()
      ls.removeAll()
    },
    login(state) {
      window.location.href="/accounts/login/"
    },
    signup(state) {
      window.location.href="/accounts/signup/" 
    },
  },
  extraReducers: {
    // Add reducers for additional action types here, and handle loading state as needed
    [getTokens.pending]: (state, action) => ({
      ...state,
      authenticating: true,
    }),
    [getTokens.rejected]: (state, action) => ({
      ...state,
      authenticating: false,
    }),
    [getTokens.fulfilled]: (state, action) => ({
      ...state,
      token: action.payload.token,
      refreshToken: action.payload.refreshToken,
      authenticating: false,
    }),
    [getUserProfile.pending]: (state, action) => ({
      ...state,
      loading: true,
    }),
    [getUserProfile.fulfilled]: (state, action) => ({
      ...state,
      profile: action.payload.profile,
      loading: false,
    }),
    [getUserProfile.rejected]: (state, action) => ({
      ...state,
      loading: false,
    }),
    [getAchievements.pending]: (state, action) => ({
      ...state,
      achievementsLoading: true,
    }),
    [getAchievements.fulfilled]: (state, action) => ({
      ...state,
      ...action.payload,
      achievementsLoading: false,
    }),
    [getAchievements.rejected]: (state, action) => {
      return {
        ...state,
        achievementsLoading: false,
      }
    },
  },
});

export const { setSuperhostOpenUrls, setAchievements, setTokens, logout, login, signup } = slice.actions;
export default slice.reducer;
