import React, { useEffect, useRef, useState } from "react";
import _ from "lodash";
import { LocalSettings } from "./LocalSettings";
import { logs } from "./ajax";

export function LogViewerContent(props) {
  var [hidden, setHidden] = useState({
    benchmark: true,
    http: true,
    table: true,
  });

  var scrollRef = useRef(null);
  var lastTimeRef = useRef(null);

  function handleChange(e) {
    var name = e.target.name;
    var value = !e.target.checked;
    setHidden((hidden) => ({ ...hidden, [name]: value }));
  }

  useEffect(() => {
    var div = scrollRef.current;
    if (!logs.length) return;
    var time = _.last(logs).time;
    if (time != lastTimeRef.current) {
      lastTimeRef.current = time;
      div.scrollTop = div.scrollHeight;
    }
  });

  var types = _.countBy(logs, "log");

  return (
    <div className="log-viewer">
      <div className="options">
        {props.closeButton}
        {props.modeButton}
        <ul className="list-inline">
          {_.sortBy(_.keys(types)).map((type) => (
            <li key={type}>
              <label>
                <input
                  type="checkbox"
                  name={type}
                  checked={!hidden[type]}
                  onChange={handleChange}
                />
                {" " + type + " (" + types[type] + ")"}
              </label>
            </li>
          ))}
        </ul>
      </div>

      <div className="scroll" ref={scrollRef}>
        <table>
          <tbody>
            {logs.map(
              (entry, index) =>
                !hidden[entry.log] && (
                  <tr key={index}>
                    <td className="text-right">
                      {(entry.time - logs[0].time).toFixed(3)}
                    </td>
                    <td>
                      <code>{entry.log}</code>
                    </td>
                    <td>
                      <code>{entry.message}</code>
                    </td>
                  </tr>
                )
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function computeBenchmarks() {
  var sums: Record<string, number> = {};
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

  for (const entry of logs) {
    if (entry.log == "benchmark" && entry.message.substr(0, 6) == "Begin ") {
      start(entry.message.substr(6), entry.time);
    }
    if (entry.log == "benchmark" && entry.message.substr(0, 4) == "End ") {
      end(entry.message.substr(4), entry.time);
    }
    if (entry.log == "rpc" && entry.message.substr(-8) == " started") {
      start("total RPC time", entry.time);
    }
    if (entry.log == "rpc" && entry.message.substr(-9) == " finished") {
      end("total RPC time", entry.time);
    }
  }

  return _.sortBy(_.toPairs(sums), 1).reverse();
}

export function LogViewerBenchmarkContent(props) {
  var benchmarks = computeBenchmarks();

  return (
    <div className="log-viewer">
      <div className="options">
        {props.closeButton}
        {props.modeButton}
      </div>

      <div className="scroll">
        <table>
          <tbody>
            {benchmarks.map(([message, sum], index) => (
              <tr key={message}>
                <td className="text-right">{sum.toFixed(3)}</td>
                <td>{message}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

var explainedLogViewer = false;

export function LogViewer() {
  function toggle() {
    LocalSettings.set("logViewer", LocalSettings.get("logViewer") ? "" : "log");
  }

  function toggleMode() {
    LocalSettings.set(
      "logViewer",
      LocalSettings.get("logViewer") == "log" ? "benchmark" : "log"
    );
  }

  useEffect(() => {
    function handleKeypress(e) {
      if (e.altKey && (e.key == "L" || e.key == "l" || e.code == "KeyL")) {
        // Alt+L
        toggle();
        e.preventDefault();
      }
    }
    window.addEventListener("keydown", handleKeypress);
    return () => window.removeEventListener("keydown", handleKeypress);
  }, []);

  useEffect(() => {
    if (!explainedLogViewer) {
      explainedLogViewer = true;
      console.log(
        "%c%s%c%s",
        "font-size: 1.4em; font-weight: bold; color: #B3231B;",
        "Stlač Alt+L a uvidíš interné podrobnosti o tom, čo Votr robí.",
        "font-size: 1.4em;",
        " (Najprv klikni do stránky, nech má focus.)"
      );
    }
  }, []);

  var mode = LocalSettings.get("logViewer");

  if (mode != "log" && mode != "benchmark") return null;

  var modeButton = (
    <button type="button" className="pull-left" onClick={toggleMode}>
      {mode}
    </button>
  );

  var closeButton = (
    <button type="button" className="close" onClick={toggle}>
      <span aria-hidden="true">&times;</span>
      <span className="sr-only">Close</span>
    </button>
  );

  var C = mode == "log" ? LogViewerContent : LogViewerBenchmarkContent;
  return <C modeButton={modeButton} closeButton={closeButton} />;
}
