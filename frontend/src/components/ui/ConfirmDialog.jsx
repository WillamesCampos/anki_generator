import Button from "./Button";
import Card from "./Card";
import "./ConfirmDialog.css";

const RETENTION_WARNING = "Após a confirmação, o item ficará retido por 7 dias antes da remoção permanente.";

export default function ConfirmDialog({ open, title, message, onConfirm, onCancel, loading = false }) {
  if (!open) return null;

  return (
    <div className="confirm-dialog__backdrop" role="presentation">
      <div className="confirm-dialog" role="dialog" aria-modal="true" aria-label={title}>
        <Card title={title}>
          {message && <p className="confirm-dialog__message">{message}</p>}
          <p className="confirm-dialog__warning">{RETENTION_WARNING}</p>
          <div className="confirm-dialog__actions">
            <Button variant="secondary" onClick={onCancel} disabled={loading}>
              Cancelar
            </Button>
            <Button onClick={onConfirm} disabled={loading}>
              {loading ? "Excluindo…" : "Confirmar exclusão"}
            </Button>
          </div>
        </Card>
      </div>
    </div>
  );
}
