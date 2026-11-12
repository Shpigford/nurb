import { SVGProps } from 'react';
export type IconName = "chevron-left" | "chevron-down" | "chevron-up" | "check" | "warning" | "lock" | "plus" | "minus" | "camera" | "search" | "xmark" | "image" | "download" | "expand" | "eye" | "arrow-up" | "link" | "stop" | "loader" | "chat" | "dots" | "trash" | "ruler" | "gear" | "user" | "logout" | "box" | "copy" | "folder" | "tag";
export interface IconProps extends Omit<SVGProps<SVGSVGElement>, "name"> {
    name: IconName;
}
export default function Icon({ name, className, ...rest }: IconProps): import("react").JSX.Element;
