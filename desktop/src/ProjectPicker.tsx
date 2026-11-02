import { useEffect, useRef, useState } from "react";
import { Button } from "@nurb/ui";
import type { MoveTarget } from "./parts";

// Where a part goes. The folders the library already has, and the way to make
// one when none of them fit, in the same place so the choice never dead-ends.
export default function ProjectPicker({
  partName,
  targets,
  busy,
  error,
  onPick,
  onCreate,
  onCancel,
}: {
  partName: string;
  targets: MoveTarget[];
  busy: boolean;
  error: string | null;
  onPick: (projectId: string) => void;
  onCreate: (name: string) => void;
  onCancel: () => void;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  const [name, setName] = useState("");

  useEffect(() => {
    ref.current?.showModal();
  }, []);

  return (
    <dialog
      ref={ref}
      aria-labelledby="picker-title"
      onCancel={(e) => {
        e.preventDefault();
        onCancel();
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onCancel();
      }}
      className="panel m-auto w-[340px] max-w-[calc(100vw-32px)] p-0 text-ink backdrop:bg-ink/30"
    >
      <div className="flex flex-col gap-1.5 px-4 pt-4 pb-3">
        <h2
          id="picker-title"
          className="font-display text-[16px] leading-5 font-bold tracking-[-0.02em] text-ink"
        >
          Add {partName} to a project
        </h2>
        <p className="text-xs leading-4 text-muted">
          A project keeps related parts together. The part stays where it is until you pick one.
        </p>
      </div>
      {targets.length > 0 ? (
        <ul className="max-h-[220px] overflow-y-auto border-t border-line-soft p-1.5">
          {targets.map((target) => (
            <li key={target.id}>
              <button
                type="button"
                disabled={busy}
                onClick={() => onPick(target.id)}
                className="flex h-[30px] w-full cursor-default items-center gap-2 rounded-[3px] px-2.5 hover:bg-raised focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-accent"
              >
                <span className="mono-value min-w-0 flex-1 truncate text-left uppercase text-ink">
                  {target.name}
                </span>
                <span className="mono-caption shrink-0 text-muted">
                  {target.parts} {target.parts === 1 ? "part" : "parts"}
                </span>
              </button>
            </li>
          ))}
        </ul>
      ) : null}
      <form
        className="flex flex-col gap-2 border-t border-line-soft px-4 py-3"
        onSubmit={(e) => {
          e.preventDefault();
          if (name.trim()) onCreate(name.trim());
        }}
      >
        <label className="mono-label text-muted" htmlFor="picker-new">
          New project with this part
        </label>
        <div className="flex gap-1.5">
          <input
            id="picker-new"
            autoFocus
            value={name}
            placeholder="Project name"
            maxLength={100}
            onChange={(e) => setName(e.target.value)}
            className="mono-value h-8 min-w-0 flex-1 rounded-[3px] border border-line bg-ground px-2 uppercase text-ink focus:border-panel-edge focus:outline-none"
          />
          <Button type="submit" variant="accent" disabled={busy || !name.trim()}>
            Create
          </Button>
        </div>
      </form>
      {error ? (
        <p className="mono-caption px-4 pb-3 text-fail" role="alert">
          {error}
        </p>
      ) : null}
      <div className="flex justify-end border-t border-line-soft px-4 py-3">
        <Button variant="outline" onClick={onCancel}>
          Cancel
        </Button>
      </div>
    </dialog>
  );
}
