
import { LocalSettings } from './LocalSettings';
import { logs } from './ajax';


export var LogViewerContent = React.createClass({
  getInitialState() {
    return {
      http: true,
      table: true
    }
  },

  handleChange(e) {
    var update = {};
    update[e.target.name] = !e.target.checked;
    this.setState(update);
  },

  componentDidUpdate() {
    var div = this.refs.scroll;
    var time = _.last(logs).time;
    if (time != this.lastTime) {
      this.lastTime = time;
      div.scrollTop = div.scrollHeight;
    }
  },

  render() {
    var types = _.countBy(logs, 'log');

    return <span>
      <ul className="list-inline options">
        {_.sortBy(_.keys(types)).map((type) =>
          <li key={type}>
            <label>
              <input type="checkbox" name={type} checked={!this.state[type]}
                     onChange={this.handleChange} />
              {" " + type + " (" + types[type] + ")"}
            </label>
          </li>
        )}
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
    </span>;
  }
});


export var LogViewer = React.createClass({
  toggle() {
    LocalSettings.set("logViewer",
      LocalSettings.get("logViewer") == "true" ? "false" : "true");
  },

  handleKeypress(e) {
    if (e.ctrlKey && e.altKey && e.shiftKey && e.which == 76) {   // Ctrl+Alt+Shift+L
      this.toggle();
      e.preventDefault();
    }
  },

  componentDidMount() {
    $(window).on('keypress.logViewer', this.handleKeypress);
  },

  componentWillUnmount() {
    $(window).off('keypress.logViewer');
  },

  render() {
    if (LocalSettings.get("logViewer") != "true") return null;

    return <div className="log-viewer">
      <LogViewerContent />

      <div className="right">
        <button type="button" className="close" onClick={this.toggle}>
          <span aria-hidden="true">&times;</span>
          <span className="sr-only">Close</span>
        </button>
      </div>
    </div>;
  }
});
