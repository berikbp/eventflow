export function ErrorMessage({ error }: { error: Error | null }) {
  return error ? (
    <p role="alert" className="error">
      {error.message}
    </p>
  ) : null;
}

export function Loading() {
  return (
    <div className="loading" role="status">
      <span className="visually-hidden">Загружаем данные…</span>
      <span className="loading-line" />
      <span className="loading-line" />
      <span className="loading-line" />
    </div>
  );
}
