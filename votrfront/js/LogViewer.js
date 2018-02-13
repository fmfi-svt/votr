
import { LocalSettings } from './LocalSettings';
import { logs } from './ajax';


export var LogViewerContent = React.createClass({
  getInitialState() {
    return {
      benchmark: true,
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

    return <div className="log-viewer">
      <div className="options">
        {this.props.closeButton}
        {this.props.modeButton}
        <ul className="list-inline">
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
      </div>

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
    </div>;
  }
});


export var LogViewerBenchmarkContent = React.createClass({
  computeBenchmarks() {
    var sums = {};
    var beginnings = {};

    function start(what, time) {
      beginnings[what] = time;
    }
    function end(what, time) {
      if (!beginnings[what]) return;
      if (!sums[what]) sums[what] = 0;
      sums[what] += time - beginnings[what];
      delete beginnings[what];
    }

    logs.forEach((entry) => {
      if (entry.log == 'benchmark' && entry.message.substr(0, 6) == 'Begin ') {
        start(entry.message.substr(6), entry.time);
      }
      if (entry.log == 'benchmark' && entry.message.substr(0, 4) == 'End ') {
        end(entry.message.substr(4), entry.time);
      }
      if (entry.log == 'rpc' && entry.message.substr(-8) == ' started') {
        start('total RPC time', entry.time);
      }
      if (entry.log == 'rpc' && entry.message.substr(-9) == ' finished') {
        end('total RPC time', entry.time);
      }
    });

    return _(sums).pairs().sortBy(1).reverse().valueOf();
  },

  render() {
    var benchmarks = this.computeBenchmarks();

    return <div className="log-viewer">
      <div className="options">
        {this.props.closeButton}
        {this.props.modeButton}
      </div>

      <div className="scroll">
        <table>
          <tbody>
            {benchmarks.map(([message, sum], index) =>
              <tr key={message}>
                <td className="text-right">{sum.toFixed(3)}</td>
                <td>{message}</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>;
  }
});


export var LogViewer = React.createClass({
  toggle() {
    LocalSettings.set("logViewer",
      LocalSettings.get("logViewer") ? "" : "log");
  },

  toggleMode() {
    LocalSettings.set("logViewer",
      LocalSettings.get("logViewer") == "log" ? "benchmark" : "log");
  },

  handleKeypress(e) {
    if (e.ctrlKey && e.altKey && e.shiftKey && e.which == 76) {   // Ctrl+Alt+Shift+L
      this.toggle();
      e.preventDefault();
    }
  },

  componentDidMount() {
    $(window).on('keydown.logViewer', this.handleKeypress);
  },

  componentWillUnmount() {
    $(window).off('keydown.logViewer');
  },

  render() {
    var mode = LocalSettings.get("logViewer");

    if (mode != "log" && mode != "benchmark") return null;

    var modeButton = <button type="button" className="pull-left" onClick={this.toggleMode}>{mode}</button>;

    var closeButton = <button type="button" className="close" onClick={this.toggle}>
      <span aria-hidden="true">&times;</span>
      <span className="sr-only">Close</span>
    </button>;

    var C = mode == "log" ? LogViewerContent : LogViewerBenchmarkContent;
    return <C modeButton={modeButton} closeButton={closeButton} />;
  }
});
