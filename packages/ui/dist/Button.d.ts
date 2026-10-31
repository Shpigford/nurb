import { ButtonHTMLAttributes, ReactNode } from 'react';
import { IconName } from './Icon';
type Variant = "accent" | "ink" | "outline" | "ghost" | "danger";
type Size = "sm" | "md" | "lg";
interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: Variant;
    size?: Size;
    icon?: IconName;
    trailingIcon?: IconName;
    children: ReactNode;
}
declare const Button: import('react').ForwardRefExoticComponent<ButtonProps & import('react').RefAttributes<HTMLButtonElement>>;
export default Button;
export declare function IconButton({ icon, label, active, className, ...rest }: ButtonHTMLAttributes<HTMLButtonElement> & {
    icon: IconName;
    label: string;
    active?: boolean;
}): import("react").JSX.Element;
