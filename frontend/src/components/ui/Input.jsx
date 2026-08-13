import "./Input.css";

export default function Input({ label, ...inputProps }) {
  return (
    <label className="ui-input">
      <span className="ui-input__label">{label}</span>
      <input className="ui-input__field" {...inputProps} />
    </label>
  );
}
