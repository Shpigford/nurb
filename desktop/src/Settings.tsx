import { open as pickFolder } from "@tauri-apps/plugin-dialog";

type Props = {
  folder: string;
  customized: boolean;
  onChange: (folder: string) => void | Promise<void>;
  onReset: () => void | Promise<void>;
  onClose: () => void;
};

export default function Settings({ folder, customized, onChange, onReset, onClose }: Props) {
  const changeFolder = async () => {
    // Before the backend resolves the default, the folder shown is the
    // literal "~/Documents/nurb" placeholder, which is not a path.
    const picked = await pickFolder({
      directory: true,
      defaultPath: folder.startsWith("~") ? undefined : folder,
      title: "Choose where new nurb projects are created",
    });
    if (typeof picked === "string") await onChange(picked);
  };

  return (
    <div className="about" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div
        className="about-card settings"
        role="dialog"
        aria-modal="true"
        aria-labelledby="settings-title"
      >
        <button className="about-close" title="close" onClick={onClose}>
          ×
        </button>
        <div className="about-title" id="settings-title">
          Settings
        </div>
        <div className="about-body">
          <h3>Projects folder</h3>
          <p>New projects are created here. Changing it never moves existing files.</p>
          <div className="settings-folder" title={folder}>
            {folder}
          </div>
          <div className="settings-actions">
            <button className="settings-action" onClick={changeFolder}>
              Change folder
            </button>
            {customized && (
              <button className="settings-action secondary" onClick={onReset}>
                Use default
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
