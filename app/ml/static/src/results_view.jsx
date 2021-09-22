import React from 'react';
import Card from 'react-bootstrap/Card';
import {BulkLabelContainer, translate_label} from '../../../labels/static/src/labels.jsx'


class ResultsClip extends React.Component {
  constructor(props) {
    super(props);
  }

  render() {
    const clip = this.props.clip
    return (
      <div>
        <Card.Text>Time: {clip.window_start}</Card.Text>
        <Card.Text>Monitoring station: {clip.file.recording_device.station.name}</Card.Text>
        <Card.Text>Predicted label: {clip.label.name} {translate_label(clip.label, 'en')}</Card.Text>
        <Card.Text>Probability: {clip.probability}</Card.Text>
      </div>
    );
  }

}


export class ResultsClips extends React.Component {
  constructor(props) {
    super(props);
  }

  render() {
    return (
      <BulkLabelContainer
        project_id={this.props.project_id}
        duration={this.props.duration}
        clips={this.props.clips}
        inner={ResultsClip}
      />
    );
  }

}
