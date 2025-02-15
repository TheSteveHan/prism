import React from 'react'
import { NavLink } from "react-router";



export default () => {
  return <div style={{
    height:10, display:"flex", gap:12, justifyContent:"flex-end", marginRight:16, 
    position: "fixed", right:0, top:0
  }}>
    <NavLink to="/ops/submit" target="_blank">Submit</NavLink>
    <NavLink to="/ops/Review">Review</NavLink>
    <NavLink to="/ops/dashboard">Dashboard</NavLink>
  </div>
}

