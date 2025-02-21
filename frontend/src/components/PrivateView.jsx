
import {connect} from 'react-redux'
import ExternalRedirect from './ExternalRedirect'


const mapStateToProps = (state) => ({
  user:state.user.profile,
  token:state.user.token,
  loading:state.user.loading,
  authenticating:state.user.authenticating
})

export default connect(mapStateToProps, null)(({ user, token, authenticating, loading, view:MainView, backup:BackupView, ...props}) => {
  // Show backup view if loading or not logged in
  if(!user && (loading||authenticating)){
    return BackupView? <BackupView {...props}/>:<></>
  } if (user===null||token===null){
    return BackupView? <BackupView {...props}/>:<ExternalRedirect to="/accounts/login"/>
  } 
    return <MainView {...props}/>
  
})
