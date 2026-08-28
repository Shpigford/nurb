export function createLatestRequestGate() {
  let latest = 0;

  return {
    begin() {
      const request = ++latest;
      return () => request === latest;
    },
  };
}
