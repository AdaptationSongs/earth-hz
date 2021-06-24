import React from 'react';
import queryString from 'query-string';
import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import Button from 'react-bootstrap/Button';
import Collapse from 'react-bootstrap/Collapse';
import 'react-date-range/dist/styles.css';
import 'react-date-range/dist/theme/default.css';
import { DateRange } from 'react-date-range';
import TimeRange from 'react-time-range';
import moment from 'moment';

class ModelSelect extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      models: [],
      iterations: []
    };
  }

  handleModelChange(e) {
    this.props.onModelChange(e.target.value);
  }

  handleIterationChange(e) {
    this.props.onIterationChange(e.target.value);
  }

  componentDidMount() {
    fetch("/ml/_get_models/" + this.props.project_id)
      .then((response) => {
        return response.json();
      })
      .then((data) => {
        this.setState({models: data});
        this.props.onModelChange(this.props.model || data[0].id);
      }).catch((error) => {
        console.log(error);
      });
  }

  componentDidUpdate(prevProps, prevState) {
    // triggered on first load or when model changed
    if(this.props.model && (prevProps.model !== this.props.model || !this.state.iterations.length)) {
      fetch("/ml/_get_model_iterations/" + this.props.model)
        .then((response) => {
          return response.json();
        })
        .then((data) => {
          this.setState({iterations: data});
          this.props.onIterationChange(this.props.iteration || data[0].id);
        }).catch((error) => {
          console.log(error);
        });
    }
  }

  render() {
    return (
      <span>
        Model: 
        <select name="model" value={this.props.model || ""} onChange={this.handleModelChange.bind(this)}>
          {this.state.models.map((model) => <option key={model.id} value={model.id}>{model.name}</option>)}
        </select>
        <select name="iteration" value={this.props.iteration || ""} onChange={this.handleIterationChange.bind(this)}>
          {this.state.iterations.map((iteration) => <option key={iteration.id} value={iteration.id}>{iteration.updated}</option>)}
        </select>
      </span>
    );
  }

}


class LabelSelect extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      labels: []
    };
  }

  handleChange(e) {
    this.props.onChange(e.target.value);
  }

  componentDidUpdate(prevProps, prevState) {
    // triggered on first load or when iteration changed
    if(this.props.iteration && (prevProps.iteration !== this.props.iteration || !this.state.labels.length)) {
      fetch("/ml/_get_model_labels/" + this.props.iteration)
        .then((response) => {
          return response.json();
        })
        .then((data) => {
          this.setState({labels: data});
        }).catch((error) => {
          console.log(error);
        });
    }
  }

  render() {
    return (
      <label>
        Predicted label: 
        <select name="label" value={this.props.selected || ""} onChange={this.handleChange.bind(this)}>
          <option key="default" value="">Any</option>
          {this.state.labels.map((label) => <option key={label.id} value={label.id}>{label.name}</option>)}
        </select>
      </label>
    );
  }

}


class StationSelect extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      stations: [],
    };
  }

  handleChange(e) {
    this.props.onChange(e.target.value);
  }

  componentDidMount() {
    fetch("/projects/_get_monitoring_stations/" + this.props.project_id)
      .then((response) => {
        return response.json();
      })
      .then((data) => {
        this.setState({stations: data});
      }).catch((error) => {
        console.log(error);
      });
  }

  render() {
    return (
      <label>
        Location:  
        <select name="station" value={this.props.selected || ""} onChange={this.handleChange.bind(this)}>   
          <option key="default" value="">Any</option>
          {this.state.stations.map((station) => <option key={station.id} value={station.id}>{station.name}</option>)}
        </select>
      </label>
    );
  }

}


class ProbabilityRange extends React.Component {
  constructor(props) {
    super(props);
  }

  handleMinChange(e) {
    this.props.onMinChange(e.target.value);
  }

  handleMaxChange(e) {
    this.props.onMaxChange(e.target.value);
  }

  validateMin(e) {
    const { min, max } = this.props;
    if (min > max) {
      this.props.onMaxChange(1.0);
    }
    if(!e.target.validity.valid) {
      this.props.onMinChange(0.99);
    }
  }

  validateMax(e) {
    const { min, max } = this.props;
    if (max < min) {
      this.props.onMinChange(0.0);
    }
    if(!e.target.validity.valid) {
      this.props.onMaxChange(1.0);
    }
  }

