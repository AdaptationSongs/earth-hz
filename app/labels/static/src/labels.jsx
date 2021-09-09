import React from 'react';
import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import Card from 'react-bootstrap/Card';
import Button from 'react-bootstrap/Button';
import Collapse from 'react-bootstrap/Collapse';
import OverlayTrigger from 'react-bootstrap/OverlayTrigger';
import Popover from 'react-bootstrap/Popover';
import Form from 'react-bootstrap/Form';


function translate_label(label, lang) {
  const filtered_names = label.common_names.filter((row) => row.language.code == lang);
  if (filtered_names.length) {
    return ('(' + filtered_names[0].name + ')');
  }
}


class LabelList extends React.Component {
  constructor(props) {
    super(props);
  }

  render() {
    return (
      <ul>
        {this.props.labels.map((label) =>
          <li key={label.id}>
            <OverlayTrigger
              trigger={['hover', 'click']}
              placement="right"
              overlay={
                <Popover>
                  <Popover.Title as="h3">{label.label.name}</Popover.Title>
                  <Popover.Content>
                      <p>{label.label.type.name}</p>
                      <div>{label.label.common_names.length ? 'common name:' : ''}
                        <ul>
                          {label.label.common_names.map((cname) =>
                            <li key={cname.id}>{cname.name} ({cname.language.name})</li>
                          )}
                        </ul>
                      </div>
                      {label.sub_label
                        ? <p>{label.sub_label.type.name}: {label.sub_label.name}</p>
                        : ''
                      }
                      <p>certain: {label.certain ? 'Yes' : 'No'}</p>
                      <p>added: {label.modified}</p>
                      <p>by user: {label.user.name}</p>
                      <p>notes: {label.notes}</p>
                  </Popover.Content>
                </Popover>
              }
            >
              <Button variant="link">
                {label.label.name} {translate_label(label.label, 'en')} {label.sub_label ? label.sub_label.name : ''}
              </Button>
            </OverlayTrigger>
          </li>
        )}
      </ul>
    );
  }

}


