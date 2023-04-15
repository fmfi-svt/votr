import { countBy, last, sortBy } from "lodash-es";
import React, { useEffect, useRef, useState } from "react";
import { ajaxLogs } from "./ajax";
import { getLocalSetting, setLocalSetting } from "./LocalSettings";

function LogViewerContent(props: {
  closeButton: React.ReactNode;
  modeButton: React.ReactNode;
}) {
  const [hidden, setHidden] = useState<Record<string, boolean>>({
    benchmark: true,
    http: true,
    table: true,
  });

  const scrollRef = useRef<HTMLDivElement | null>(null);
  const lastTimeRef = useRef<number | null>(null);

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const name = e.target.name;
    const value = !e.target.checked;
    setHidden((hidden) => ({ ...hidden, [name]: value }));
  }

  useEffect(() => {
    const div = scrollRef.current!;
    const lastEntry = last(ajaxLogs);
    if (!lastEntry) return;
    if (lastTimeRef.current != lastEntry.time) {
      lastTimeRef.current = lastEntry.time;
      div.scrollTop = div.scrollHeight;
    }
  });

  const types = countBy(ajaxLogs, "log");

  return (
    <div className="log-viewer">
      <div className="options">
        {props.closeButton}
        {props.modeButton}
        <ul className="list-inline">
          {sortBy(Object.entries(types), 0).map(([type, count]) => (
            <li key={type}>
              <label>
                <input
                  type="checkbox"
                  name={type}
                  checked={!hidden[type]}
                  onChange={handleChange}
                />
                {` ${type} (${count})`}
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
  const sums = new Map<string, number>();
  const beginnings = new Map<string, number>();

  function start(what: string, time: number) {
    beginnings.set(what, time);
  }
  function end(what: string, time: number) {
    const beginning = beginnings.get(what);
    if (beginning === undefined) return;
    sums.set(what, (sums.get(what) || 0) + (time - beginning));
    beginnings.delete(what);
  }

  for (const entry of ajaxLogs) {
    if (entry.log == "benchmark" && entry.message.startsWith("Begin ")) {
      start(entry.message.substring(6), entry.time);
    }
    if (entry.log == "benchmark" && entry.message.startsWith("End ")) {
      end(entry.message.substring(4), entry.time);
    }
    if (entry.log == "rpc" && entry.message.endsWith(" started")) {
      start("total RPC time", entry.time);
    }
    if (entry.log == "rpc" && entry.message.endsWith(" finished")) {
      end("total RPC time", entry.time);
    }
  }

  return sortBy(Array.from(sums.entries()), 1).reverse();
}

function LogViewerBenchmarkContent(props: {
  closeButton: React.ReactNode;
  modeButton: React.ReactNode;
}) {
  const benchmarks = computeBenchmarks();

  return (
    <div className="log-viewer">
      <div className="options">
        {props.closeButton}
        {props.modeButton}
      </div>

      <div className="scroll">
        <table>
          <tbody>
            {benchmarks.map(([message, sum]) => (
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

let explainedLogViewer = false;

export function LogViewer() {
  function toggle() {
    setLocalSetting("logViewer", getLocalSetting("logViewer") ? "" : "log");
  }

  function toggleMode() {
    setLocalSetting(
      "logViewer",
      getLocalSetting("logViewer") == "log" ? "benchmark" : "log"
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

  const mode = getLocalSetting("logViewer");

  if (mode != "log" && mode != "benchmark") return null;

  const modeButton = (
    <button type="button" className="pull-left" onClick={toggleMode}>
      {mode}
    </button>
  );

  const closeButton = (
    <button type="button" className="close" onClick={toggle}>
      <span aria-hidden="true">&times;</span>
      <span className="sr-only">Close</span>
    </button>
  );

  const C = mode == "log" ? LogViewerContent : LogViewerBenchmarkContent;
  return <C modeButton={modeButton} closeButton={closeButton} />;
}
