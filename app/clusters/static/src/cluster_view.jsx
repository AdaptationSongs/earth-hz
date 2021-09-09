import React from 'react';
import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import Card from 'react-bootstrap/Card';
import Button from 'react-bootstrap/Button';
import Collapse from 'react-bootstrap/Collapse';
import Form from 'react-bootstrap/Form';
import {LabelWidget, AddLabelForm} from '../../../labels/static/src/labels.jsx'


class ClipContainer extends React.Component {
  constructor(props) {
    super(props);
  }

  handleCheckToggle(e) {
    this.props.onCheckToggle(this.props.number, e.target.checked);
  }

  handleAddLabel(label) {
    this.props.onAdd(label, this.props.number);
  }

  render() {
    const clip = this.props.clip
    return (
      <Card body className={"mt-3 mb-3" + (this.props.selected ? " border-primary" : "")}>
        <Row>
          <Col md={1}>
            <Form.Check className="h-100 pb-5">
              <Form.Check.Input className="h-100" onChange={this.handleCheckToggle.bind(this)} checked={this.props.selected} />
            </Form.Check>
          </Col>
          <Col md={5}>
            <Button variant="primary" onClick={() => playClip(clip.file_name, clip.offset)}>
              Play clip
            </Button>
            <Card.Text>Time: {clip.window_start}</Card.Text>
            <Card.Text>Monitoring station: {clip.file.recording_device.station.name}</Card.Text>
            <Card.Text>Manual ID: {clip.label}</Card.Text>
            <LabelWidget
              file_name={clip.file_name}
              offset={clip.offset}
              project_id={this.props.project_id}
              duration={this.props.duration}
              labels={this.props.labels}
              onAdd={this.handleAddLabel.bind(this)}
            />
            <a href={"/labels/clip/"+clip.file_name+"/"+clip.offset}>View/Edit Clip Labels</a>
          </Col>
          <Col md={6}>
            <Card.Img variant="top" src={"/spectrogram/"+clip.file_name+"-"+clip.offset+".png"} />
          </Col>
        </Row>
      </Card>
    );
  }

}


export class ClusteredClips extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      open: false,
      selected: this.props.clips.map((clip) => false),
      labels: this.props.clips.map((clip) => [])
    };
  }

  componentDidMount() {
    this.props.clips.forEach((clip, index) => {
      fetch('/labels/_get_clip_labels/' + clip.file_name
        + '?offset=' + clip.offset + '&duration=' + this.props.duration)
        .then((response) => {
          return response.json();
        })
        .then((data) => {
          let labels = [...this.state.labels];
          labels[index] = data;
          this.setState({labels: labels});
        }).catch((error) => {
          console.log(error);
        });
    });
  }

  expand() {
    this.setState({open: true});
  }

  collapse() {
    this.setState({open: false});
  }

  toggleSelectAll(e) {
    this.setState({selected: this.props.clips.map((clip) => e.target.checked)});
  }

  toggleSelectOne(key, value) {
    let items = [...this.state.selected];
    items[key] = value;
    this.setState({selected: items});
  }

  labelAdded(label, index) {
    let labels = [...this.state.labels];
    labels[index] = [...labels[index], label];
    this.setState({labels: labels});
  }

  bulkLabelAdded(label) {
    this.state.selected.forEach((selected, index) => {
      if (selected) {
        let labels = [...this.state.labels];
        labels[index] = [...labels[index], label];
        this.setState({labels: labels});
      }
    });
  }

  render() {
    const { open, labels } = this.state;
    let selected_clips = [];
    this.state.selected.forEach((selected, index) => {
      if (selected) {
        let clip = {
          file_name: this.props.clips[index].file_name,
          offset: this.props.clips[index].offset,
          duration: this.props.duration
        }
        selected_clips.push(clip);
      }
    });
    return (
      <Form>
        <Form.Check inline id="select-all" label="Select all" onChange={this.toggleSelectAll.bind(this)} />
        <Button variant='primary'
          className={open ? 'd-none' : null}
          onClick={this.expand.bind(this)}
        >
          + Bulk Label
        </Button>
        <Collapse mountOnEnter={true} in={open}>
          <div>
            <AddLabelForm
              project_id={this.props.project_id}
              clips={selected_clips}
              onClose={this.collapse.bind(this)}
              onAdd={this.bulkLabelAdded.bind(this)}
            />
          </div>
        </Collapse>
        {this.props.clips.map((clip, index) =>
          <ClipContainer
            key={index}
            number={index}
            selected={this.state.selected[index]}
            onCheckToggle={this.toggleSelectOne.bind(this)}
            onAdd={this.labelAdded.bind(this)}
            clip={clip}
            project_id={this.props.project_id}
            duration={this.props.duration}
            labels={labels[index]}
          />
        )}
      </Form>
    );
  }

}

