import React from 'react'
import { connect } from 'react-redux'
import { NavLink } from "react-router";
import AuthBasedView from 'components/AuthBasedView'
import { logout, login } from '../redux/slices/user'
import 'components/Nav.css'



export default connect(state=>({user:state.user.profile}),{logout, login})(({user, login, logout}) => {
  return <div className="nav-container" style={{
    height:10, display:"flex", gap:12, justifyContent:"flex-end", marginRight:16, 
    position: "fixed", right:0, top:0
  }}>
    <AuthBasedView whenLoggedIn >
      <NavLink to="/ops/submit" target="_blank">Submit</NavLink>
      {(user.is_staff||user.is_superuser) && <>
      <NavLink to="/ops/Review">Review</NavLink>
      <NavLink to="/ops/dashboard">Dashboard</NavLink>
    </>
      }
      <NavLink to="" onClick={logout}>Log Out</NavLink>
    </AuthBasedView>
    <AuthBasedView whenLoggedOut >
      <NavLink to="" onClick={login}>Log In</NavLink>
    </AuthBasedView>
  </div>
})

