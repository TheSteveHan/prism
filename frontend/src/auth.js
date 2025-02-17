import axios from 'axios'

let USER_TOKEN = localStorage.getItem('user-token')
if(!USER_TOKEN){
  axios.post("/api/auth/stateless-user").then(({data:{token}})=>{
    localStorage.setItem('user-token', token)
    USER_TOKEN = token
    axios.defaults.headers.common['Authorization'] = `JWT ${USER_TOKEN}`;
  })
} else {
  axios.defaults.headers.common['Authorization'] = `JWT ${USER_TOKEN}`;
}
