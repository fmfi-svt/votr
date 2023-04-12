module.exports = (array, func) => {
  if (array.toSorted) return array.toSorted(func);
  const copy = [...array];
  copy.sort(func);
  return copy;
};
