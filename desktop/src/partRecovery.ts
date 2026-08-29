export function createPartRecovery(recover: () => Promise<void>) {
  let failures = 0;
  let pending = false;
  let stopped = false;

  return {
    success() {
      if (!stopped) failures = 0;
    },
    failure() {
      if (stopped || pending) return;
      failures += 1;
      if (failures < 3) return;

      failures = 0;
      pending = true;
      void recover().then(settled, settled);
    },
    stop() {
      stopped = true;
    },
  };

  function settled() {
    if (!stopped) pending = false;
  }
}
