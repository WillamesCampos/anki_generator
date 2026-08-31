import "./Button.css";

export default function Button({
  as: Component = "button",
  children,
  onClick,
  variant = "primary",
  type = "button",
  ...buttonProps
}) {
  const componentProps = Component === "button" ? { type } : {};

  return (
    <Component
      className={`ui-button ui-button--${variant}`}
      onClick={onClick}
      {...componentProps}
      {...buttonProps}
    >
      {children}
    </Component>
  );
}