  render() {
    const { min, max } = this.props;
    return (
      <span>
        Probability: 
        <input
          name="min_prob"
          type="number"
          size={6}
          min={0}
          max={1}
          step="any"
          value={min}
          onChange={this.handleMinChange.bind(this)}
          onBlur={this.validateMin.bind(this)}
        />
        to: 
        <input
          name="max_prob"
          type="number"
          size={6}
          min={0}
          max={1}
          step="any"
          value={max}
          onChange={this.handleMaxChange.bind(this)}
          onBlur={this.validateMax.bind(this)}
        />
      </span>
    );
  }

}


class DateRangeSelect extends React.Component {
  constructor(props) {
    super(props);
    this.handleChange = this.handleChange.bind(this);
  }

  isDate(d) {
    // Test for date object
    if (d && Object.prototype.toString.call(d) === '[object Date]' && !isNaN(d)) {
      return true;
    } else {
      return false;
    }
  }

  formatDate(d) {
    if (this.isDate(d)) {
      // Remove time part, keep only date string
      return d.toISOString().split('T')[0];
    }
    else {
      // Not a date object, pass it through unchanged
      return d;
    }
  }

  // work around bug where calendar days are off by by 1 from previous query
  toLocalDate(d) {
    if (!d) {
      return null;
    } else if (this.isDate(d)) {
      // Already a date object, doesn't need to be altered
      return d;
    } else {
      var new_d = new Date(d);
      // If d is a valid date string, new_d is midnight UTC on that day
      if (this.isDate(new_d)) {
        const offset = new_d.getTimezoneOffset();
        // Add timezone offset to make it midnight local time
        new_d.setTime(new_d.getTime() + (offset*60*1000));
        return new_d;
      } else {
        // Invalid date format
        return null; 
      } 
    }
  }

  handleChange(e) {
    this.props.onChange(e.selection);
  }


  render() {
    const { start_date, end_date } = this.props;
    const selection_range = {
      startDate: this.toLocalDate(start_date),
      endDate: this.toLocalDate(end_date),
      key: 'selection',
    };

    return (
      <span>Days: 
        <DateRange
          startDatePlaceholder="Start"
          endDatePlaceholder="End"
          editableDateInputs={true}
          ranges={[selection_range]}
          onChange={this.handleChange.bind(this)}
        />
        <input
          type="hidden"
          name="start_date"
          value={this.formatDate(start_date) || ""}
        />
        <input
          type="hidden"
          name="end_date"
          value={this.formatDate(end_date) || ""}
        />
      </span>
    );
  }

}


class TimeRangeSelect extends React.Component {
  constructor(props) {
    super(props);
    this.handleChange = this.handleChange.bind(this);
  }

  handleChange(e){
    this.props.onChange(e);
  }

  render(){
    const { start_hour, end_hour } = this.props;
    return (
      <span>Hours: 
        <TimeRange
          className="d-inline-block"
          minuteIncrement={60}
	  startMoment={start_hour}
	  endMoment={end_hour}
	  onChange={this.handleChange}
        />
        <input 
          type="hidden"
          name="start_hour" 
          value={moment(start_hour).hour()}
        />
        <input
          type="hidden"
          name="end_hour"
          value={moment(end_hour).hour()}
        />
      </span>
    );
  }

}


class VerificationSelect extends React.Component {
  constructor(props) {
    super(props);
  }

  handleChange(e) {
    this.props.onChange(e.target.value);
  }

  render() {
   return (
      <label>
        Verification status:
        <select name="verification" onChange={this.handleChange.bind(this)} value={this.props.selected}>
          <option key='default' value=''>Any</option>
          <option key='unverified' value='unverified'>Unverified</option>
          <option key='confirmed' value='confirmed'>Confirmed</option>
        </select>
      </label>
    );
  }
}


class ShowSingle extends React.Component {
  constructor(props) {
    super(props);
  }

  handleChange(e) {
    this.props.onChange(e.target.checked);
  }

  render() {
   return (
     <label>
       Single result per file:
       <input
         name="single"
         type="checkbox"
         checked={this.props.checked || false}
         onChange={this.handleChange.bind(this)}
       />
     </label>
    );
  }
}


class SortOptions extends React.Component {
  constructor(props) {
    super(props);
  }

  handleChange(e) {
    this.props.onChange(e.target.value);
  }

  render() {
   return (
     <label>
       Sort by:
       <select name="sort" onChange={this.handleChange.bind(this)} value={this.props.selected || ""}>
         <option key='prob' value='prob'>Probability</option>
         <option key='earliest' value='earliest'>Earliest</option>
         <option key='latest' value='latest'>Latest</option>
       </select>
     </label>
    );
  }
}


