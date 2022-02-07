import React from 'react';
import Form from 'react-bootstrap/Form';
import Button from 'react-bootstrap/Button';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import Card from 'react-bootstrap/Card';
import Table from 'react-bootstrap/Table';
import Spinner from 'react-bootstrap/Spinner';
import Modal from 'react-bootstrap/Modal';
import {AutoCompleteLabel} from '../../../labels/static/src/labels.jsx'


export class AddProjectLabelForm extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      types: [],
      all_labels: [],
      labels: [],
      primary_types: [],
      selected_type: '',
      selected_label: '',
      label_input: '',
      loading: true,
    };
  }

  componentDidMount() {
    let filtered_types = [];
    let sub = this.props.sub || 0;
    fetch('/labels/_get_label_types')
      .then((response) => {
        return response.json();
      })
      .then((data) => {
        if (sub) {
          filtered_types = data.filter((row) => row.parent_id != null);
        } else {
          filtered_types = data.filter((row) => row.parent_id == null);
        }
        this.setState({
          types: filtered_types,
        });
      })
      .then(fetch('/labels/_get_all?sub=' + sub)
        .then((response) => {
          return response.json()
        })
        .then((data) => {
          this.setState({
            all_labels: data,
            loading: false,
          });
          this.handleTypeChange({target: {value: filtered_types[0].id}});
        })
      ).catch((error) => {
          console.log(error);
      });
  }

  handleSubmit(e) {
    e.preventDefault();
    fetch('/projects/_add_project_label', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        project_id: this.props.project_id,
        label_id: this.state.selected_label,
      })
    }).then((response) => {
      if (response.ok) {
        this.setState({error_code: '', error_message: ''});
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

  handleTypeChange(e) {
    const type = e.target.value;
    const filtered_labels = this.state.all_labels.filter((row) => row.type.id == type);
    this.setState({
          selected_type: type,
          labels: filtered_labels,
          selected_label: '',
          label_input: '',
    });
  }

  handleLabelInput(value) {
    this.setState({label_input: value});
  }

  handleLabelSelect(id) {
    this.setState({selected_label: id});
  }

  render() {
    const { types, labels, selected_type, selected_label, label_input, loading, error_code, error_message } = this.state;
    let error_text = '';
    if (error_code) {
      error_text += 'Error ' + error_code + ': ';
    }
    if (error_message) {
      error_text += error_message;
    }
    return (
      <Form onSubmit={this.handleSubmit}>
        <Form.Group as={Row}>
          <Col md="auto">
            <Form.Control
              as="select"
              value={selected_type}
              onChange={this.handleTypeChange.bind(this)}
            >
              {types.map((type) =>
                <option key={type.id} value={type.id}>{type.name}</option>
              )}
            </Form.Control>
          </Col>
          <Col md="auto">
            { loading
              ? <Spinner as="span" animation="border" />
              : <AutoCompleteLabel
                  labels={labels}
                  value={label_input}
                  onInput={this.handleLabelInput.bind(this)}
                  onSelect={this.handleLabelSelect.bind(this)}
                />
            }
          </Col>
          <Col md="auto">
            <Button
              variant="primary"
              disabled={!(selected_label)}
              onClick={this.handleSubmit.bind(this)}
            >
              Add
            </Button>
          </Col>
        </Form.Group>
        <div className="text-danger">{error_text}</div>
      </Form>
    );

  }

}


class DeleteConfirmation extends React.Component {
  render() {
    const selected = this.props.project_label;
    return (
      <Modal
        centered
        show={selected ? true : false}
        onHide={this.props.onClose.bind(this)}
      >
        <Modal.Header closeButton>
          <Modal.Title>Remove project label?</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <p>Are you sure you want to remove <em>{selected ? selected.label.name : ''}</em> from the list of available labels for your project?</p>
          <p>This will not affect any labeled clips, and you can re-add this label at any time.</p>
        </Modal.Body>
        <Modal.Footer>
          <Button
            variant="secondary"
            onClick={this.props.onClose.bind(this)}
          >
            Cancel
          </Button>
          <Button
            variant="danger"
            value={selected ? selected.id : ''}
            onClick={this.props.onConfirm.bind(this)}
          >
            Remove
          </Button>
        </Modal.Footer>
      </Modal>
    );
  }
}


export class ProjectLabels extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      labels: this.props.labels,
      selected_label: '',
    };
  }

  handleAdd(new_label) {
    this.setState(prevState => ({
      labels: [new_label, ...prevState.labels]
    }));
  }

  showConfirmation(e) {
    this.setState({selected_label: JSON.parse(e.target.value)});
  }

  hideConfirmation(e) {
    this.setState({selected_label: ''});
  }

  handleRemove(e) {
    fetch('/projects/_delete_project_label', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        id: e.target.value,
      })
    }).then((response) => {
      if (response.ok) {
        this.setState(prevState => ({
          labels: prevState.labels.filter((row) => row.id != e.target.value),
          selected_label: '',
        }));
      }
    }).catch((error) => {
      console.log(error);
    });
  }

  render () {
    return (
      <div>
        <Card>
          <Card.Body>
            <Card.Title>Add Label</Card.Title>
            <AddProjectLabelForm
              project_id={this.props.project_id}
              sub={this.props.sub}
              onAdd={this.handleAdd.bind(this)}
            />
          </Card.Body>
        </Card>
        <Table>
          <thead>
            <tr>
              <th>Label</th>
              <th>Common names</th>
              <th>Clips</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {this.state.labels.map((label) =>
              <tr key={label.id}>
                <td><a href={"/labels/project/"+this.props.project_id+"?select_label="+label.label_id}>{label.label.name}</a></td>
                <td>
                  <ul>
                    {label.label.common_names.map((cname) =>
                      <li key={cname.id}>{cname.name} ({cname.language.name})</li>
                    )}
                  </ul>
                </td>
                <td>{label.clip_count}</td>
                <td>
                  <Button
                    variant="danger"
                    value={JSON.stringify(label)}
                    onClick={this.showConfirmation.bind(this)}
                  >Remove</Button>
                </td>
              </tr>
            )}
          </tbody>
        </Table>
        <DeleteConfirmation
          project_label={this.state.selected_label}
          onClose={this.hideConfirmation.bind(this)}
          onConfirm={this.handleRemove.bind(this)}
        />
      </div>
    );
  }
}
