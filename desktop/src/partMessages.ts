export type PartConfigurationRequest = {
  path: string;
  part: string;
  variant: string | null;
};

type PartMessage = {
  type: "nurb:part";
  name: string;
  variant?: string | null;
};

// Missing `variant` means "show this part as it is". A present null means the
// user explicitly clicked its defaults row, so the viewer may reset a variant.
export function partMessage(
  path: string,
  part: string,
  request: PartConfigurationRequest | null,
): { message: PartMessage; consumed: boolean } {
  const consumed = request?.path === path && request.part === part;
  return {
    message: consumed
      ? { type: "nurb:part", name: part, variant: request.variant }
      : { type: "nurb:part", name: part },
    consumed,
  };
}
