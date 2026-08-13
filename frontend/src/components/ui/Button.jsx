import "./Button.css";

export default function Button({ children, onClick, variant = "primary", type = "button" }) {
  return (
    <button type={type} className={`ui-button ui-button--${variant}`} onClick={onClick}>
      {children}
    </button>
  );
}
