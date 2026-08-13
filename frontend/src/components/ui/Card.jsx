import "./Card.css";

export default function Card({ title, children }) {
  return (
    <div className="ui-card">
      {title && <h3 className="ui-card__title">{title}</h3>}
      <div className="ui-card__body">{children}</div>
    </div>
  );
}
