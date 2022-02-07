import React from 'react';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import Card from 'react-bootstrap/Card';
import Button from 'react-bootstrap/Button';
import Collapse from 'react-bootstrap/Collapse';
import OverlayTrigger from 'react-bootstrap/OverlayTrigger';
import Popover from 'react-bootstrap/Popover';
import Tooltip from 'react-bootstrap/Tooltip';
import Form from 'react-bootstrap/Form';
import InputGroup from 'react-bootstrap/InputGroup';
import ReactAutocomplete from 'react-autocomplete';


export function translate_label(label) {
  // todo: get current language from browser
  const lang = 'en'
  const filtered_names = label.common_names.filter((row) => row.language.code == lang);
  if (filtered_names.length) {
    return (filtered_names[0].name);
  } else {
    return '';
  }
}


export function format_common_name(label) {
  const common_name = translate_label(label);
  if (common_name) {
    return ('(' + common_name + ')');
  } else {
    return '';
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
                {label.label.name} {format_common_name(label.label)} {label.sub_label ? label.sub_label.name : ''}
              </Button>
            </OverlayTrigger>
          </li>
        )}
      </ul>
    );
  }

}


export class AutoCompleteLabel extends React.Component {
  constructor(props) {
    super();
  }

  shouldItemRender(item, value) {
    return (
      (item.name.toLowerCase().indexOf(value.toLowerCase()) > -1) ||
      (translate_label(item).toLowerCase().indexOf(value.toLowerCase()) > -1)
    );
  }

  getSuggestionValue(item) {
    return (translate_label(item) || item.name);
  }

  renderSuggestion(item, isHighlighted) {
    return (
      <div
        key={item.id}
        style={{ background: isHighlighted ? 'lightgray' : 'white' }}
        className='mb-1'
      >
        {item.name} {format_common_name(item)}
      </div>
    );
  }

  handleInput(e) {
    this.props.onInput(e.target.value);
    // unset selected label while typing
    this.props.onSelect('');
  };

  handleSelection(value, item) {
    this.props.onInput(value);
    this.props.onSelect(item.id);
  }

  handleClear() {
    this.props.onInput('');
    this.props.onSelect('');
  }

  render() {
    // pass through all these props to the input
    const input_props = {
      placeholder: 'Type the label name',
      className: 'form-control'
    };

    const menu_style = {
      borderRadius: '3px',
      boxShadow: '0 2px 12px rgba(0, 0, 0, 0.1)',
      background: 'rgba(255, 255, 255, 0.9)',
      padding: '2px 0',
      position: 'fixed',
      overflow: 'auto',
      maxHeight: '50%',
      zIndex: 999
    }

    const wrapper_style = {
      display: 'inline-block',
      width: '100%'
    }

    const renderTooltip = (
       <Tooltip>Clear input</Tooltip>
    );

    return (
      <InputGroup>
        <ReactAutocomplete
          items={this.props.labels}
          shouldItemRender={this.shouldItemRender.bind(this)}
          getItemValue={this.getSuggestionValue.bind(this)}
          renderItem={this.renderSuggestion.bind(this)}
          value={this.props.value}
          onChange={this.handleInput.bind(this)}
          onSelect={this.handleSelection.bind(this)}
          inputProps={input_props}
          menuStyle={menu_style}
          wrapperStyle={wrapper_style}
        />
        <OverlayTrigger placement="top" overlay={renderTooltip}>
          <Button
            variant="outline-secondary"
            size="sm"
            onClick={this.handleClear.bind(this)}
            disabled={this.props.value == ''}
            style={{position: 'absolute', right: '0px'}}
          >
            x
          </Button>
        </OverlayTrigger>
      </InputGroup>
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
      selected_type: '',
      selected_label: '',
      label_input: '',
      selected_sub_type: '',
      selected_sub_label: '',
      notes: '',
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
      .then(fetch('/labels/_get_all/project/' + this.props.project_id)
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
    const filtered_labels = this.state.all_labels.filter((row) => row.type.id == type);
    const filtered_types = this.state.all_types.filter((row) => row.parent_id == type);
    this.setState({
          selected_type: type,
          primary_labels: filtered_labels,
          selected_label: '',
          label_input: '',
          sub_types: filtered_types,
    });
    if (filtered_types.length) {
      this.handleSubTypeChange({target: {value: filtered_types[0].id}});
    }
  }

  handleSubTypeChange(e) {
    const sub_type = e.target.value;
    const filtered_labels = this.state.all_labels.filter((row) => row.type.id == sub_type);
    this.setState({
      selected_sub_type: sub_type,
      sub_labels: filtered_labels
    });
  }

  handleLabelInput(value) {
    this.setState({label_input: value});
  }

  handleLabelSelect(id) {
    this.setState({selected_label: id});
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
          sub_label_id: (this.state.selected_sub_label || null),
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
    const { primary_types, primary_labels, sub_types, sub_labels, selected_type, selected_sub_type, selected_label, label_input, selected_sub_label, certain, notes, error_code, error_message } = this.state;
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
              {sub_labels.map((row) =>
                <option key={row.id} value={row.id}>{row.name}</option>
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
          <Card.Title>Add Label</Card.Title>
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
              <AutoCompleteLabel
                labels={primary_labels}
                value={label_input}
                onInput={this.handleLabelInput.bind(this)}
                onSelect={this.handleLabelSelect.bind(this)}
              />
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
                disabled={this.props.disabled || !(selected_label)}
                onClick={this.handleSubmit.bind(this)}
              >
                Save
              </Button>
            </Col>
          </Row>
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
      <div className="mt-1">
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
            {this.props.children}
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


export class BulkLabelContainer extends React.Component {
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
        this.labelAdded(label, index);
      }
    });
  }

  handleSubmit(e) {
    e.preventDefault();
  }

  render() {
    const Inner = this.props.inner;
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
    const select_all = (selected_clips.length == this.props.clips.length);
    return (
      <Form onSubmit={this.handleSubmit}>
        <Form.Check
          id="select-all-top"
          label="Select all"
          checked={select_all}
          onChange={this.toggleSelectAll.bind(this)}
        />
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
          >
            <Inner clip={clip} />
          </ClipContainer>
        )}
        <Form.Check
          id="select-all-bottom"
          label="Select all"
          checked={select_all}
          onChange={this.toggleSelectAll.bind(this)}
        />
        <span>{selected_clips.length} selected clips: </span>
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
              disabled={!(selected_clips.length)}
            />
          </div>
        </Collapse>
      </Form>
    );
  }

}