export class FilterForm extends React.Component {
  constructor(props) {
    super(props);
    const query = queryString.parse(window.location.search);
    this.state = {
      open: false,
      model: query.model,
      iteration: query.iteration,
      label: query.label,
      min_prob: query.min_prob || 0.99,
      max_prob: query.max_prob || 1.0,
      station: query.station,
      verification: query.verification,
      single: query.single,
      start_hour: moment({hour: query.start_hour || 0}),
      end_hour: moment({hour: query.end_hour || 23}),
      start_date: query.start_date,
      end_date: query.end_date,
      sort: query.sort
    };
  }

  modelChanged(value) {
    this.setState({model: value});
  }

  iterationChanged(value) {
    this.setState({iteration: value});
  }

  labelChanged(value) {
    this.setState({label: value});
  }

  minProbChanged(value) {
    this.setState({min_prob: value});
  }

  maxProbChanged(value) {
    this.setState({max_prob: value});
  }

  stationChanged(value) {
    this.setState({station: value});
  }

  verificationChanged(value) {
    this.setState({verification: value});
  }

  singleChanged(value) {
    this.setState({single: value});
  }

  dateChanged(selection) {
    this.setState({start_date: selection.startDate, end_date: selection.endDate});
  }

  timeChanged(e) {
    this.setState({start_hour: e.startTime, end_hour: e.endTime});
  }

  sortChanged(value) {
    this.setState({sort: value});
  }

  canSubmit() {
    const { start_hour, end_hour, min_prob, max_prob } = this.state;
    if (moment(start_hour).isAfter(end_hour)) {
      return false;
    }
    if (min_prob > max_prob) {
      return false;
    }
    // passed checks
    return true;
  }

  handleSubmit(e) {
    if (!this.canSubmit()) {
      e.preventDefault();
      return false;
    }
    // Allow form submit to go through
    return true;
  }

  render() {
    const { open, model, iteration, show_single, label, min_prob, max_prob, station, verification, single, start_hour, end_hour, start_date, end_date, sort } = this.state;
    const enabled = this.canSubmit();
    return (
      <Container>
        <Button
          variant={open ? 'secondary' : 'primary'}
          onClick={() => this.setState({open: !open})}
          aria-controls="search-options"
          aria-expanded={open}
        >
          {open ? '-' : '+'} Search Options
        </Button>
        <Collapse mountOnEnter={true} in={open}>
          <form id="search-options" method="get" onSubmit={this.handleSubmit.bind(this)}>
            <Row>
              <Col lg="5">
                <p>
                  <ModelSelect 
                    project_id={this.props.project_id}
                    model={model}
                    iteration={iteration} 
                    onModelChange={this.modelChanged.bind(this)}
                    onIterationChange={this.iterationChanged.bind(this)} 
                  />
                </p>
                <p>
                  <LabelSelect 
                    iteration={iteration}
                    selected={label} 
                    onChange={this.labelChanged.bind(this)} 
                  />
                </p>
                <p>
                  <ProbabilityRange
                    min={min_prob}
                    max={max_prob} 
                    onMinChange={this.minProbChanged.bind(this)}
                    onMaxChange={this.maxProbChanged.bind(this)} 
                  />
                </p>
                <p>
                  <StationSelect
                    project_id={this.props.project_id}
                    selected={station}
                    onChange={this.stationChanged.bind(this)}
                  />
                </p>
                <p>
                  <VerificationSelect
                    selected={verification}
                    onChange={this.verificationChanged.bind(this)}
                  />
                </p>
                <p>
                  <ShowSingle
                    checked={single}
                    onChange={this.singleChanged.bind(this)}
                  />
                </p>
              </Col>
              <Col lg="5">
                <div>
                  <DateRangeSelect 
                    onChange={this.dateChanged.bind(this)}
                    start_date={start_date}
                    end_date={end_date}
                  />
                </div>
                <div>
                  <TimeRangeSelect
                    start_hour={start_hour}
                    end_hour={end_hour}
                    onChange={this.timeChanged.bind(this)}
                  />
                </div>
              </Col>
              <Col lg="2">
                <p>
                  <SortOptions
                    selected={sort}
                    onChange={this.sortChanged.bind(this)}
                  />
                </p>
                <input type="submit" disabled={!enabled} value="Search Now" className="btn btn-primary" />
              </Col>
          </Row>
          </form>
        </Collapse>
      </Container>
    );
  }

}

