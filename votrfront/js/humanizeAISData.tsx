function humanizeWith(table: Record<string, string>) {
  return function (value: string) {
    return table[value] || value;
  };
}

export const humanizeTypVyucby = humanizeWith({
  "A": "povinné (A)",
  "B": "povinne voliteľné (B)",
  "C": "výberové (C)",
});

export const humanizeTerminHodnotenia = humanizeWith({
  "R - Riadny termín": "riadny",
  "1 - Prvý opravný termín": "prvý opravný",
  "2 - Druhý opravný termín": "druhý opravný",
});

export const humanizeNazovPriemeru = humanizeWith({
  "Sem ?": "Semester",
  "AkadR ?": "Akademický rok",
});

export const humanizeBoolean = humanizeWith({
  "A": "áno",
  "N": "nie",
});

export function classForSemester(semester: string) {
  if (semester == "Z") return "v-humanizeAISData-zima";
  if (semester == "L") return "v-humanizeAISData-leto";
  return undefined;
}

export function plural(count: number, one: string, few: string, many: string) {
  if (count == 1) return one;
  if (count >= 2 && count <= 4) return few;
  return many;
}
