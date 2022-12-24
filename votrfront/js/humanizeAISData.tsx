function humanizeWith(table) {
  return function (value) {
    return table[value] || value;
  };
}

export var humanizeTypVyucby = humanizeWith({
  "A": "povinné (A)",
  "B": "povinne voliteľné (B)",
  "C": "výberové (C)",
});

export var humanizeTerminHodnotenia = humanizeWith({
  "R - Riadny termín": "riadny",
  "1 - Prvý opravný termín": "prvý opravný",
  "2 - Druhý opravný termín": "druhý opravný",
});

export var humanizeNazovPriemeru = humanizeWith({
  "Sem ?": "Semester",
  "AkadR ?": "Akademický rok",
});

export var humanizeBoolean = humanizeWith({
  "A": "áno",
  "N": "nie",
});

export function classForSemester(semester) {
  if (semester == "Z") return "zima";
  if (semester == "L") return "leto";
  return undefined;
}

export function plural(count, one, few, many) {
  if (count == 1) return one;
  if (count >= 2 && count <= 4) return few;
  return many;
}
