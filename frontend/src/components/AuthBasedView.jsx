import {connect} from 'react-redux'


const mapStateToProps = (state) => ({
  user:state.user.profile,
  token:state.user.token,
  loading:state.user.loading,
  authenticating:state.user.authenticating
})

export default connect(mapStateToProps, null)(({ user, token, authenticating, loading, children, 
  whenLoading=false, whenLoggedIn=false, whenLoggedOut=false}) => {
  if(
    ((loading||authenticating) && whenLoading) || 
    ((user===null||token===null) && whenLoggedOut) || 
    ((user && token) && whenLoggedIn) 
  ){
      return <>{children}</>
  }
  return <></>
})
