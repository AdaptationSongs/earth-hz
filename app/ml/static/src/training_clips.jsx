import React from 'react';
import Form from 'react-bootstrap/Form';


export class UseClip extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      use: false
    };
    this.url = '/ml/iteration/' + this.props.iteration_id + '/_use_clip/' + this.props.clip_id;
  }

  componentDidMount() {
    fetch(this.url)
      .then((response) => {
        return response.json();
      }).then((data) => {
        this.setState({use: data});
      }).catch((error) => {
        console.log(error);
      });
  }

  handleCheckToggle(e) {
    fetch(this.url, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(e.target.checked)
    }).then((response) => {
      return response.json();
    }).then ((data) => {
      this.setState({use: data});
    }).catch((error) => {
      console.log(error);
    });
  }

  render() {
    return (
      <Form.Check
        label="Use for training"
        id={'checkbox-' + this.props.clip_id}
        onChange={this.handleCheckToggle.bind(this)}
        checked={this.state.use}
        disabled={this.props.disabled}
      />
    );
  }

}
