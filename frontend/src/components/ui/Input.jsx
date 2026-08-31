import "./Input.css";

export default function Input({ as: Component = "input", label, ...inputProps }) {
  return (
    <label className="ui-input">
      <span className="ui-input__label">{label}</span>
      <Component className="ui-input__field" {...inputProps} />
    </label>
  );
}
