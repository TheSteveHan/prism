import {Component} from 'react'

export default class ExternalRedirect extends Component {
  componentDidMount() {
    const { to, from } = this.props
    window.location.href = `${to}?next=${from||window.location.pathname}`
  }

  render() {
    return <></>
  }
}
