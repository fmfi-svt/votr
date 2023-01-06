import _ from "lodash";
import React, { useEffect, useRef, useState } from "react";
import { ajaxLogs } from "./ajax";
import { LocalSettings } from "./LocalSettings";

function LogViewerContent(props: {
  closeButton: React.ReactNode;
  modeButton: React.ReactNode;
}) {
  var [hidden, setHidden] = useState<Record<string, boolean>>({
    benchmark: true,
    http: true,
    table: true,
  });

  var scrollRef = useRef<HTMLDivElement | null>(null);
  var lastTimeRef = useRef<number | null>(null);

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    var name = e.target.name;
    var value = !e.target.checked;
    setHidden((hidden) => ({ ...hidden, [name]: value }));
  }

  useEffect(() => {
    var div = scrollRef.current;
    if (!ajaxLogs.length) return;
    var time = _.last(ajaxLogs)!.time;
    if (time != lastTimeRef.current) {
      lastTimeRef.current = time;
      div!.scrollTop = div!.scrollHeight;
    }
  });

  var types = _.countBy(ajaxLogs, "log");

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
            {ajaxLogs.map(
              (entry, index) =>
                !hidden[entry.log] && (
                  <tr key={index}>
                    <td className="text-right">
                      {(entry.time - ajaxLogs[0]!.time).toFixed(3)}
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
  var beginnings: Record<string, number> = {};

  function start(what: string, time: number) {
    beginnings[what] = time;
  }
  function end(what: string, time: number) {
    const beginning = beginnings[what];
    if (!beginning) return;
    if (!sums[what]) sums[what] = 0;
    sums[what] += time - beginning;
    delete beginnings[what];
  }

  for (const entry of ajaxLogs) {
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

function LogViewerBenchmarkContent(props: {
  closeButton: React.ReactNode;
  modeButton: React.ReactNode;
}) {
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
    function handleKeypress(e: KeyboardEvent) {
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
