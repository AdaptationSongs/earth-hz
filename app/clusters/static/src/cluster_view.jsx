import React from 'react';
import Card from 'react-bootstrap/Card';
import {BulkLabelContainer} from '../../../labels/static/src/labels.jsx'


class ClusteredClip extends React.Component {
  constructor(props) {
    super(props);
  }

  render() {
    const clip = this.props.clip
    return (
      <div>
        <Card.Text>Time: {clip.window_start}</Card.Text>
        <Card.Text>Monitoring station: {clip.file.recording_device.station.name}</Card.Text>
        <Card.Text>Manual ID: {clip.label}</Card.Text>
      </div>
    );
  }

}


export class ClusteredClips extends React.Component {
  constructor(props) {
    super(props);
  }

  render() {
    return (
      <BulkLabelContainer
        project_id={this.props.project_id}
        duration={this.props.duration}
        clips={this.props.clips}
        inner={ClusteredClip}
      />
    );
  }

}
