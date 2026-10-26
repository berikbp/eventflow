import { Link } from "react-router-dom";
import { Icon } from "./Icon";

export function Brand() {
  return (
    <Link to="/" className="brand" aria-label="EventFlow — на главную">
      <span className="brand-symbol">
        <Icon name="ticket" />
      </span>
      eventflow
    </Link>
  );
}
