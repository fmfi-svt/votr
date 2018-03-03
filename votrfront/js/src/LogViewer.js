import React, { Component } from 'react';
import $ from 'jquery';
import _ from 'lodash';
import { LocalSettings } from './LocalSettings';
import { logs } from './ajax';

export class LogViewerContent extends Component {
  componentWillMount() {
    this.setState({
      http: true,
      table: true,
    });
  }

  componentDidUpdate() {
    const div = this.refs.scroll;
    const time = logs[logs.length - 1].time;
    if (time !== this.lastTime) {
      this.lastTime = time;
      div.scrollTop = div.scrollHeight;
    }
  }

  handleChange = (e) => {
    const update = {};
    update[e.target.name] = !e.target.checked;
    this.setState(update);
  }

  render() {
    // count the type of logs
    const types = logs.reduce(
      (counts, { log }) => {
        counts[log] = counts[log] ? counts[log] + 1 : 1;
        return counts;
      },
      {}
    );

    return (
      <span>
        <ul className="list-inline options">
          {Object.keys(types).sort().map((type) => (
            <li key={type}>
              <label>
                <input
                  type="checkbox"
                  name={type}
                  checked={!this.state[type]}
                  onChange={this.handleChange}
                />
                {` ${type} (${types[type]})`}
              </label>
            </li>
          ))}
        </ul>

        <div className="scroll" ref="scroll">
          <table>
            <tbody>
              {logs.map((entry, index) => !this.state[entry.log] &&
                <tr key={index}>
                  <td className="text-right">{(entry.time - logs[0].time).toFixed(3)}</td>
                  <td><code>{entry.log}</code></td>
                  <td><code>{entry.message}</code></td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </span>
    );
  }
}

export class LogViewer extends Component {
  toggle = () => {
    LocalSettings.set(
      'logViewer',
      LocalSettings.get('logViewer') === 'true' ? 'false' : 'true'
    );
  }

  handleKeypress = (e) => {
    // Ctrl + Alt + Shift + L
    if (e.ctrlKey && e.altKey && e.shiftKey && e.which === 76) {
      this.toggle();
      e.preventDefault();
    }
  }

  componentDidMount() {
    $(window).on('keypress.logViewer', this.handleKeypress);
  }

  componentWillUnmount() {
    $(window).off('keypress.logViewer');
  }

  render() {
    if (LocalSettings.get('logViewer') !== 'true') {
      return null;
    }

    return (
      <div className="log-viewer">
        <LogViewerContent />
        <div className="right">
          <button type="button" className="close" onClick={this.toggle}>
            <span aria-hidden="true">&times;</span>
            <span className="sr-only">Close</span>
          </button>
        </div>
      </div>
    );
  }
}