export class AddLabelForm extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      all_types: [],
      all_labels: [],
      primary_types: [],
      primary_labels: [],
      sub_types: [],
      sub_labels: [],
      certain: 1,
      selected_type: null,
      selected_label: null,
      selected_sub_type: null,
      selected_sub_label: null,
      notes: null,
      error_code: '',
      error_message: ''
    };
  }

  componentDidMount() {
    let filtered_types = [];
    fetch('/labels/_get_label_types')
      .then((response) => {
        return response.json();
      })
      .then((data) => {
        filtered_types = data.filter((row) => row.parent_id == null);
        this.setState({
          all_types: data,
          primary_types: filtered_types,
        })
      })
      .then(fetch('/labels/_get_project_labels/' + this.props.project_id)
        .then((response) => {
          return response.json()
        })
        .then((data) => {
          this.setState({all_labels: data});
          this.handleTypeChange({target: {value: filtered_types[0].id}});
        })
      ).catch((error) => {
          console.log(error);
      });
  }

  handleCertaintyChange(e) {
    this.setState({certain: e.target.value});
  }

  handleTypeChange(e) {
    const type = e.target.value;
    const filtered_labels = this.state.all_labels.filter((row) => row.label.type.id == type);
    const filtered_types = this.state.all_types.filter((row) => row.parent_id == type);
    this.setState({
          selected_type: type,
          primary_labels: filtered_labels,
          selected_label: filtered_labels.length ? filtered_labels[0].label.id : '',
          sub_types: filtered_types,
    });
    if (filtered_types.length) {
      this.handleSubTypeChange({target: {value: filtered_types[0].id}});
    }
  }

  handleSubTypeChange(e) {
    const sub_type = e.target.value;
    const filtered_labels = this.state.all_labels.filter((row) => row.label.type.id == sub_type);
    this.setState({
      selected_sub_type: sub_type,
      sub_labels: filtered_labels
    });
  }

  handleLabelChange(e) {
    this.setState({selected_label: e.target.value});
  }

  handleSubLabelChange(e) {
    this.setState({selected_sub_label: e.target.value});
  }

  handleNotesChange(e) {
    this.setState({notes: e.target.value});
  }

  handleCancelClick(e) {
    this.setState({error_code: '', error_message: ''});
    this.props.onClose();
  }

  handleSubmit(e) {
    e.preventDefault();
    fetch('/labels/_add_clip_label', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        clips: this.props.clips,
        label: {
          certain: this.state.certain,
          label_id: this.state.selected_label,
          sub_label_id: this.state.selected_sub_label,
          notes: this.state.notes
        }
      })
    }).then((response) => {
      if (response.ok) {
        this.setState({error_code: '', error_message: ''});
        this.props.onClose();
      } else {
        this.setState({error_code: response.status});
      }
      return response.json();
    }).then ((data) => {
      if (this.state.error_code) {
        this.setState({error_message: data.message});
      } else {
        this.props.onAdd(data);
      }
    }).catch((error) => {
      console.log(error);
    });
  }

  render () {
    const { primary_types, primary_labels, sub_types, sub_labels, selected_type, selected_sub_type, selected_label, selected_sub_label, certain, notes, error_code, error_message } = this.state;
    let sub_label_select;
    if (sub_types.length) {
      sub_label_select =
        <Form.Group as={Row}>
          <Col>
            <Form.Control
              as="select"
              value={selected_sub_type}
              onChange={this.handleSubTypeChange.bind(this)}
            >
              {sub_types.map((type) =>
                <option key={type.id} value={type.id}>{type.name}</option>
              )}
            </Form.Control>
          </Col>
          <Col>
            <Form.Control
              as="select"
              value={selected_sub_label}
              onChange={this.handleSubLabelChange.bind(this)}
            >
              <option key="default" value=""></option>
              {sub_labels.map((label) =>
                <option key={label.label.id} value={label.label.id}>{label.label.name}</option>
              )}
            </Form.Control>
          </Col>
        </Form.Group>;
    }
    let error_text = '';
    if (error_code) {
      error_text += 'Error ' + error_code + ': ';
    }
    if (error_message) {
      error_text += error_message;
    }
    return (
      <Card>
        <Card.Body>
          <Card.Title>New Label</Card.Title>
          <Form onSubmit={this.handleSubmit.bind(this)}>
            <Form.Group as={Row}>
              <Form.Control
                as="select"
                value={certain}
                onChange={this.handleCertaintyChange.bind(this)}
              >
                <option value={1}>Definitely</option>
                <option value={0}>Maybe</option>
              </Form.Control>
            </Form.Group>
            <Form.Group as={Row}>
              <Col>
                <Form.Control
                  as="select"
                  value={selected_type}
                  onChange={this.handleTypeChange.bind(this)}
                >
                  {primary_types.map((type) =>
                    <option key={type.id} value={type.id}>{type.name}</option>
                  )}
                </Form.Control>
              </Col>
              <Col>
                <Form.Control
                  as="select"
                  value={selected_label}
                  onChange={this.handleLabelChange.bind(this)}
                >
                  {primary_labels.map((label) =>
                    <option key={label.label.id} value={label.label.id}>
                      {label.label.name} {translate_label(label.label, 'en')}
                    </option>
                  )}
                </Form.Control>
              </Col>
            </Form.Group>
            {sub_label_select}
            <Form.Group as={Row}>
              <Form.Label>Notes:</Form.Label>
              <Form.Control
                as="textarea"
                value={notes}
                onChange={this.handleNotesChange.bind(this)}
              />
            </Form.Group>
            <Row>
              <Col>
                <Button
                  variant="secondary"
                  onClick={this.handleCancelClick.bind(this)}
                >
                  Cancel
                </Button>
              </Col>
              <Col>
                <Button
                  variant="primary"
                  className="float-right"
                  onClick={this.handleSubmit.bind(this)}
                >
                  Save
                </Button>
              </Col>
            </Row>
          </Form>
          <div className="text-danger">{error_text}</div>
        </Card.Body>
      </Card>
    );
  }

}


export class LabelWidget extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      open: false
    };
  }

  expand() {
    this.setState({open: true});
  }

  collapse() {
    this.setState({open: false});
  }

  render() {
    const { open } = this.state;
    return (
      <div>
        <div>Manual labels:</div>
        <LabelList
          labels={this.props.labels}
        />
        <Button variant='primary'
          className={open ? 'd-none' : null}
          onClick={this.expand.bind(this)}
        >
          + Add Label
        </Button>
        <Collapse mountOnEnter={true} in={open}>
          <div>
            <AddLabelForm
              project_id={this.props.project_id}
              clips={[{file_name: this.props.file_name, offset: this.props.offset, duration: this.props.duration}]}
              onClose={this.collapse.bind(this)}
              onAdd={this.props.onAdd.bind(this)}
            />
          </div>
        </Collapse>
      </div>
    );
  }

}


export class LabelContainer extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      labels: []
    };
  }

  componentDidMount() {
    fetch('/labels/_get_clip_labels/' + this.props.file_name
      + '?offset=' + this.props.offset + '&duration=' + this.props.duration)
      .then((response) => {
        return response.json();
      })
      .then((data) => {
        this.setState({labels: data});
      }).catch((error) => {
        console.log(error);
      });
  }

  labelAdded(label) {
    this.setState(prevState => ({
      labels: [...prevState.labels, label]
    }));
  }

  render() {
    return (
      <div>
        <LabelWidget
          labels={this.state.labels}
          project_id={this.props.project_id}
          file_name={this.props.file_name}
          offset={this.props.offset}
          duration={this.props.duration}
          onAdd={this.labelAdded.bind(this)}
        />
      </div>
    );
  }

}
