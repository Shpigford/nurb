/** A shipped profile, as the catalogue lists it. */
export interface PrinterCatalogueEntry {
    name: string;
    label: string;
    brand: string;
    bed: number[];
}
export interface AddPrinterDialogProps {
    catalogue: PrinterCatalogueEntry[];
    /** Names already on the bench: they show, dimmed, so the list stays the same shape. */
    owned: string[];
    busy?: boolean;
    error?: string | null;
    onAdd: (name: string) => void;
    onClose: () => void;
}
export declare const bedLine: (bed: number[] | null | undefined) => string;
export default function AddPrinterDialog({ catalogue, owned, busy, error, onAdd, onClose, }: AddPrinterDialogProps): import("react").JSX.Element;
